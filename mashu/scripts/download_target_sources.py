#!/usr/bin/env python3
"""Download curated Mashu-like sticker source URLs."""

from __future__ import annotations

import json
import subprocess
import urllib.request
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
STICKER_DIR = ROOT / "assets" / "stickers"
SOURCES = STICKER_DIR / "target-sources.json"
TARGET_DIR = STICKER_DIR / "candidates"


def download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def download_to_file(url: str, output: Path) -> None:
    try:
        output.write_bytes(download(url))
        return
    except Exception:
        pass

    ps_command = [
        "powershell",
        "-NoProfile",
        "-Command",
        (
            "$ProgressPreference='SilentlyContinue'; "
            f"Invoke-WebRequest -Uri '{url}' -UseBasicParsing -OutFile '{output}'"
        ),
    ]
    try:
        subprocess.run(ps_command, check=True)
        return
    except subprocess.CalledProcessError:
        pass

    curl_command = [
        "curl.exe",
        "-L",
        "--http1.1",
        "-k",
        "--retry",
        "3",
        "--max-time",
        "30",
        "-A",
        "Mozilla/5.0",
        url,
        "-o",
        str(output),
    ]
    subprocess.run(curl_command, check=True)


def main() -> None:
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    sources = json.loads(SOURCES.read_text(encoding="utf-8"))
    records = []
    for index, item in enumerate(sources, 1):
        ext = ".gif" if ".gif" in item["url"].lower() else ".webp"
        output = TARGET_DIR / f"target-{index:03d}{ext}"
        if not output.exists():
            download_to_file(item["url"], output)

        # Save a PNG preview for contact sheets and quick visual review.
        preview = TARGET_DIR / f"target-{index:03d}.png"
        try:
            image = Image.open(output)
            image.seek(0)
            image.convert("RGBA").save(preview)
        except Exception:
            preview = output

        records.append({**item, "file": f"candidates/{output.name}", "preview": f"candidates/{preview.name}"})

    (STICKER_DIR / "target-downloads.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"downloaded": len(records)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
