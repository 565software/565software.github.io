#!/usr/bin/env python3
import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# フォント探索候補パス
FONT_CANDIDATES = [
    # Ubuntu / Debian noto
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
    # IPA Font
    "/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf",
    "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf",
    "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
    "/usr/share/fonts/truetype/ipafont/ipagp.ttf",
    # macOS
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
]

DEFAULT_FALLBACK_TEXT = """【特定商取引法に基づく表記】

■ 販売事業者名
（サンプル事業者名）

■ 代表責任者
（サンプル責任者名）

■ 所在地
〒000-0000 東京都〇〇区〇〇 1-2-3

■ 電話番号
03-0000-0000
※ お問い合わせはメールにてお願いいたします。

■ メールアドレス
565software@gmail.com

■ 販売価格
各アプリ内の購入画面に記載（税込）

■ お支払方法
Google Play の決済手段（クレジットカード、キャリア決済等）に準じます

■ 提供時期
決済手続き完了後、直ちにご利用いただけます

■ 返品・キャンセル
デジタルコンテンツの性質上、購入確定後の返品・返金はお受けできません
"""

def find_font():
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            return path
    return None

def wrap_text(text, font, max_width, draw):
    lines = []
    for raw_line in text.splitlines():
        if not raw_line:
            lines.append("")
            continue
        current_line = ""
        for char in raw_line:
            test_line = current_line + char
            bbox = draw.textbbox((0, 0), test_line, font=font)
            w = bbox[2] - bbox[0]
            if w <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = char
        if current_line:
            lines.append(current_line)
    return lines

def get_line_height(font):
    ascent, descent = font.getmetrics()
    return ascent + descent

def generate_image(text: str, output_path: str):
    font_path = find_font()
    if not font_path:
        print("Error: Japanese font not found. Please install fonts-noto-cjk or ipafont.", file=sys.stderr)
        sys.exit(1)

    # 2x Retina解像度用
    title_font = ImageFont.truetype(font_path, 40)
    heading_font = ImageFont.truetype(font_path, 28)
    body_font = ImageFont.truetype(font_path, 26)
    sub_font = ImageFont.truetype(font_path, 22)

    title_lh = get_line_height(title_font)
    heading_lh = get_line_height(heading_font)
    body_lh = get_line_height(body_font)
    sub_lh = get_line_height(sub_font)

    # 描画キャンバス設計（2xスケール）
    card_width = 1200
    padding_x = 70
    padding_y = 60
    content_width = card_width - (padding_x * 2)

    dummy_img = Image.new("RGBA", (card_width, 100), (255, 255, 255, 0))
    draw = ImageDraw.Draw(dummy_img)

    rendered_items = []
    current_y = padding_y

    for raw_line in text.strip().splitlines():
        line = raw_line.strip()
        if not line:
            current_y += 18
            continue

        if line.startswith("【") and line.endswith("】"):
            # メインタイトル
            title_text = line.strip("【】")
            rendered_items.append({
                "type": "title",
                "text": title_text,
                "font": title_font,
                "color": "#111827",
                "y": current_y,
            })
            current_y += title_lh + 25
            rendered_items.append({
                "type": "separator",
                "y": current_y
            })
            current_y += 35
        elif line.startswith("■"):
            # 項目見出し
            current_y += 14
            rendered_items.append({
                "type": "heading",
                "text": line,
                "font": heading_font,
                "color": "#1f2937",
                "y": current_y,
            })
            current_y += heading_lh + 12
        elif line.startswith("※"):
            # 補足説明
            wrapped = wrap_text(line, sub_font, content_width - 30, draw)
            for wline in wrapped:
                rendered_items.append({
                    "type": "sub",
                    "text": wline,
                    "font": sub_font,
                    "color": "#6b7280",
                    "x_offset": 30,
                    "y": current_y,
                })
                current_y += sub_lh + 8
            current_y += 6
        else:
            # 本文
            wrapped = wrap_text(line, body_font, content_width - 30, draw)
            for wline in wrapped:
                rendered_items.append({
                    "type": "body",
                    "text": wline,
                    "font": body_font,
                    "color": "#374151",
                    "x_offset": 30,
                    "y": current_y,
                })
                current_y += body_lh + 12

    total_height = current_y + padding_y

    # 画像作成（カードデザイン）
    # 背景は透過、角丸四角形（白地＋薄いグレー枠線）
    img = Image.new("RGBA", (card_width, total_height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    # 白地角丸四角形と枠線
    card_rect = [2, 2, card_width - 3, total_height - 3]
    corner_radius = 24
    draw.rounded_rectangle(
        card_rect,
        radius=corner_radius,
        fill="#FFFFFF",
        outline="#D1D5DB",
        width=3
    )

    # コンテンツ描画
    for item in rendered_items:
        itype = item["type"]
        if itype == "separator":
            sep_y = item["y"]
            draw.line([(padding_x, sep_y), (card_width - padding_x, sep_y)], fill="#E5E7EB", width=2)
        else:
            x = padding_x + item.get("x_offset", 0)
            y = item["y"]
            draw.text((x, y), item["text"], font=item["font"], fill=item["color"])

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, "PNG", optimize=True)
    print(f"Generated Tokushoho image: {output_path} ({card_width}x{total_height})")

def main():
    is_ci = os.environ.get("GITHUB_ACTIONS") == "true" or os.environ.get("CI") == "true"
    text = os.environ.get("TOKUSHOHO_TEXT")

    if not text or not text.strip():
        if is_ci:
            print("Error: TOKUSHOHO_TEXT secret is not set or empty in CI environment.", file=sys.stderr)
            print("Please set the TOKUSHOHO_TEXT secret in GitHub repository settings.", file=sys.stderr)
            sys.exit(1)
        print("Note: TOKUSHOHO_TEXT environment variable is not set or empty. Using default template (local only).")
        text = DEFAULT_FALLBACK_TEXT

    repo_root = Path(__file__).resolve().parent.parent
    output_path = repo_root / "assets" / "images" / "tokushoho.png"
    generate_image(text, str(output_path))

if __name__ == "__main__":
    main()
