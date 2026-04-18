# AskSage Model Provider Plugin for Dify

A Dify plugin that integrates [AskSage](https://asksage.ai) as a model provider, giving you access to 47+ AI models (GPT, Claude, Gemini, Llama, Groq, and more) through AskSage's FedRAMP-authorized API.

## Features

- **47+ predefined models** auto-generated from AskSage's model catalog
- **Custom model support** -- add any model your AskSage tenant provides
- **Dynamic model discovery** -- fetches available models from the API at runtime with 5-minute caching
- **Token usage tracking** -- reports prompt and completion tokens back to Dify
- **Simulated streaming** -- works with Dify's streaming UI even though AskSage uses synchronous responses
- **Model generator script** -- run `generate_models.py` to refresh model YAMLs when AskSage adds new models

## Requirements

| Component | Version |
|-----------|---------|
| Dify | 1.0+ with Plugin Daemon |
| Dify Plugin Daemon | 0.5.x |
| Dify Plugin SDK (`dify_plugin`) | 0.5.x (must match daemon) |
| Python | 3.12 |
| AskSage Account | With API key access |

**Important:** The `dify_plugin` SDK version must match your Plugin Daemon version. If your daemon is `0.5.3`, install `dify_plugin>=0.5.0,<0.6.0`. A version mismatch (e.g., SDK 0.7.x with daemon 0.5.x) will cause silent connection failures.

## Installation

### Option A: Install from .difypkg (recommended)

1. Download `asksage-0.1.0.difypkg` from the [Releases](https://github.com/JLay2026/asksage-dify-plugin/releases) page
2. In Dify, go to **Plugins** (top right)
3. Click **Install Plugin**
4. Upload the `.difypkg` file
5. Configure credentials (see below)

### Option B: Remote debugging (development)

1. Clone this repo:
   ```
   git clone https://github.com/JLay2026/asksage-dify-plugin.git
   cd asksage-dify-plugin
   ```

2. Create a virtual environment:
   ```
   py -3.12 -m venv .venv
   .\.venv\Scripts\Activate.ps1    # Windows
   source .venv/bin/activate        # Linux/Mac
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Copy `.env.example` to `.env` and fill in your debug key:
   ```
   INSTALL_METHOD=remote
   REMOTE_INSTALL_HOST=localhost
   REMOTE_INSTALL_PORT=5003
   REMOTE_INSTALL_KEY=your-debug-key-from-dify
   ```
   To find your debug key: Dify UI > Plugins > click the bug icon > copy Debug Key.

5. Run the plugin:
   ```
   python -m main
   ```

## Credential Setup

After installing the plugin, configure it in Dify:

1. Go to **Settings > Model Providers**
2. Find **AskSage** and click it
3. Enter the following:

| Field | Description |
|-------|-------------|
| **API Key** | Your AskSage static API key. Find it at Settings > Account > Manage your API Keys in the [AskSage app](https://app.asksage.ai). |
| **Email** | The email address associated with your AskSage account. |
| **API Base URL** | Default: `https://api.asksage.ai`. Only change if you use a custom AskSage deployment. |

4. Click **Save** -- the plugin validates your credentials by calling AskSage's `/server/get-models` endpoint.

## Refreshing Models

When AskSage adds new models to your tenant:

```
python generate_models.py
```

This calls `/server/get-models`, generates a YAML file for each model, and updates `_position.yaml`. Image-generation models are automatically filtered out. Restart the plugin or reinstall the `.difypkg` to pick up the changes.

## Project Structure

```
asksage/
├── _assets/                    # Provider icons (SVG)
├── models/llm/
│   ├── _position.yaml          # Model display order
│   ├── *.yaml                  # One file per predefined model
│   └── llm.py                  # LLM implementation (core logic)
├── provider/
│   ├── asksage.yaml            # Provider config and credential schemas
│   └── asksage.py              # Credential validation
├── manifest.yaml               # Plugin manifest
├── main.py                     # Entry point
├── generate_models.py          # Model YAML generator script
├── requirements.txt            # Python dependencies
└── .env.example                # Environment template
```

## Known Limitations

- **No native streaming** -- AskSage's `/server/query` returns complete responses. The plugin simulates streaming by yielding the full response as a single chunk.
- **No stop sequences** -- AskSage does not support stop sequence parameters.
- **Token estimation** -- Uses a 4-chars-per-token heuristic for pre-invocation estimates since AskSage does not expose a tokenizer endpoint. Actual usage from responses is reported accurately.
- **No function/tool calling** -- AskSage's tool calling support varies by underlying model and is not yet exposed through this plugin.

## License

Apache 2.0

## Links

- [AskSage API Documentation](https://docs.asksage.ai/docs/api-documentation/api-documentation.html)
- [Dify Plugin Development Docs](https://docs.dify.ai/en/develop-plugin/dev-guides-and-walkthroughs/creating-new-model-provider)
- [Dify Plugin SDK](https://github.com/langgenius/dify-plugin-sdks)
