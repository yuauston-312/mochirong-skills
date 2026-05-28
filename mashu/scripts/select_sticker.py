#!/usr/bin/env python3
"""Select a Mashu sticker from the local manifest."""

from __future__ import annotations

import argparse
import html
import json
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "assets" / "stickers" / "manifest.json"
STICKER_DIR = ROOT / "assets" / "stickers"
RAW_BASE_URL = (
    "https://raw.githubusercontent.com/"
    "yuauston-312/mochirong-skills/main/mashu/assets/stickers"
)


def load_stickers() -> list[dict]:
    with MANIFEST.open("r", encoding="utf-8") as handle:
        return json.load(handle)["stickers"]


def choose_from(stickers: list[dict], strategy: str, rng: random.Random) -> dict:
    existing = [sticker for sticker in stickers if (STICKER_DIR / sticker["file"]).exists()]
    pool = existing or stickers
    if strategy == "first":
        return pool[0]
    return rng.choice(pool)


def choose_sticker(
    emotion: str,
    intent: str | None = None,
    strategy: str = "random",
    seed: str | None = None,
) -> dict:
    emotion = emotion.lower().strip()
    stickers = load_stickers()
    rng = random.Random(seed)

    primary_matches = [
        sticker
        for sticker in stickers
        if sticker.get("emotion", [None])[0] == emotion
        and (intent is None or intent == sticker.get("intent"))
    ]
    if primary_matches:
        return choose_from(primary_matches, strategy, rng)

    secondary_matches = [
        sticker
        for sticker in stickers
        if emotion in sticker.get("emotion", [])
        and (intent is None or intent == sticker.get("intent"))
    ]
    if secondary_matches:
        return choose_from(secondary_matches, strategy, rng)

    primary_matches = [
        sticker for sticker in stickers if sticker.get("emotion", [None])[0] == emotion
    ]
    if primary_matches:
        return choose_from(primary_matches, strategy, rng)

    secondary_matches = [
        sticker for sticker in stickers if emotion in sticker.get("emotion", [])
    ]
    if secondary_matches:
        return choose_from(secondary_matches, strategy, rng)

    neutral_matches = [sticker for sticker in stickers if "neutral" in sticker.get("emotion", [])]
    if neutral_matches:
        return choose_from(neutral_matches, strategy, rng)

    return choose_from(stickers, strategy, rng)


def render(sticker: dict, output_format: str) -> str:
    image_path = STICKER_DIR / sticker["file"]
    image_url = f"{RAW_BASE_URL}/{sticker['file']}"
    if output_format == "json":
        payload = {
            "id": sticker["id"],
            "label": sticker["label"],
            "path": str(image_path) if image_path.exists() else None,
            "url": image_url,
            "fallback": sticker["fallback"],
        }
        return json.dumps(payload, ensure_ascii=False)

    if image_path.exists():
        label = f"麻薯表情包：{sticker['label']}"
        src = image_url
        if output_format == "html":
            return f'<img src="{html.escape(src)}" alt="{html.escape(label)}" width="180">'
        return f"![{label}]({src})"
    return sticker["fallback"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Select a Mashu sticker.")
    parser.add_argument("--emotion", default="neutral", help="Detected user emotion.")
    parser.add_argument("--intent", default=None, help="Optional response intent.")
    parser.add_argument(
        "--strategy",
        choices=["random", "first"],
        default="random",
        help="Selection strategy. Use first for deterministic debugging.",
    )
    parser.add_argument("--seed", default=None, help="Optional seed for repeatable random selection.")
    parser.add_argument(
        "--format",
        choices=["html", "markdown", "json"],
        default="markdown",
        help="Output format.",
    )
    args = parser.parse_args()

    print(render(choose_sticker(args.emotion, args.intent, args.strategy, args.seed), args.format))


if __name__ == "__main__":
    main()
