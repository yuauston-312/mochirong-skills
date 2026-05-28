#!/usr/bin/env python3
"""Download Mochirong candidates from a DuckDuckGo image result export."""

from __future__ import annotations

import concurrent.futures
import hashlib
import json
import mimetypes
import re
import urllib.request
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parents[0]
STICKER_DIR = ROOT / "assets" / "stickers"
CANDIDATE_DIR = STICKER_DIR / "candidates"
RESULTS = PROJECT / "ddg-images.json"
SOURCES = STICKER_DIR / "mochirong-sources.json"
DUITANG_EXPORT = PROJECT / "duitang-pumupuz.html"

ALBUMS = [
    "https://www.qiubiaoqing.com/album/user_album/800412751145996233.html",
    "https://www.qiubiaoqing.com/album/user_album/817972807060160867.html",
]

SOHU = [
    {
        "image": "https://q1.itc.cn/images01/20250606/da360dd13dc344b2ad632a17303cd8db.png",
        "url": "https://www.sohu.com/a/902069413_121253246",
        "title": "Mochirong麻薯小人无字表情包",
    },
    {
        "image": "https://q2.itc.cn/images01/20250606/61d926f588054fe6abda3db2ef38e571.png",
        "url": "https://www.sohu.com/a/902069413_121253246",
        "title": "Mochirong麻薯小人无字表情包",
    },
    {
        "image": "https://q3.itc.cn/images01/20250606/08b30cfbeb5d4222b93ce95e3bca139d.png",
        "url": "https://www.sohu.com/a/902069413_121253246",
        "title": "Mochirong麻薯小人无字表情包",
    },
    {
        "image": "https://q4.itc.cn/images01/20250606/451297570bae404aa181970b43be001e.png",
        "url": "https://www.sohu.com/a/902069413_121253246",
        "title": "Mochirong麻薯小人无字表情包",
    },
    {
        "image": "https://q8.itc.cn/images01/20250606/37e188292252476894ae38721d209b90.png",
        "url": "https://www.sohu.com/a/902069413_121253246",
        "title": "Mochirong麻薯小人无字表情包",
    },
    {
        "image": "https://q8.itc.cn/images01/20250606/e2df2526bf744325804983a7474d260a.png",
        "url": "https://www.sohu.com/a/902069413_121253246",
        "title": "Mochirong麻薯小人无字表情包",
    },
    {
        "image": "https://q9.itc.cn/images01/20250606/014e56a76ae0438bb103b58b88fb591c.png",
        "url": "https://www.sohu.com/a/902069413_121253246",
        "title": "Mochirong麻薯小人无字表情包",
    },
    {
        "image": "https://q9.itc.cn/images01/20250606/8b3a5c97fddf4ddc90e8d974ef3cdb37.png",
        "url": "https://www.sohu.com/a/902069413_121253246",
        "title": "Mochirong麻薯小人无字表情包",
    },
    {
        "image": "https://q9.itc.cn/images01/20250606/8f84b028d2dc441ab9979da81606c951.png",
        "url": "https://www.sohu.com/a/902069413_121253246",
        "title": "Mochirong麻薯小人无字表情包",
    },
]


def is_relevant(item: dict) -> bool:
    text = f"{item.get('title', '')} {item.get('url', '')}".lower()
    if any(bad in text for bad in ["pneumothorax", "x-ray", "anime", "nikke", "pokemon", "zerochan", "seaart", "deviantart"]):
        return False
    return any(term in text for term in ["mochirong麻薯小人", "mochirong 麻薯小人", "麻薯小人", "麻薯表情包", "麻薯宝宝", "pumupuz"])


def fetch_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8", errors="ignore")


def album_items() -> list[dict]:
    items = []
    image_pattern = re.compile(r"https://imgs\.qiubiaoqing\.com/[^\"'<> ]+\.(?:jpg|jpeg|png|gif|webp)", re.I)
    for album in ALBUMS:
        for page in range(1, 6):
            url = album if page == 1 else f"{album}?page={page}"
            try:
                text = fetch_text(url)
            except Exception:
                continue
            for image in sorted(set(image_pattern.findall(text))):
                if "/album_cover/" in image:
                    continue
                if not any(marker in image for marker in ["/imgs/68ab", "/imgs/68eb", "/user_pre_up_imgs/67e549", "/user_pre_up_imgs/681628"]):
                    continue
                items.append({"image": image, "url": url, "title": "Mochirong麻薯小人表情包"})
    return items


def duitang_items() -> list[dict]:
    if not DUITANG_EXPORT.exists():
        return []
    text = DUITANG_EXPORT.read_text(encoding="utf-8", errors="ignore")
    urls = sorted(
        set(
            re.findall(
                r"https://c-ssl\.duitang\.com/uploads/blog/202504/02/[A-Za-z0-9]+\.jpeg",
                text,
            )
        )
    )
    return [
        {
            "image": url,
            "url": "https://m.duitang.com/blog/?id=1551503177",
            "title": "pumupuz 麻薯我们喜欢你",
        }
        for url in urls
    ]


def extension(url: str, content_type: str | None) -> str:
    guessed = mimetypes.guess_extension((content_type or "").split(";")[0].strip())
    if guessed in [".jpeg", ".jpg", ".png", ".gif", ".webp"]:
        return ".jpg" if guessed == ".jpeg" else guessed
    match = re.search(r"\.(png|jpg|jpeg|gif|webp)(?:$|[?#])", url, re.I)
    if match:
        ext = match.group(1).lower()
        return ".jpg" if ext == "jpeg" else f".{ext}"
    return ".png"


def download(item: dict) -> dict | None:
    url = item["image"]
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": item.get("url") or "https://www.qiubiaoqing.com/",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            if response.status != 200:
                return None
            data = response.read(4_000_000)
            if len(data) < 500:
                return None
            ext = extension(url, response.headers.get("Content-Type"))
    except Exception:
        return None

    try:
        image = Image.open(PathLikeBytes(data))
        image.seek(0)
        if not looks_like_sticker(image):
            return None
    except Exception:
        if ext not in [".gif", ".webp"]:
            return None

    return {"data": data, "ext": ext, "item": item, "sha256": hashlib.sha256(data).hexdigest()}


def looks_like_sticker(image: Image.Image) -> bool:
    image = image.convert("RGB")
    width, height = image.size
    if width < 70 or height < 70 or min(width, height) / max(width, height) < 0.45:
        return False
    thumb = image.copy()
    thumb.thumbnail((180, 180))
    pixels = list(thumb.getdata())
    total = len(pixels)
    whiteish = sum(1 for r, g, b in pixels if r > 220 and g > 220 and b > 220) / total
    blackish = sum(1 for r, g, b in pixels if r < 70 and g < 70 and b < 70) / total
    colorful = sum(1 for r, g, b in pixels if max(r, g, b) - min(r, g, b) > 80) / total
    very_dark = sum(1 for r, g, b in pixels if r < 25 and g < 25 and b < 25) / total
    return whiteish > 0.35 and blackish > 0.01 and colorful < 0.38 and very_dark < 0.5


class PathLikeBytes:
    def __init__(self, data: bytes):
        self.data = data
        self.offset = 0

    def read(self, size: int = -1) -> bytes:
        if size == -1:
            size = len(self.data) - self.offset
        chunk = self.data[self.offset : self.offset + size]
        self.offset += len(chunk)
        return chunk

    def seek(self, offset: int, whence: int = 0) -> int:
        if whence == 0:
            self.offset = offset
        elif whence == 1:
            self.offset += offset
        elif whence == 2:
            self.offset = len(self.data) + offset
        return self.offset

    def tell(self) -> int:
        return self.offset


def main() -> None:
    CANDIDATE_DIR.mkdir(parents=True, exist_ok=True)
    items = SOHU + album_items() + duitang_items()
    if RESULTS.exists():
        items += json.loads(RESULTS.read_text(encoding="utf-8"))

    filtered = []
    seen_urls = set()
    for item in items:
        if not is_relevant(item):
            continue
        url = item.get("image")
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        filtered.append(item)

    records = []
    seen_hashes = set()
    with concurrent.futures.ThreadPoolExecutor(max_workers=24) as executor:
        futures = [executor.submit(download, item) for item in filtered]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if not result or result["sha256"] in seen_hashes:
                continue
            seen_hashes.add(result["sha256"])
            index = len(records) + 1
            filename = f"mochirong-{index:03d}{result['ext']}"
            path = CANDIDATE_DIR / filename
            path.write_bytes(result["data"])
            records.append(
                {
                    "file": f"candidates/{filename}",
                    "sha256": result["sha256"],
                    "source": result["item"].get("url"),
                    "image": result["item"].get("image"),
                    "title": result["item"].get("title"),
                }
            )
            if len(records) >= 100:
                break

    SOURCES.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"downloaded": len(records), "filtered": len(filtered)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
