# Changelog

All notable changes to the AskSage Dify Plugin will be documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- **Minimum daemon version raised to 0.5.5+** in README. Daemon 0.5.3 (Dify 1.13.3 default) has a `form:` struct-tag bug that breaks `.difypkg` installation with a 400 error on `/decode/from_identifier`. Fixed upstream in [dify-plugin-daemon PR #593](https://github.com/langgenius/dify-plugin-daemon/pull/593).

### Added

- **Known Issues section** in README documenting the daemon 0.5.3 regression with workaround and references.
- **Daemon version check** instructions in the Installation section with docker-compose snippet.

## [0.1.0] - 2026-04-18

### Added

- **Provider credential validation** via AskSage `/server/get-models` endpoint. Validates API key and email on save with clear error messages for timeouts, connection failures, and invalid keys.
- **47 predefined model YAMLs** auto-generated from the AskSage API, covering GPT (4.1, 5.x, o-series), Claude (4 through 4.7), Gemini 2.5, AWS Bedrock (Nova, Nemotron, Titan), Groq, Llama 3, and xAI Grok.
- **Custom model support** via `customizable-model` configuration. Users can add any model ID their AskSage tenant supports beyond the predefined list.
- **Dynamic model discovery** with `get_models()` calling `/server/get-models` at runtime. Results are cached for 5 minutes to avoid excessive API calls, with graceful fallback to stale cache on failure.
- **Simulated streaming** for Dify's streaming UI. AskSage's `/server/query` returns complete responses; the plugin yields the full response as a single `LLMResultChunk` so Dify's streaming interface works without modification.
- **Token usage reporting** via AskSage's `usage: true` parameter. Prompt and completion token counts are passed back to Dify for tracking.
- **Token count estimation** using a 4-characters-per-token heuristic for pre-invocation estimates.
- **Model generator script** (`generate_models.py`) that fetches all models from the AskSage API and generates YAML definitions. Filters out image-generation models (Imagen, Veo) and sets appropriate context sizes per model family.
- **Error mapping** from Python/requests exceptions to Dify's standardized error types (authorization, rate limit, connection, server unavailable, bad request).
- **Configurable API base URL** for custom AskSage deployments.
- **GitHub Actions workflow** for automated plugin packaging and PR creation to the Dify marketplace.

### Known Limitations

- No native streaming support from the AskSage API.
- No stop sequence support.
- No function/tool calling passthrough.
- `max_tokens` parameter is tracked but not enforced by AskSage.

[0.1.0]: https://github.com/JLay2026/asksage-dify-plugin/releases/tag/v0.1.0
