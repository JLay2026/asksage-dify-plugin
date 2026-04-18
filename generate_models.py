"""
Fetches all models from AskSage and generates YAML files for each one.
Run this periodically to keep your predefined models list current.
"""
import requests
import sys
import os
import yaml

API_BASE = "https://api.asksage.ai"

# Models to exclude (image generation, non-LLM)
EXCLUDE_MODELS = {
    "google-imagen-3",
    "google-imagen-4",
    "google-gemini-2.5-flash-image",
}

# Substrings that indicate an image model -- auto-excluded
EXCLUDE_PATTERNS = ["imagen", "-image"]

# Models that are completion-only (not chat), get mode: completion
COMPLETION_MODELS = {
    "aws-bedrock-titan",
}

def should_exclude(model_id):
    if model_id in EXCLUDE_MODELS:
        return True
    for pattern in EXCLUDE_PATTERNS:
        if pattern in model_id.lower():
            return True
    return False

def get_mode(model_id):
    if model_id in COMPLETION_MODELS:
        return "completion"
    return "chat"

def get_context_size(model_id):
    mid = model_id.lower()
    if "gemini-2.5-pro" in mid:
        return 1048576
    if "gemini-2.5-flash" in mid:
        return 1048576
    if "claude-45" in mid or "claude-46" in mid:
        return 200000
    if "nova-lite" in mid or "nova-micro" in mid:
        return 32000
    if "nova-pro" in mid:
        return 300000
    if "nemotron" in mid:
        return 32000
    if "titan" in mid:
        return 8000
    if "llma3" in mid and "8b" in mid:
        return 8192
    if "llma3" in mid:
        return 128000
    return 128000

def main():
    api_key = input("Enter your AskSage API key: ").strip()

    response = requests.post(
        f"{API_BASE}/server/get-models",
        headers={
            "x-access-tokens": api_key,
            "Content-Type": "application/json",
        },
        json={},
        timeout=30,
    )

    if response.status_code != 200:
        print(f"Error: API returned {response.status_code}")
        sys.exit(1)

    data = response.json()
    models = data.get("data", [])
    print(f"Found {len(models)} total models from AskSage.\n")

    os.makedirs("models/llm", exist_ok=True)
    position_list = []
    skipped = []

    for m in models:
        model_id = m.get("id", "")
        model_name = m.get("name", model_id)
        if not model_id:
            continue

        if should_exclude(model_id):
            skipped.append(model_id)
            continue

        safe_filename = model_id.replace("/", "-").replace(" ", "-")
        filepath = f"models/llm/{safe_filename}.yaml"
        mode = get_mode(model_id)
        context_size = get_context_size(model_id)

        model_def = {
            "model": model_id,
            "label": {"en_US": f"{model_name} (via AskSage)"},
            "model_type": "llm",
            "features": ["agent-thought"],
            "model_properties": {
                "mode": mode,
                "context_size": context_size,
            },
            "parameter_rules": [
                {"name": "temperature", "use_template": "temperature"},
                {
                    "name": "max_tokens",
                    "use_template": "max_tokens",
                    "required": False,
                    "default": 4096,
                    "min": 1,
                    "max": 16384,
                },
            ],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            yaml.dump(model_def, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        position_list.append(model_id)
        print(f"  Created: {filepath} (mode={mode}, ctx={context_size})")

    with open("models/llm/_position.yaml", "w", encoding="utf-8") as f:
        for mid in position_list:
            f.write(f"- {mid}\n")

    print(f"\nGenerated {len(position_list)} model YAMLs.")
    if skipped:
        print(f"Skipped {len(skipped)} non-LLM models: {', '.join(skipped)}")
    print("Updated _position.yaml")

if __name__ == "__main__":
    main()