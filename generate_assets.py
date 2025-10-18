#!/usr/bin/env python3
"""
アイコンとOGP画像を生成
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
REPORTS_DIR = PROJECT_ROOT / 'reports'

def create_favicon():
    """ファビコンを作成 (32x32, 180x180)"""

    # 32x32 favicon
    img = Image.new('RGB', (32, 32), color='#4facfe')
    draw = ImageDraw.Draw(img)

    # 📰 ニュースアイコン風のデザイン
    # 白い紙
    draw.rectangle([6, 4, 26, 28], fill='white')

    # 見出し（青いバー）
    draw.rectangle([8, 7, 24, 10], fill='#1976d2')

    # テキスト行（グレー）
    draw.rectangle([8, 13, 24, 14], fill='#999')
    draw.rectangle([8, 16, 20, 17], fill='#999')
    draw.rectangle([8, 19, 24, 20], fill='#999')
    draw.rectangle([8, 22, 18, 23], fill='#999')

    # 変更マーク（赤い点）
    draw.ellipse([22, 22, 26, 26], fill='#d32f2f')

    img.save(REPORTS_DIR / 'favicon.ico', format='ICO', sizes=[(32, 32)])
    print(f"✅ ファビコンを作成: {REPORTS_DIR / 'favicon.ico'}")

    # 180x180 Apple touch icon
    img_large = Image.new('RGB', (180, 180), color='#4facfe')
    draw_large = ImageDraw.Draw(img_large)

    # 白い紙（角丸風）
    draw_large.rounded_rectangle([20, 20, 160, 160], radius=10, fill='white')

    # 見出し（青いバー）
    draw_large.rounded_rectangle([35, 40, 145, 60], radius=5, fill='#1976d2')

    # テキスト行
    for y in [75, 90, 105, 120]:
        width = 110 if y != 120 else 80
        draw_large.rounded_rectangle([35, y, 35 + width, y + 8], radius=3, fill='#e0e0e0')

    # 変更マーク（赤い円）
    draw_large.ellipse([130, 125, 150, 145], fill='#d32f2f')
    draw_large.ellipse([135, 130, 145, 140], fill='white')

    img_large.save(REPORTS_DIR / 'apple-touch-icon.png', format='PNG')
    print(f"✅ Apple touch iconを作成: {REPORTS_DIR / 'apple-touch-icon.png'}")

def create_ogp_image():
    """OGP画像を作成 (1200x630) - 4:3セーフエリア対応、モダンなデザイン"""

    img = Image.new('RGB', (1200, 630), color='#ffffff')
    draw = ImageDraw.Draw(img)

    # より洗練されたグラデーション背景（ダークブルーから紫へ）
    for y in range(630):
        ratio = y / 630
        # 上部: #1e3a8a（ダークブルー） → 下部: #7c3aed（紫）
        r = int(30 + (124 - 30) * ratio)
        g = int(58 + (58 - 58) * ratio)
        b = int(138 + (237 - 138) * ratio)
        draw.rectangle([0, y, 1200, y+1], fill=(r, g, b))

    # タイトル用のフォント（4:3セーフエリア対応）
    try:
        title_font = ImageFont.truetype('/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc', 80)
        subtitle_font = ImageFont.truetype('/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc', 42)
        desc_font = ImageFont.truetype('/System/Library/Fonts/ヒラギノ角ゴシック W4.ttc', 32)
        small_font = ImageFont.truetype('/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc', 28)
    except:
        try:
            title_font = ImageFont.truetype('/System/Library/Fonts/Hiragino Sans GB.ttc', 80)
            subtitle_font = ImageFont.truetype('/System/Library/Fonts/Hiragino Sans GB.ttc', 42)
            desc_font = ImageFont.truetype('/System/Library/Fonts/Hiragino Sans GB.ttc', 32)
            small_font = ImageFont.truetype('/System/Library/Fonts/Hiragino Sans GB.ttc', 28)
        except:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
            desc_font = ImageFont.load_default()
            small_font = ImageFont.load_default()

    # 上部装飾バー（アクセントカラー）
    draw.rectangle([0, 0, 1200, 8], fill='#f59e0b')

    # メインタイトル（中央、大きく、白文字）
    title_text = "NHK記事追跡システム"
    # タイトルの幅を計算して中央揃え
    try:
        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
    except:
        title_width = len(title_text) * 46  # フォールバック

    title_x = (1200 - title_width) // 2
    title_y = 110

    # タイトルに影を追加（立体感）
    draw.text((title_x + 3, title_y + 3), title_text, fill='#1e293b', font=title_font)
    draw.text((title_x, title_y), title_text, fill='#ffffff', font=title_font)

    # サブタイトル（中央揃え、黄色でアクセント）
    subtitle_text = "報道の透明性を可視化"
    try:
        subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
        subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
    except:
        subtitle_width = len(subtitle_text) * 26

    subtitle_x = (1200 - subtitle_width) // 2
    subtitle_y = title_y + 115
    draw.text((subtitle_x, subtitle_y), subtitle_text, fill='#fbbf24', font=subtitle_font)

    # 装飾ライン（少し短く）
    line_y = subtitle_y + 65
    line_width = 350
    line_x = (1200 - line_width) // 2
    draw.rectangle([line_x, line_y, line_x + line_width, line_y + 4], fill='#fbbf24')

    # 3つの特徴（横並び、4:3セーフエリア内に配置）
    # 4:3範囲: 中央840px (左端180px～右端1020px)
    features = [
        ("地方局", "24時間監視", "#60a5fa"),
        ("訂正記事", "即座に検出", "#f87171"),
        ("変更履歴", "完全記録", "#34d399")
    ]

    feature_y = line_y + 38
    # セーフエリア内に均等配置
    safe_area_width = 840  # 4:3セーフエリア幅
    safe_area_start = (1200 - safe_area_width) // 2  # 180px
    card_width = 250  # カード幅を調整
    card_spacing = safe_area_width // 3  # 280px間隔
    start_x = safe_area_start + (card_spacing - card_width) // 2  # 中央寄せ

    for i, (title, desc, color) in enumerate(features):
        x = start_x + i * card_spacing

        # 背景カード（グラスモーフィズム風）
        card_height = 110
        draw.rounded_rectangle(
            [x, feature_y, x + card_width, feature_y + card_height],
            radius=16,
            fill=(255, 255, 255, 50)
        )

        # カラーアクセント（上部バー）
        draw.rounded_rectangle(
            [x, feature_y, x + card_width, feature_y + 6],
            radius=16,
            fill=color
        )

        # タイトル（大きく、濃い色、文字間隔調整）
        title_y_pos = feature_y + 30
        try:
            title_bbox = draw.textbbox((0, 0), title, font=subtitle_font)
            title_text_width = title_bbox[2] - title_bbox[0]
        except:
            title_text_width = len(title) * 22

        title_x = x + (card_width - title_text_width) // 2
        draw.text((title_x, title_y_pos), title, fill='#1e293b', font=subtitle_font)

        # 説明（小さく、グレー）
        desc_y = feature_y + 70
        try:
            desc_bbox = draw.textbbox((0, 0), desc, font=desc_font)
            desc_width = desc_bbox[2] - desc_bbox[0]
        except:
            desc_width = len(desc) * 16

        desc_x = x + (card_width - desc_width) // 2
        draw.text((desc_x, desc_y), desc, fill='#64748b', font=desc_font)

    # 下部にURL（中央、控えめに）
    url_text = "nhk-news-tracker.netlify.app"
    try:
        url_bbox = draw.textbbox((0, 0), url_text, font=small_font)
        url_width = url_bbox[2] - url_bbox[0]
    except:
        url_width = len(url_text) * 15

    url_x = (1200 - url_width) // 2
    draw.text((url_x, 570), url_text, fill='#cbd5e1', font=small_font)

    img.save(REPORTS_DIR / 'ogp-image.png', format='PNG', quality=95)
    print(f"✅ OGP画像を作成: {REPORTS_DIR / 'ogp-image.png'}")

def main():
    """メイン処理"""
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("アイコン・OGP画像生成")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()

    # reportsディレクトリが存在するか確認
    REPORTS_DIR.mkdir(exist_ok=True)

    print("🎨 アイコンを生成中...")
    create_favicon()
    print()

    print("🎨 OGP画像を生成中...")
    create_ogp_image()
    print()

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("✅ 完了")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

if __name__ == '__main__':
    main()
