"""
ai_parser.py

Mock AI layer for Sprint 4.
Converts user prompt text into structured action JSON.

Later this file can be replaced with real GenAI (OpenAI / Gemini),
without changing the rest of the system.
"""

import re
from typing import Dict, Any


def parse_prompt_to_actions(prompt: str) -> Dict[str, Any]:
    """
    Convert free-text prompt into structured action schema.

    This is a deterministic, rule-based mock.
    """

    prompt = (prompt or "").lower()

    actions: Dict[str, Any] = {
        "type": "image"
    }

    # --------------------
    # FORMAT CONVERSION
    # --------------------
    if "webp" in prompt:
        actions["convert"] = {"format": "webp"}
    elif "png" in prompt:
        actions["convert"] = {"format": "png"}
    elif "jpg" in prompt or "jpeg" in prompt:
        actions["convert"] = {"format": "jpeg"}

    # --------------------
    # RESIZE
    # --------------------
    # Passport size (India standard)
    if "passport" in prompt:
        actions["resize"] = {
            "width": 413,
            "height": 531,
            "mode": "fit"
        }
    else:
        # Match 30x30, 300x300, etc.
        match = re.search(r"(\d{2,4})\s*[xX]\s*(\d{2,4})", prompt)
        if match:
            actions["resize"] = {
                "width": int(match.group(1)),
                "height": int(match.group(2)),
                "mode": "fit"
            }

    # --------------------
    # COMPRESSION
    # --------------------
    if "very small" in prompt:
        actions["compression"] = {"quality": 45}
    elif "compress" in prompt or "small" in prompt:
        actions["compression"] = {"quality": 65}
    elif "high quality" in prompt:
        actions["compression"] = {"quality": 90}

    return actions
