"""
AskSage Model Provider for Dify
Handles provider-level credential validation.
"""

import logging
import requests

from dify_plugin import ModelProvider
from dify_plugin.entities.model import ModelType
from dify_plugin.errors.model import CredentialsValidateFailedError

logger = logging.getLogger(__name__)


class AskSageProvider(ModelProvider):
    """
    AskSage provider class.
    Validates that the user's API key and email are correct
    by making a lightweight API call.
    """

    def validate_provider_credentials(self, credentials: dict) -> None:
        """
        Validate provider credentials by calling the AskSage /get-models endpoint.
        This is a lightweight call that confirms the API key works.

        :param credentials: Dict with 'asksage_api_key', 'asksage_email', 'asksage_api_base'
        :raises CredentialsValidateFailedError: If the API key is invalid
        """
        try:
            api_key = credentials.get("asksage_api_key", "")
            api_base = credentials.get("asksage_api_base", "https://api.asksage.ai")

            # Strip trailing slash
            api_base = api_base.rstrip("/")

            # Use /server/get-models as a lightweight validation call
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
                raise CredentialsValidateFailedError(
                    f"AskSage API returned status {response.status_code}: {response.text}"
                )

            data = response.json()
            if "response" not in data and "data" not in data:
                raise CredentialsValidateFailedError(
                    "Unexpected response format from AskSage API."
                )

            logger.info("AskSage provider credentials validated successfully.")

        except CredentialsValidateFailedError:
            raise
        except requests.exceptions.Timeout:
            raise CredentialsValidateFailedError(
                "Connection to AskSage API timed out. Check your API base URL."
            )
        except requests.exceptions.ConnectionError:
            raise CredentialsValidateFailedError(
                "Could not connect to AskSage API. Check your API base URL."
            )
        except Exception as ex:
            logger.exception("AskSage credentials validation failed")
            raise CredentialsValidateFailedError(
                f"Failed to validate AskSage credentials: {str(ex)}"
            )