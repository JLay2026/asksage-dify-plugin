# Privacy Policy - AskSage Dify Plugin

## Data Collection

This plugin collects and transmits the following data to the AskSage API (`api.asksage.ai`):

- **User-provided credentials**: API key and email address (stored in Dify's encrypted credential store, transmitted to AskSage for authentication)
- **Prompt content**: Messages sent through Dify workflows and apps are forwarded to AskSage's `/server/query` endpoint for model inference
- **Model parameters**: Temperature, model selection, and other configuration values

## Data Storage

- This plugin does **not** store any user data locally or in any external database
- Credentials are managed entirely by Dify's built-in credential storage
- No conversation history, logs, or analytics are collected by the plugin itself

## Third-Party Data Sharing

All prompt and credential data is transmitted to **AskSage** (operated by BigBear.ai) for processing. AskSage's data handling is governed by their own privacy policy and terms of service:

- [AskSage Terms & Conditions](https://www.asksage.ai/terms-conditions/)
- [AskSage Privacy Policy](https://www.asksage.ai/privacy-policy/)

AskSage operates FedRAMP-authorized infrastructure. No data is shared with any other third party by this plugin.

## Contact

For questions about this plugin's privacy practices:

- **Plugin author**: JLay2026
- **Repository**: https://github.com/JLay2026/asksage-dify-plugin
- **Email**: jalayman@gmail.com
