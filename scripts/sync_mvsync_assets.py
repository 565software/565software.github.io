#!/usr/bin/env python3
"""mvsync リポジトリから HP 用の画像アセットを取り込み、Web 向けに軽量化して配置する。

使い方:
    python3 scripts/sync_mvsync_assets.py
    python3 scripts/sync_mvsync_assets.py --src /path/to/mvsync
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

LANGS = ("ja", "en")
CUTS = (
    "01-sync",
    "02-zoom",
    "03-tune",
    "04-playmode",
    "05-saved",
    "06-export",
)
EXPORT_EXTRAS = (
    ("06-export-video.png", "06-export-video.webp"),
    ("06-export-capture.jpg", "06-export-capture.webp"),
)


def run_ffmpeg(args: list[str]) -> None:
    cmd = ["ffmpeg", "-y", "-loglevel", "error", *args]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {' '.join(cmd)}\n{result.stderr}")


def convert_webp(src: Path, dst: Path, width: int, quality: int) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    run_ffmpeg(
        [
            "-i",
            str(src),
            "-vf",
            f"scale={width}:-2:flags=lanczos",
            "-c:v",
            "libwebp",
            "-q:v",
            str(quality),
            "-compression_level",
            "6",
            str(dst),
        ]
    )


def convert_og_jpeg(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    run_ffmpeg(
        [
            "-i",
            str(src),
            "-q:v",
            "3",
            str(dst),
        ]
    )


def parse_ts_consts(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    consts: dict[str, str] = {}
    for match in re.finditer(r'export const ([A-Z0-9_]+)\s*=\s*(?:\n\s*)?"([^"]+)";', text):
        consts[match.group(1)] = match.group(2)
    for match in re.finditer(r"export const ([A-Z0-9_]+)\s*=\s*([0-9.]+);", text):
        consts[match.group(1)] = match.group(2)
    return consts


def generate_icon_svg(icon_shapes_path: Path, dst: Path) -> None:
    consts = parse_ts_consts(icon_shapes_path)
    required = ("ICON_BG_FROM", "ICON_BG_TO", "ICON_SCREEN", "ICON_SCREENS", "ICON_PLAY", "ICON_PLAYS")
    missing = [key for key in required if key not in consts]
    if missing:
        raise RuntimeError(f"Missing constants in {icon_shapes_path}: {', '.join(missing)}")

    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="18 18 72 72">\n'
        '  <defs>\n'
        '    <linearGradient id="g" x1="0" y1="0" x2="108" y2="108" gradientUnits="userSpaceOnUse">\n'
        f'      <stop offset="0" stop-color="{consts["ICON_BG_FROM"]}" />\n'
        f'      <stop offset="1" stop-color="{consts["ICON_BG_TO"]}" />\n'
        '    </linearGradient>\n'
        '  </defs>\n'
        '  <rect width="108" height="108" fill="url(#g)" />\n'
        f'  <path fill="{consts["ICON_SCREEN"]}" d="{consts["ICON_SCREENS"]}" />\n'
        f'  <path fill="{consts["ICON_PLAY"]}" d="{consts["ICON_PLAYS"]}" />\n'
        '</svg>\n'
    )
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(svg, encoding="utf-8")


def generate_brand_logo_svg(icon_shapes_path: Path, wordmark_path: Path, dst: Path) -> None:
    icons = parse_ts_consts(icon_shapes_path)
    words = parse_ts_consts(wordmark_path)

    side = float(words["WORDMARK_EM"])
    gap = side * 0.25
    left = -(side + gap)
    top = -side * 0.86
    width = side + gap + float(words["WORDMARK_WIDTH"])
    bottom = max(side + top, float(words["WORDMARK_DESCENT"]))
    height = bottom - top
    scale = side / 72.0

    svg = (
        f'<svg class="mvsync-logo" xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="{left:g} {top:g} {width:g} {height:g}" aria-hidden="true">\n'
        '  <defs>\n'
        '    <linearGradient id="mvsyncLogoBg" gradientUnits="userSpaceOnUse" x1="18" y1="18" x2="90" y2="90">\n'
        f'      <stop offset="0" stop-color="{icons["ICON_BG_FROM"]}" />\n'
        f'      <stop offset="1" stop-color="{icons["ICON_BG_TO"]}" />\n'
        '    </linearGradient>\n'
        '  </defs>\n'
        f'  <g transform="translate({left:g} {top:g}) scale({scale:.6f}) translate(-18 -18)">\n'
        '    <rect x="18" y="18" width="72" height="72" rx="16" fill="url(#mvsyncLogoBg)" />\n'
        f'    <path fill="{icons["ICON_SCREEN"]}" d="{icons["ICON_SCREENS"]}" />\n'
        f'    <path fill="{icons["ICON_PLAY"]}" d="{icons["ICON_PLAYS"]}" />\n'
        '  </g>\n'
        f'  <path fill="currentColor" d="{words["WORDMARK_PATH"]}" />\n'
        '</svg>\n'
    )
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(svg, encoding="utf-8")


def format_kb(path: Path) -> str:
    return f"{path.stat().st_size / 1024:.1f} KB"


def sync_assets(mvsync_dir: Path, out_dir: Path, width: int, quality: int) -> None:
    if not shutil.which("ffmpeg"):
        print("Error: ffmpeg is required but was not found in PATH.", file=sys.stderr)
        sys.exit(1)

    if not mvsync_dir.is_dir():
        print(f"Error: mvsync directory not found: {mvsync_dir}", file=sys.stderr)
        sys.exit(1)

    repo_root = out_dir.parent.parent
    tasks: list[tuple[str, Path, Path]] = []

    icon_shapes_src = mvsync_dir / "src" / "icon-shapes.ts"
    wordmark_src = mvsync_dir / "src" / "wordmark.ts"
    tasks.append(("icon_svg", icon_shapes_src, out_dir / "icon.svg"))
    tasks.append(("logo_svg", wordmark_src, repo_root / "_includes" / "mvsync-logo.svg"))

    for lang in LANGS:
        og_src = mvsync_dir / "store-assets" / lang / "feature-graphic.png"
        tasks.append(("og", og_src, out_dir / lang / "og.jpg"))

        raw_dir = mvsync_dir / "store-assets" / lang / "phone-raw"
        for cut in CUTS:
            shot_src = raw_dir / f"{cut}.png"
            tasks.append(("shot", shot_src, out_dir / lang / f"{cut}.webp"))
        for src_name, dst_name in EXPORT_EXTRAS:
            tasks.append(("extra", raw_dir / src_name, out_dir / lang / dst_name))

    missing = [src for _, src, _ in tasks if not src.is_file()]
    if missing:
        print("Error: source assets are missing. Run `STORE_DEVICE=phone npm run store` in mvsync first:", file=sys.stderr)
        for path in missing:
            print(f"  - {path}", file=sys.stderr)
        sys.exit(1)

    for kind, src, dst in tasks:
        if kind == "icon_svg":
            generate_icon_svg(src, dst)
        elif kind == "logo_svg":
            generate_brand_logo_svg(icon_shapes_src, src, dst)
        elif kind == "og":
            convert_og_jpeg(src, dst)
        elif kind == "extra":
            convert_webp(src, dst, width=min(width, 480), quality=quality)
        else:
            convert_webp(src, dst, width=width, quality=quality)

        rel_dst = dst.relative_to(repo_root)
        print(f"synced {rel_dst} ({format_kb(src)} -> {format_kb(dst)})")


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    default_src = Path(os.environ.get("MVSYNC_DIR") or (repo_root.parent / "mvsync"))

    parser = argparse.ArgumentParser(description="Sync and optimize MVsync assets for the website.")
    parser.add_argument("--src", type=Path, default=default_src, help="Path to mvsync repository")
    parser.add_argument("--width", type=int, default=640, help="Target width in px for screenshots (default: 640)")
    parser.add_argument("--quality", type=int, default=82, help="WebP quality 0-100 (default: 82)")
    args = parser.parse_args()

    out_dir = repo_root / "assets" / "mvsync"
    sync_assets(args.src.resolve(), out_dir, width=args.width, quality=args.quality)


if __name__ == "__main__":
    main()
