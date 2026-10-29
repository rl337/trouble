#!/usr/bin/env python3
"""Download or load an image and write a small WebP thumbnail for post media."""

from __future__ import annotations

import argparse
import sys
from io import BytesIO
from pathlib import Path
from urllib.request import urlopen

from PIL import Image

MAX_WIDTH = 480
WEBP_QUALITY = 82


def load_image(source: str) -> Image.Image:
    if source.startswith(("http://", "https://")):
        with urlopen(source, timeout=60) as response:
            raw = response.read()
        img = Image.open(BytesIO(raw))
    else:
        img = Image.open(source)
    img.load()
    return img


def make_thumbnail(img: Image.Image) -> Image.Image:
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    width, height = img.size
    if width > MAX_WIDTH:
        height = max(1, int(height * MAX_WIDTH / width))
        width = MAX_WIDTH
        img = img.resize((width, height), Image.Resampling.LANCZOS)
    return img


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create a repo WebP thumbnail (~480px wide) for post media."
    )
    parser.add_argument("source", help="Image URL or local path")
    parser.add_argument("out_path", help="Output path, e.g. posts/YYYY/MM/DD/<id>/media/0.webp")
    args = parser.parse_args(argv)

    out = Path(args.out_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    try:
        img = load_image(args.source)
        thumb = make_thumbnail(img)
        thumb.save(out, format="WEBP", quality=WEBP_QUALITY, method=6)
    except OSError as exc:
        print(f"Failed to write thumbnail: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote {out} ({out.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
