#!/usr/bin/env python3
"""Collect public SigStick sticker previews for Mashu."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STICKER_DIR = ROOT / "assets" / "stickers"
COLLECTED_DIR = STICKER_DIR / "collected"
MANIFEST = STICKER_DIR / "manifest.json"
SOURCES = STICKER_DIR / "sources.json"

PACKS = [
    {
        "name": "麻薯1",
        "id": "EbetRhLdtAwlKvoD1i81",
        "page": "https://www.sigstick.com/pack/EbetRhLdtAwlKvoD1i81-%E9%BA%BB%E8%96%AF1",
    },
    {
        "name": "麻薯2",
        "id": "ooPKRJBk5ijOBwYSv8km",
        "page": "https://www.sigstick.com/pack/ooPKRJBk5ijOBwYSv8km",
    },
    {
        "name": "小麻薯貼紙",
        "id": "VVgbOetcsKElCIratnCu",
        "page": "https://www.sigstick.com/pack/VVgbOetcsKElCIratnCu-%E5%B0%8F%E9%BA%BB%E8%96%AF%E8%B2%BC%E7%B4%99",
    },
    {
        "name": "Mochi",
        "id": "2Rf5vmsvlBo4evNUdIVu",
        "page": "https://www.sigstick.com/pack/2Rf5vmsvlBo4evNUdIVu-mochi",
    },
    {
        "name": "MOCHI CAT",
        "id": "7C9BKtNVZFci8hZ8TTXs",
        "page": "https://www.sigstick.com/pack/7C9BKtNVZFci8hZ8TTXs-mochi-cat",
    },
    {
        "name": "Mochi",
        "id": "AxVLXhrdmYb009ezjf7f",
        "page": "https://www.sigstick.com/pack/AxVLXhrdmYb009ezjf7f-mochi",
    },
    {
        "name": "mochi mochi",
        "id": "X6QTdBkabG5aOz5Ibslr",
        "page": "https://www.sigstick.com/pack/X6QTdBkabG5aOz5Ibslr",
    },
    {
        "name": "Mochi Mochi Peach & Goma",
        "id": "vkjJuKyVqIWu0Js2xOKG",
        "page": "https://www.sigstick.com/pack/vkjJuKyVqIWu0Js2xOKG",
    },
    {
        "name": "Mochi",
        "id": "CkYmMnKSBDA75LYAfmjU",
        "page": "https://www.sigstick.com/pack/CkYmMnKSBDA75LYAfmjU",
    },
]

EMOTION_CYCLE = [
    ("sadness", "comfort", "抱抱"),
    ("anxiety", "calm", "摸摸头"),
    ("anger", "validate", "一起气鼓鼓"),
    ("tiredness", "accompany", "瘫成小饼"),
    ("joy", "celebrate", "开心转圈"),
    ("pride", "celebrate", "举小旗"),
    ("confusion", "clarify", "歪头疑惑"),
    ("loneliness", "accompany", "陪你坐坐"),
    ("gratitude", "warm", "比心"),
    ("playfulness", "tease", "眨眼"),
    ("neutral", "acknowledge", "探头"),
]


def fetch(url: str, timeout: int = 3) -> bytes | None:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 MashuSkillCollector/1.0",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            content_type = response.headers.get("Content-Type", "")
            if response.status != 200 or "image" not in content_type:
                return None
            return response.read()
    except (urllib.error.URLError, TimeoutError):
        return None


def load_manifest() -> dict:
    with MANIFEST.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: object) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect SigStick sticker previews.")
    parser.add_argument("--target", type=int, default=100)
    parser.add_argument("--max-index", type=int, default=80)
    parser.add_argument("--delay", type=float, default=0.02)
    parser.add_argument("--miss-limit", type=int, default=12)
    args = parser.parse_args()

    COLLECTED_DIR.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest()
    existing_files = {item.get("file") for item in manifest["stickers"]}
    seen_hashes: set[str] = set()
    records = []

    for path in COLLECTED_DIR.glob("*"):
        if path.is_file():
            seen_hashes.add(hashlib.sha256(path.read_bytes()).hexdigest())

    count = len(list(COLLECTED_DIR.glob("*.png")))
    for pack in PACKS:
        misses = 0
        for index in range(1, args.max_index + 1):
            if count >= args.target:
                break
            url = f"https://cdn2.cdnstep.com/{pack['id']}/0-{index}.thumb128.png"
            data = fetch(url)
            time.sleep(args.delay)
            if not data:
                misses += 1
                if misses >= args.miss_limit and index > 20:
                    break
                continue
            misses = 0

            digest = hashlib.sha256(data).hexdigest()
            if digest in seen_hashes:
                continue
            seen_hashes.add(digest)

            count += 1
            emotion, intent, label = EMOTION_CYCLE[(count - 1) % len(EMOTION_CYCLE)]
            filename = f"collected/mashu-{count:03d}-{emotion}.png"
            output_path = STICKER_DIR / filename
            output_path.write_bytes(data)

            sticker_id = f"collected-{count:03d}-{emotion}"
            if filename not in existing_files:
                manifest["stickers"].append(
                    {
                        "id": sticker_id,
                        "emotion": [emotion],
                        "intent": intent,
                        "label": f"{label}{count:03d}",
                        "file": filename,
                        "fallback": f"[麻薯表情包：{label}]",
                        "source": pack["page"],
                    }
                )
                existing_files.add(filename)

            records.append(
                {
                    "file": filename,
                    "pack": pack["name"],
                    "source": pack["page"],
                    "cdn": url,
                    "sha256": digest,
                }
            )
        if count >= args.target:
            break

    write_json(MANIFEST, manifest)
    write_json(SOURCES, records)
    print(f"Collected {count} sticker image(s).")


if __name__ == "__main__":
    main()
