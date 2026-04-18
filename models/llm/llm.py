"""
AskSage LLM implementation for Dify.
Translates Dify's standardized model interface into AskSage API calls.
"""

import json
import time
import logging
from decimal import Decimal
from typing import Generator, Optional, Union

import requests

from dify_plugin.entities.model import (
    AIModelEntity,
    FetchFrom,
    ModelPropertyKey,
    ModelType,
)
from dify_plugin.entities.model.llm import (
    LLMMode,
    LLMResult,
    LLMResultChunk,
    LLMResultChunkDelta,
    LLMUsage,
)
from dify_plugin.entities.model.message import (
    AssistantPromptMessage,
    PromptMessage,
    PromptMessageRole,
    SystemPromptMessage,
    UserPromptMessage,
)
from dify_plugin.errors.model import (
    CredentialsValidateFailedError,
    InvokeAuthorizationError,
    InvokeBadRequestError,
    InvokeConnectionError,
    InvokeError,
    InvokeRateLimitError,
    InvokeServerUnavailableError,
)
from dify_plugin.interfaces.model.large_language_model import LargeLanguageModel

logger = logging.getLogger(__name__)


class AskSageLargeLanguageModel(LargeLanguageModel):
    """
    AskSage Large Language Model implementation.

    Maps Dify's LLM interface to AskSage's /server/query endpoint.
    """

    # ------------------------------------------------------------------ #
    #  Core invocation
    # ------------------------------------------------------------------ #

    def _invoke(
        self,
        model: str,
        credentials: dict,
        prompt_messages: list[PromptMessage],
        model_parameters: dict,
        tools: Optional[list] = None,
        stop: Optional[list[str]] = None,
        stream: bool = True,
        user: Optional[str] = None,
    ) -> Union[LLMResult, Generator[LLMResultChunk, None, None]]:
        """
        Invoke the AskSage model.

        AskSage's /server/query endpoint does NOT support streaming natively
        for the standard query path, so we always do a synchronous call.
        If Dify requests streaming, we simulate it by yielding the full
        response as a single chunk.
        """
        api_key = credentials.get("asksage_api_key", "")
        api_base = credentials.get("asksage_api_base", "https://api.asksage.ai").rstrip("/")

        # --- Build the AskSage request payload ---
        system_prompt, conversation = self._format_messages(prompt_messages)

        payload = {
            "message": conversation,
            "model": model,
            "temperature": model_parameters.get("temperature", 0.7),
            "limit_references": 0,        # No RAG by default; user can change via AskSage settings
            "live": model_parameters.get("live", 0),  # 0=off, 1=Google, 2=Google+crawl
            "dataset": "none",
            "usage": True,                 # Request token usage stats
        }

        if system_prompt:
            payload["system_prompt"] = system_prompt

        # AskSage doesn't use max_tokens directly, but we track it for Dify
        max_tokens = model_parameters.get("max_tokens")

        headers = {
            "x-access-tokens": api_key,
            "Content-Type": "application/json",
        }

        # --- Make the API call ---
        try:
            response = requests.post(
                f"{api_base}/server/query",
                headers=headers,
                json=payload,
                timeout=120,
            )
        except requests.exceptions.Timeout:
            raise InvokeConnectionError("AskSage API request timed out.")
        except requests.exceptions.ConnectionError:
            raise InvokeConnectionError("Could not connect to AskSage API.")

        if response.status_code == 401:
            raise InvokeAuthorizationError("Invalid AskSage API key.")
        elif response.status_code == 429:
            raise InvokeRateLimitError("AskSage API rate limit exceeded.")
        elif response.status_code >= 500:
            raise InvokeServerUnavailableError(
                f"AskSage server error: {response.status_code}"
            )
        elif response.status_code != 200:
            raise InvokeBadRequestError(
                f"AskSage API error {response.status_code}: {response.text}"
            )

        # --- Parse the response ---
        try:
            result = response.json()
        except json.JSONDecodeError:
            raise InvokeServerUnavailableError("Invalid JSON response from AskSage API.")

        assistant_message = result.get("message", "")

        # Build usage object
        usage_data = result.get("usage", {})
        usage = self._build_usage(
            model=model,
            prompt_tokens=usage_data.get("prompt_tokens", 0),
            completion_tokens=usage_data.get("completion_tokens", 0),
        )

        if stream:
            # Simulate streaming: yield the entire response as one chunk
            return self._simulate_stream(model, assistant_message, usage)
        else:
            return LLMResult(
                model=model,
                prompt_messages=prompt_messages,
                message=AssistantPromptMessage(content=assistant_message),
                usage=usage,
            )

    def _simulate_stream(
        self, model: str, content: str, usage: LLMUsage
    ) -> Generator[LLMResultChunk, None, None]:
        """
        Simulate streaming by yielding the complete response as a single chunk.
        This satisfies Dify's streaming interface when the upstream API
        doesn't support native streaming.
        """
        yield LLMResultChunk(
            model=model,
            prompt_messages=[],
            delta=LLMResultChunkDelta(
                index=0,
                message=AssistantPromptMessage(content=content),
                finish_reason="stop",
                usage=usage,
            ),
        )

    # ------------------------------------------------------------------ #
    #  Message formatting
    # ------------------------------------------------------------------ #

    def _format_messages(
        self, prompt_messages: list[PromptMessage]
    ) -> tuple[str, str | list]:
        """
        Convert Dify PromptMessage objects into AskSage format.

        AskSage accepts either:
        - A plain string for `message`
        - A conversation array: [{"user": "me|ai", "message": "..."}]

        Returns:
            (system_prompt, conversation)
        """
        system_prompt = ""
        conversation = []

        for msg in prompt_messages:
            if isinstance(msg, SystemPromptMessage):
                system_prompt = msg.content
            elif isinstance(msg, UserPromptMessage):
                # Handle multimodal content (text only for now)
                content = msg.content if isinstance(msg.content, str) else str(msg.content)
                conversation.append({"user": "me", "message": content})
            elif isinstance(msg, AssistantPromptMessage):
                content = msg.content if isinstance(msg.content, str) else str(msg.content)
                conversation.append({"user": "ai", "message": content})

        # If single message, AskSage also accepts a plain string
        if len(conversation) == 1:
            return system_prompt, conversation[0]["message"]

        return system_prompt, conversation

    # ------------------------------------------------------------------ #
    #  Usage / token helpers
    # ------------------------------------------------------------------ #

    def _build_usage(
        self, model: str, prompt_tokens: int, completion_tokens: int
    ) -> LLMUsage:
        """Build a Dify LLMUsage object from token counts."""
        return LLMUsage(
            prompt_tokens=prompt_tokens,
            prompt_unit_price=Decimal("0"),   # AskSage doesn't expose per-call pricing
            prompt_price_unit=Decimal("0"),
            prompt_price=Decimal("0"),
            completion_tokens=completion_tokens,
            completion_unit_price=Decimal("0"),
            completion_price_unit=Decimal("0"),
            completion_price=Decimal("0"),
            total_tokens=prompt_tokens + completion_tokens,
            total_price=Decimal("0"),
            currency="USD",
            latency=0,
        )

    def get_num_tokens(
        self,
        model: str,
        credentials: dict,
        prompt_messages: list[PromptMessage],
        tools: Optional[list] = None,
    ) -> int:
        """
        Estimate token count. AskSage doesn't provide a tokenizer endpoint
        for arbitrary text, so we use a rough heuristic (4 chars â‰ˆ 1 token).
        """
        total_chars = 0
        for msg in prompt_messages:
            content = msg.content if isinstance(msg.content, str) else str(msg.content)
            total_chars += len(content)
        return max(total_chars // 4, 1)

    # ------------------------------------------------------------------ #
    #  Credential validation (per-model)
    # ------------------------------------------------------------------ #

    def validate_credentials(self, model: str, credentials: dict) -> None:
        """
        Validate credentials by making a small test query to AskSage.
        """
        try:
            api_key = credentials.get("asksage_api_key", "")
            api_base = credentials.get("asksage_api_base", "https://api.asksage.ai").rstrip("/")

            response = requests.post(
                f"{api_base}/server/query",
                headers={
                    "x-access-tokens": api_key,
                    "Content-Type": "application/json",
                },
                json={
                    "message": "Say 'OK' and nothing else.",
                    "model": model,
                    "temperature": 0.0,
                    "limit_references": 0,
                    "live": 0,
                    "dataset": "none",
                },
                timeout=60,
            )

            if response.status_code != 200:
                raise CredentialsValidateFailedError(
                    f"AskSage returned status {response.status_code}: {response.text}"
                )

        except CredentialsValidateFailedError:
            raise
        except Exception as ex:
            raise CredentialsValidateFailedError(
                f"AskSage credential validation failed: {str(ex)}"
            )

    # ------------------------------------------------------------------ #
    #  Custom model support
    # ------------------------------------------------------------------ #

    def get_customizable_model_schema(
        self, model: str, credentials: dict
    ) -> AIModelEntity:
        """
        Return a model entity for user-added custom models.
        This lets users type any model name that their AskSage tenant supports.
        """
        return AIModelEntity(
            model=model,
            label={"en_US": model},
            model_type=ModelType.LLM,
            fetch_from=FetchFrom.CUSTOMIZABLE_MODEL,
            features=[],
            model_properties={
                ModelPropertyKey.MODE: LLMMode.CHAT.value,
                ModelPropertyKey.CONTEXT_SIZE: 128000,
            },
            parameter_rules=[],
        )


    # ------------------------------------------------------------------ #
    #  Dynamic model discovery
    # ------------------------------------------------------------------ #

    # Cache: avoids calling /get-models on every request
    _models_cache: list[AIModelEntity] = []
    _models_cache_timestamp: float = 0
    _CACHE_TTL: float = 300  # 5 minutes

    def get_models(self, credentials: dict) -> list[AIModelEntity]:
        """
        Fetch available models from AskSage /server/get-models at runtime.
        Results are cached for 5 minutes to avoid excessive API calls.
        Models fetched here appear in Dify's model selector automatically.
        """
        now = time.time()
        if self._models_cache and (now - self._models_cache_timestamp) < self._CACHE_TTL:
            return self._models_cache

        api_key = credentials.get("asksage_api_key", "")
        api_base = credentials.get("asksage_api_base", "https://api.asksage.ai").rstrip("/")

        try:
            response = requests.post(
                f"{api_base}/server/get-models",
                headers={
                    "x-access-tokens": api_key,
                    "Content-Type": "application/json",
                },
                json={},
                timeout=30,
            )

            if response.status_code != 200:
                logger.warning(f"Failed to fetch models from AskSage: {response.status_code}")
                return self._models_cache  # Return stale cache on failure

            data = response.json()
            models_data = data.get("response", {}).get("data", [])

            entities = []
            for m in models_data:
                model_id = m.get("id", "")
                model_name = m.get("name", model_id)
                if not model_id:
                    continue

                entities.append(
                    AIModelEntity(
                        model=model_id,
                        label={"en_US": f"{model_name} (via AskSage)"},
                        model_type=ModelType.LLM,
                        fetch_from=FetchFrom.PREDEFINED_MODEL,
                        features=[],
                        model_properties={
                            ModelPropertyKey.MODE: LLMMode.CHAT.value,
                            ModelPropertyKey.CONTEXT_SIZE: 128000,
                        },
                        parameter_rules=[],
                    )
                )

            if entities:
                self._models_cache = entities
                self._models_cache_timestamp = now
                logger.info(f"Discovered {len(entities)} models from AskSage API.")

            return self._models_cache

        except Exception as ex:
            logger.warning(f"Error fetching AskSage models: {ex}")
            return self._models_cache  # Return stale cache on error

    # ------------------------------------------------------------------ #
    #  Error mapping
    # ------------------------------------------------------------------ #

    @property
    def _invoke_error_mapping(self) -> dict[type[InvokeError], list[type[Exception]]]:
        """
        Map Python/requests exceptions to Dify's standardized error types.
        """
        return {
            InvokeConnectionError: [
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
            ],
            InvokeServerUnavailableError: [
                requests.exceptions.HTTPError,
            ],
            InvokeRateLimitError: [],
            InvokeAuthorizationError: [],
            InvokeBadRequestError: [
                requests.exceptions.InvalidURL,
                requests.exceptions.MissingSchema,
                KeyError,
                ValueError,
            ],
        }
