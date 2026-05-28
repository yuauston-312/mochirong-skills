#!/usr/bin/env python3
"""Collect visually similar Mashu sticker candidates from web image search.

The target style is a white bean/ghost-like character with black line art,
simple facial expressions, mostly white background, and low color complexity.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import html
import io
import json
import re
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageStat


ROOT = Path(__file__).resolve().parents[1]
STICKER_DIR = ROOT / "assets" / "stickers"
CANDIDATE_DIR = STICKER_DIR / "candidates"
REJECTED_DIR = STICKER_DIR / "rejected" / "web-candidates"
SOURCES = STICKER_DIR / "candidate-sources.json"

DEFAULT_QUERIES = [
    "mochirong sticker",
    "mochirong emoji",
    "mochirong gif",
    "mochirong 表情包",
    "Mochirong麻薯小人无字表情包",
    "Mochirong 麻薯小人",
    "麻薯小人 无字 表情包",
    "麻薯小人 表情包",
]

EMOTIONS = [
    "sadness",
    "anxiety",
    "anger",
    "tiredness",
    "joy",
    "pride",
    "confusion",
    "loneliness",
    "gratitude",
    "playfulness",
    "neutral",
]


@dataclass
class Candidate:
    url: str
    page: str | None
    query: str


def fetch_bytes(url: str, timeout: int = 12) -> bytes | None:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 MashuSkillCollector/2.0",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            content_type = response.headers.get("Content-Type", "")
            if response.status != 200 or "image" not in content_type:
                return None
            data = response.read(3_000_000)
            return data if len(data) > 600 else None
    except Exception:
        return None


def fetch_text(url: str, timeout: int = 15) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="ignore")


def bing_candidates(query: str, limit: int) -> list[Candidate]:
    params = urllib.parse.urlencode(
        {
            "q": query,
            "count": "80",
            "qft": "+filterui:photo-transparent",
            "safeSearch": "strict",
        }
    )
    url = f"https://www.bing.com/images/search?{params}"
    try:
        text = fetch_text(url)
    except Exception:
        return []

    candidates: list[Candidate] = []
    for raw in re.findall(r'm="([^"]+)"', text):
        meta = html.unescape(raw)
        try:
            data = json.loads(meta)
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict):
            continue
        image_url = data.get("murl")
        if not image_url:
            continue
        candidates.append(Candidate(image_url, data.get("purl"), query))
        if len(candidates) >= limit:
            break
    return candidates


def direct_sohu_candidates() -> list[Candidate]:
    urls = [
        "https://q1.itc.cn/images01/20250606/da360dd13dc344b2ad632a17303cd8db.png",
        "https://q2.itc.cn/images01/20250606/61d926f588054fe6abda3db2ef38e571.png",
        "https://q3.itc.cn/images01/20250606/08b30cfbeb5d4222b93ce95e3bca139d.png",
        "https://q4.itc.cn/images01/20250606/451297570bae404aa181970b43be001e.png",
        "https://q8.itc.cn/images01/20250606/37e188292252476894ae38721d209b90.png",
        "https://q8.itc.cn/images01/20250606/e2df2526bf744325804983a7474d260a.png",
        "https://q9.itc.cn/images01/20250606/014e56a76ae0438bb103b58b88fb591c.png",
        "https://q9.itc.cn/images01/20250606/8b3a5c97fddf4ddc90e8d974ef3cdb37.png",
        "https://q9.itc.cn/images01/20250606/8f84b028d2dc441ab9979da81606c951.png",
    ]
    page = "https://www.sohu.com/a/902069413_121253246"
    return [Candidate(url, page, "direct-sohu-mochirong") for url in urls]


def analyze_image(data: bytes) -> tuple[float, Image.Image] | None:
    try:
        image = Image.open(io.BytesIO(data))
        image.seek(0)
        image = image.convert("RGBA")
    except Exception:
        return None

    width, height = image.size
    if width < 80 or height < 80 or width > 2000 or height > 2000:
        return None

    thumb = image.copy()
    thumb.thumbnail((256, 256))
    rgb = thumb.convert("RGB")
    pixels = list(rgb.getdata())
    total = len(pixels)

    whiteish = sum(1 for r, g, b in pixels if r > 225 and g > 225 and b > 225) / total
    blackish = sum(1 for r, g, b in pixels if r < 60 and g < 60 and b < 60) / total
    colorful = sum(1 for r, g, b in pixels if max(r, g, b) - min(r, g, b) > 65) / total
    mean = ImageStat.Stat(rgb).mean
    brightness = sum(mean) / 3
    aspect = min(width, height) / max(width, height)

    palette = rgb.resize((64, 64)).quantize(colors=24)
    color_count = len(palette.getcolors(maxcolors=4096) or [])

    score = 0.0
    score += min(whiteish / 0.62, 1.0) * 35
    score += min(blackish / 0.06, 1.0) * 25
    score += aspect * 15
    score += max(0.0, 1.0 - colorful / 0.18) * 15
    score += max(0.0, 1.0 - color_count / 24) * 10

    if brightness < 155 or whiteish < 0.35 or blackish < 0.01 or colorful > 0.45:
        score -= 35
    if aspect < 0.55:
        score -= 20

    return score, image


def process_candidate(candidate: Candidate, min_score: float) -> dict:
    data = fetch_bytes(candidate.url)
    if not data:
        return {"accepted": False, "reason": "download-failed", "candidate": candidate.__dict__}

    analysis = analyze_image(data)
    if not analysis:
        return {"accepted": False, "reason": "invalid-image", "candidate": candidate.__dict__}

    score, image = analysis
    return {
        "accepted": score >= min_score,
        "score": round(score, 2),
        "image": image,
        "candidate": candidate.__dict__,
    }


def next_index() -> int:
    CANDIDATE_DIR.mkdir(parents=True, exist_ok=True)
    existing = sorted(CANDIDATE_DIR.glob("mashu-candidate-*.png"))
    if not existing:
        return 1
    return max(int(path.stem.split("-")[-1]) for path in existing) + 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect Mashu-like web candidates.")
    parser.add_argument("--target", type=int, default=100)
    parser.add_argument("--per-query", type=int, default=60)
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--min-score", type=float, default=58.0)
    parser.add_argument("--query", action="append", default=[])
    args = parser.parse_args()

    CANDIDATE_DIR.mkdir(parents=True, exist_ok=True)
    REJECTED_DIR.mkdir(parents=True, exist_ok=True)

    queries = args.query or DEFAULT_QUERIES
    pool: list[Candidate] = direct_sohu_candidates()
    seen_urls: set[str] = {candidate.url for candidate in pool}
    for query in queries:
        for candidate in bing_candidates(query, args.per_query):
            if candidate.url in seen_urls:
                continue
            seen_urls.add(candidate.url)
            pool.append(candidate)
        time.sleep(0.2)

    accepted_records = []
    rejected_records = []
    index = next_index()

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(process_candidate, c, args.min_score) for c in pool]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result.get("accepted") and len(accepted_records) < args.target:
                file_name = f"mashu-candidate-{index:03d}.png"
                index += 1
                output = CANDIDATE_DIR / file_name
                result["image"].save(output, "PNG")
                record = {
                    "file": f"candidates/{file_name}",
                    "score": result["score"],
                    **result["candidate"],
                }
                accepted_records.append(record)
            else:
                rejected_records.append(
                    {
                        "score": result.get("score"),
                        "reason": result.get("reason", "below-threshold"),
                        **result["candidate"],
                    }
                )
            if len(accepted_records) >= args.target:
                break

    with SOURCES.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(
            {"accepted": accepted_records, "rejected_sample": rejected_records[:200]},
            handle,
            ensure_ascii=False,
            indent=2,
        )
        handle.write("\n")

    print(json.dumps({"accepted": len(accepted_records), "scanned": len(pool)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
