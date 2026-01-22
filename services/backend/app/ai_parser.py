import json
import os
from typing import Dict, Any, List

from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

# Allowed values (hard limits)
ALLOWED_FORMATS = {"jpg", "jpeg", "png", "webp"}
ALLOWED_ACTIONS = {"convert", "resize", "compress"}


def _safe_int(value, default=None, min_val=None, max_val=None):
    try:
        v = int(value)
        if min_val is not None:
            v = max(v, min_val)
        if max_val is not None:
            v = min(v, max_val)
        return v
    except Exception:
        return default


def _validate_actions(actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Validate and sanitize AI-produced actions.
    Unknown actions or invalid fields are ignored.
    """
    validated = []

    for action in actions:
        if not isinstance(action, dict):
            continue

        action_type = action.get("action")
        if action_type not in ALLOWED_ACTIONS:
            continue

        if action_type == "convert":
            fmt = action.get("format", "").lower()
            if fmt in ALLOWED_FORMATS:
                validated.append({
                    "action": "convert",
                    "format": fmt
                })

        elif action_type == "resize":
            width = _safe_int(action.get("width"), min_val=50, max_val=5000)
            height = _safe_int(action.get("height"), min_val=50, max_val=5000)
            keep_ratio = bool(action.get("maintain_aspect_ratio", True))

            if width or height:
                validated.append({
                    "action": "resize",
                    "width": width,
                    "height": height,
                    "maintain_aspect_ratio": keep_ratio
                })

        elif action_type == "compress":
            target_kb = _safe_int(action.get("target_kb"), min_val=10, max_val=5000)
            if target_kb:
                validated.append({
                    "action": "compress",
                    "target_kb": target_kb
                })

    return validated


def parse_prompt_with_ai(prompt: str, file_type: str = "image") -> Dict[str, Any]:
    """
    Use OpenAI to convert a natural language prompt into structured actions JSON.
    Falls back safely if AI fails.
    """

    system_prompt = (
        "You are an AI planner for a file processing system.\n"
        "Your job is to convert a user request into a STRICT JSON plan.\n\n"
        "Rules:\n"
        "- Output ONLY valid JSON\n"
        "- No explanations\n"
        "- No markdown\n"
        "- No extra text\n\n"
        "Schema:\n"
        "{\n"
        '  "file_type": "image",\n'
        '  "actions": [\n'
        "    { action objects }\n"
        "  ]\n"
        "}\n\n"
        "Supported actions:\n"
        "- convert: { action: 'convert', format: 'jpg|jpeg|png|webp' }\n"
        "- resize: { action: 'resize', width, height, maintain_aspect_ratio }\n"
        "- compress: { action: 'compress', target_kb }\n"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=300
        )

        content = response.choices[0].message.content
        raw = json.loads(content)

        actions = raw.get("actions", [])
        validated_actions = _validate_actions(actions)

        if not validated_actions:
            raise ValueError("No valid actions produced by AI")

        return {
            "file_type": file_type,
            "actions": validated_actions
        }

    except Exception as e:
        # Safe fallback: no AI actions, let worker decide
        return {
            "file_type": file_type,
            "actions": []
        }
