# AskSage Model Provider Plugin for Dify

A Dify plugin that integrates [AskSage](https://asksage.ai) as a model provider, giving you access to 47+ AI models (GPT, Claude, Gemini, Llama, Groq, and more) through AskSage's FedRAMP-authorized API.

## Features

- **47+ predefined models** auto-generated from AskSage's model catalog
- **Custom model support** -- add any model your AskSage tenant provides
- **Dynamic model discovery** -- fetches available models from the API at runtime with 5-minute caching
- **Token usage tracking** -- reports prompt and completion tokens back to Dify
- **Simulated streaming** -- works with Dify's streaming UI even though AskSage uses synchronous responses
- **Model generator script** -- run `generate_models.py` to refresh model YAMLs when AskSage adds new models

## Creating an AskSage Account

1. Go to [chat.asksage.ai/register](https://chat.asksage.ai/register)
2. Fill in all required fields (first name, last name, company, email, phone, country)
   - If you have a CAC/PIV card, ensure it is inserted during registration
   - AskSage is restricted to approved nationalities listed on the registration page
3. Submit the form -- you will receive a verification code via email
   - If you do not receive the code, email support@asksage.ai to force-validate your account
4. Log in at [chat.asksage.ai](https://chat.asksage.ai) with your email and password (or CAC/PIV)
5. New accounts receive a **free 30-day trial** with 200,000 inference tokens and 200,000 training tokens

### After Trial

| Plan | Price | Tokens/Month |
|------|-------|--------------|
| Bring Your Own LLMs | From $15/mo/user | Unlimited |
| Standard | $30/mo/user | 500K |
| Plus | $50/mo/user | 1M |
| Enterprise | $90/mo or $990/yr | 2M |

Contact sales@asksage.ai for enterprise pricing and volume discounts.

### Getting Your API Key

1. Sign in at [chat.asksage.ai](https://chat.asksage.ai)
2. Click the **Settings** cog (bottom left)
3. Select the **Account** tab
4. Scroll to **Manage your API Keys**
5. Generate a new key -- save it securely (you will need it for the plugin)

For MFA setup, we recommend Microsoft Authenticator or Google Authenticator. Configure it in the same Account settings page.

## Requirements

| Component | Version |
|-----------|---------|
| Dify | 1.0+ with Plugin Daemon |
| Dify Plugin Daemon | **0.5.5+** (see [known issues](#known-issues--daemon-053)) |
| Dify Plugin SDK (`dify_plugin`) | 0.5.x (must match daemon) |
| Python | 3.12 |
| AskSage Account | With API key access |

**Important:** The `dify_plugin` SDK version must match your Plugin Daemon version. If your daemon is `0.5.3`, install `dify_plugin>=0.5.0,<0.6.0`. A version mismatch (e.g., SDK 0.7.x with daemon 0.5.x) will cause silent connection failures.

## Installation

### Verify Your Daemon Version First

Dify 1.13.3 ships with `dify-plugin-daemon:0.5.3-local` by default, which has a bug that breaks `.difypkg` installation. You **must** upgrade the daemon to 0.5.5+ before installing any local plugin package.

In your `docker-compose.yaml` (e.g. `C:\dify\docker\docker-compose.yaml`), find the `plugin_daemon` service and update the image:

```yaml
  plugin_daemon:
    # IMPORTANT: Daemon 0.5.3 has a struct-tag bug that rejects
    # plugin_unique_identifier on the /decode/from_identifier endpoint.
    # This was fixed in 0.5.5 via dify-plugin-daemon PR #593.
    # See: https://github.com/langgenius/dify-plugin-daemon/pull/593
    image: langgenius/dify-plugin-daemon:0.5.5-local
```

Then restart the daemon:

```powershell
cd C:\dify\docker
docker compose up -d plugin_daemon
```

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

## Plugin Update Procedures

When the plugin code is updated (new features, model changes, bug fixes), the update process depends on how you installed the plugin.

### Packaged Install (.difypkg)

If you installed via a `.difypkg` upload, you must repackage and reinstall:

1. **Pull the latest code:**

   ```powershell
   cd C:\projects\asksage_plugin_dify\asksage
   git pull origin main
   ```

2. **Bump the version in `manifest.yaml`** — the daemon rejects reinstalls at the same version:

   ```powershell
   # Example: 0.1.0 → 0.2.0
   (Get-Content manifest.yaml -Raw) -replace 'version: 0.1.0', 'version: 0.2.0' |
     Set-Content manifest.yaml -NoNewline -Encoding ([System.Text.UTF8Encoding]::new($false))
   ```

3. **Repackage:**

   ```powershell
   & "$HOME\bin\dify.exe" plugin package .
   ```

4. **Uninstall the old version** in the Dify console: **Plugins** → find AskSage → delete/uninstall.

5. **Upload the new `.difypkg`**: **Plugins** → **Install Plugin** → upload the new file.

6. **Re-enter credentials** — API key and base URL do not carry over between installs. Go to the AskSage provider settings and re-enter them.

### Debug Mode

If you are running in debug mode (local Python process), updates are simpler:

1. **Pull the latest code:**

   ```powershell
   cd C:\projects\asksage_plugin_dify\asksage
   git pull origin main
   ```

2. **Restart the plugin** — stop the running process (Ctrl+C) and relaunch:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   python -m main
   ```

   Dify picks up updated model YAMLs and code on reconnect. No version bump or repackaging required.

> **Tip:** Use debug mode during active development. Switch to `.difypkg` for production or team distribution.

## Known Issues -- Daemon 0.5.3

Dify 1.13.3's default `docker-compose.yaml` pins `langgenius/dify-plugin-daemon:0.5.3-local`, which contains a bug in the `DecodePluginFromIdentifier` handler. The Go struct uses a `json:` tag instead of a `form:` tag, so Gin cannot bind the `plugin_unique_identifier` query parameter. The result is a **400 error** on `/decode/from_identifier` immediately after a successful `.difypkg` upload:

```
400: Key: 'PluginUniqueIdentifier' Error: Field validation for 'PluginUniqueIdentifier' failed on the 'required' tag
```

**Fix:** Upgrade to daemon **0.5.5+** (see [installation instructions](#verify-your-daemon-version-first) above).

References:
- [dify-plugin-daemon PR #593](https://github.com/langgenius/dify-plugin-daemon/pull/593) -- daemon-side fix (included in 0.5.5)
- [dify PR #34720](https://github.com/langgenius/dify/pull/34720) -- API-side backward-compatible fix (merged to main, not yet released)
- [dify issue #34274](https://github.com/langgenius/dify/issues/34274) -- original bug report

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
