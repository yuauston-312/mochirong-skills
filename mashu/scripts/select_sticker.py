#!/usr/bin/env python3
"""Select a Mashu sticker from the local manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "assets" / "stickers" / "manifest.json"
STICKER_DIR = ROOT / "assets" / "stickers"


def load_stickers() -> list[dict]:
    with MANIFEST.open("r", encoding="utf-8") as handle:
        return json.load(handle)["stickers"]


def choose_sticker(emotion: str, intent: str | None = None) -> dict:
    emotion = emotion.lower().strip()
    stickers = load_stickers()

    primary_matches = [
        sticker
        for sticker in stickers
        if sticker.get("emotion", [None])[0] == emotion
        and (intent is None or intent == sticker.get("intent"))
    ]
    for sticker in primary_matches:
        if (STICKER_DIR / sticker["file"]).exists():
            return sticker
    if primary_matches:
        return primary_matches[0]

    secondary_matches = [
        sticker
        for sticker in stickers
        if emotion in sticker.get("emotion", [])
        and (intent is None or intent == sticker.get("intent"))
    ]
    for sticker in secondary_matches:
        if (STICKER_DIR / sticker["file"]).exists():
            return sticker
    if secondary_matches:
        return secondary_matches[0]

    primary_matches = [
        sticker for sticker in stickers if sticker.get("emotion", [None])[0] == emotion
    ]
    for sticker in primary_matches:
        if (STICKER_DIR / sticker["file"]).exists():
            return sticker
    if primary_matches:
        return primary_matches[0]

    secondary_matches = [
        sticker for sticker in stickers if emotion in sticker.get("emotion", [])
    ]
    for sticker in secondary_matches:
        if (STICKER_DIR / sticker["file"]).exists():
            return sticker
    if secondary_matches:
        return secondary_matches[0]

    for sticker in stickers:
        if "neutral" in sticker.get("emotion", []) and (STICKER_DIR / sticker["file"]).exists():
            return sticker

    for sticker in stickers:
        if "neutral" in sticker.get("emotion", []):
            return sticker

    return stickers[0]


def render(sticker: dict, output_format: str) -> str:
    image_path = STICKER_DIR / sticker["file"]
    if output_format == "json":
        payload = {
            "id": sticker["id"],
            "label": sticker["label"],
            "path": str(image_path) if image_path.exists() else None,
            "fallback": sticker["fallback"],
        }
        return json.dumps(payload, ensure_ascii=False)

    if image_path.exists():
        return f"![麻薯表情包：{sticker['label']}]({image_path.as_posix()})"
    return sticker["fallback"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Select a Mashu sticker.")
    parser.add_argument("--emotion", default="neutral", help="Detected user emotion.")
    parser.add_argument("--intent", default=None, help="Optional response intent.")
    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format.",
    )
    args = parser.parse_args()

    print(render(choose_sticker(args.emotion, args.intent), args.format))


if __name__ == "__main__":
    main()
