#!/usr/bin/env python3
"""
NHK追跡システム - ポータルページ生成
変更履歴、アーカイブ、レポートへの統合アクセス
"""
import sqlite3
from pathlib import Path
from datetime import datetime
import logging
import re
import feedparser
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def fetch_note_articles(rss_url: str, limit: int = 3) -> list:
    """noteのRSSフィードから最新記事を取得"""
    try:
        feed = feedparser.parse(rss_url)
        articles = []

        for entry in feed.entries[:limit]:
            article = {
                'title': entry.get('title', ''),
                'link': entry.get('link', ''),
                'published': entry.get('published', ''),
                'summary': entry.get('summary', ''),
                'ogp_image': None
            }

            # OGP画像を取得
            try:
                response = requests.get(article['link'], timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')

                # OGP画像を探す
                og_image = soup.find('meta', property='og:image')
                if og_image and og_image.get('content'):
                    article['ogp_image'] = og_image.get('content')

                # OGP説明文も取得
                og_description = soup.find('meta', property='og:description')
                if og_description and og_description.get('content'):
                    article['summary'] = og_description.get('content')

            except Exception as e:
                logger.warning(f"OGP取得失敗: {article['link']} - {e}")

            articles.append(article)

        return articles
    except Exception as e:
        logger.error(f"RSSフィード取得失敗: {e}")
        return []


def highlight_correction_notice(text: str) -> str:
    """
    ※から始まる文（訂正のおことわり）をハイライト

    Args:
        text: 元のテキスト

    Returns:
        ハイライトされたHTML
    """
    if not text:
        return text

    # ※から始まる文を検出
    # パターン1: ※から始まり「失礼しました」を含む場合（句点まで）
    # パターン2: それ以外は句点まで確実にマッチ
    # パターン3: 「失礼しました。」が独立している場合
    pattern = r'(※[^。]*?失礼しました[^。]*?。|※[^。]+。|失礼しました。)'

    def replace_func(match):
        notice = match.group(1)
        return f'<span class="correction-notice">{notice}</span>'

    return re.sub(pattern, replace_func, text)


def convert_to_full_url(source: str, link: str) -> str:
    """
    相対パスを完全なURLに変換

    Args:
        source: ソース名
        link: リンク（相対パスまたは完全URL）

    Returns:
        完全なURL
    """
    # すでに完全なURLの場合はそのまま返す
    if link.startswith('http://') or link.startswith('https://'):
        return link

    # ソースごとのベースURL
    base_urls = {
        'NHK首都圏ニュース': 'https://www3.nhk.or.jp/shutoken-news/',
        'NHK東海ニュース': 'https://www3.nhk.or.jp/tokai-news/',
        'NHK関西ニュース': 'https://www3.nhk.or.jp/kansai-news/',
        'NHK広島ニュース': 'https://www3.nhk.or.jp/hiroshima-news/',
        'NHK福岡ニュース': 'https://www3.nhk.or.jp/fukuoka-news/',
        'NHK札幌ニュース': 'https://www3.nhk.or.jp/sapporo-news/',
        'NHK東北ニュース': 'https://news.web.nhk/tohoku/',
        'NHKニュース': 'https://www3.nhk.or.jp/news/',
    }

    # ソースに対応するベースURLがある場合は結合
    if source in base_urls:
        return base_urls[source] + link

    # 不明なソースの場合はそのまま返す
    return link


def get_database_stats(db_path: str) -> dict:
    """データベース統計を取得"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    stats = {}

    # 総記事数
    cursor.execute('SELECT COUNT(*) FROM articles')
    stats['total_articles'] = cursor.fetchone()[0]

    # 総変更数
    cursor.execute('SELECT COUNT(*) FROM changes WHERE change_type != "new"')
    stats['total_changes'] = cursor.fetchone()[0]

    # タイトル変更数
    cursor.execute('SELECT COUNT(*) FROM changes WHERE change_type = "title_changed"')
    stats['title_changes'] = cursor.fetchone()[0]

    # 説明文変更数（追記を含む）
    cursor.execute('SELECT COUNT(*) FROM changes WHERE change_type IN ("description_changed", "description_added")')
    stats['description_changes'] = cursor.fetchone()[0]

    # 訂正記事数
    cursor.execute('SELECT COUNT(*) FROM articles WHERE has_correction = 1')
    stats['correction_articles'] = cursor.fetchone()[0]

    # ソース別統計
    cursor.execute('''
        SELECT source, COUNT(*) as count
        FROM articles
        GROUP BY source
        ORDER BY count DESC
    ''')
    stats['by_source'] = cursor.fetchall()

    # 最新の訂正記事（10件）- 訂正発生日時を正確に取得
    # パターン1: 記事公開後に訂正が追加された → changesテーブルのdetected_at
    # パターン2: 最初から訂正があった → first_seen
    cursor.execute('''
        SELECT
            a.source,
            a.link,
            a.title,
            a.description,
            a.correction_keywords,
            a.pub_date,
            a.first_seen,
            a.last_seen,
            MIN(CASE WHEN c.has_correction = 1 THEN c.detected_at ELSE NULL END) as correction_detected_at
        FROM articles a
        LEFT JOIN changes c ON a.link = c.link AND a.source = c.source
        WHERE a.has_correction = 1
        GROUP BY a.source, a.link
        ORDER BY COALESCE(MIN(CASE WHEN c.has_correction = 1 THEN c.detected_at ELSE NULL END), a.first_seen) DESC
        LIMIT 10
    ''')
    stats['recent_corrections'] = []
    for row in cursor.fetchall():
        source = row[0]
        link = row[1]
        full_url = convert_to_full_url(source, link)

        # 訂正発生日時: changesテーブルに記録があればそれを、なければfirst_seen
        correction_detected_at = row[8] if row[8] else row[6]  # correction_detected_at or first_seen

        stats['recent_corrections'].append({
            'source': source,
            'link': full_url,
            'change_type': 'correction',
            'old_value': None,
            'new_value': row[3],  # description
            'detected_at': correction_detected_at,  # 訂正発生日時
            'pub_date': row[5],  # 記事公開日時
            'first_seen': row[6],  # システム初回検出
            'title': row[2],
            'correction_keywords': row[4],
            'is_correction_added_later': row[8] is not None  # 後から訂正が追加されたか
        })

    # 最初の記録日時
    cursor.execute('SELECT MIN(first_seen) FROM articles')
    first_record = cursor.fetchone()[0]
    stats['first_record'] = first_record

    conn.close()
    return stats


def get_report_files(reports_dir: Path, limit: int = 5) -> list:
    """レポートファイル一覧を取得（最新5件のみ）"""
    reports = []

    # changes_*.html ファイルを取得
    for report_file in sorted(reports_dir.glob('changes_*.html'), reverse=True):
        # ファイル名から日時を抽出
        filename = report_file.name
        # changes_20251011_214114.html -> 20251011_214114
        timestamp_str = filename.replace('changes_', '').replace('.html', '')

        try:
            # 20251011_214114 -> 2025-10-11 21:41:14
            dt = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
            reports.append({
                'filename': filename,
                'timestamp': dt.strftime('%Y年%m月%d日 %H:%M:%S'),
                'relative_path': filename
            })

            # 最新5件のみ取得
            if len(reports) >= limit:
                break
        except ValueError:
            continue

    return reports


def get_latest_weekly_report(reports_dir: Path) -> str:
    """最新の週次レポートを取得"""
    weekly_dir = reports_dir / 'weekly'

    if not weekly_dir.exists():
        return ""

    # weekly_report_*.html ファイルを取得
    weekly_reports = sorted(weekly_dir.glob('weekly_report_*.html'), reverse=True)

    if not weekly_reports:
        return ""

    # 最新のレポートを読み込み
    latest_report = weekly_reports[0]

    try:
        with open(latest_report, 'r', encoding='utf-8') as f:
            content = f.read()

        # <div class="report-content">の中身を抽出
        match = re.search(r'<div class="report-content">(.*?)</div>\s*<p style="text-align: center', content, re.DOTALL)

        if match:
            return match.group(1).strip()
        else:
            return ""
    except Exception as e:
        logger.warning(f"週次レポート読み込み失敗: {e}")
        return ""


def generate_portal_html(db_path: str = 'data/articles.db',
                         reports_dir: str = 'reports',
                         output_path: str = 'reports/index.html'):
    """ポータルページを生成"""

    db_path = Path(db_path)
    reports_dir = Path(reports_dir)
    output_path = Path(output_path)

    # 統計取得
    stats = get_database_stats(str(db_path))

    # レポートファイル取得
    reports = get_report_files(reports_dir)

    # 週次レポート取得
    weekly_report_content = get_latest_weekly_report(reports_dir)

    # note記事を取得
    note_articles = fetch_note_articles('https://note.com/darkside_of_nhk/rss', limit=3)

    # 現在日時
    now = datetime.now()

    # HTML生成
    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NHK記事追跡システム - ポータル</title>

    <!-- Favicon -->
    <link rel="icon" type="image/x-icon" href="favicon.ico">
    <link rel="apple-touch-icon" href="apple-touch-icon.png">

    <!-- OGP (Open Graph Protocol) -->
    <meta property="og:title" content="NHKニュース変更追跡システム" />
    <meta property="og:description" content="NHK地方局ニュースの訂正・変更を自動検出。7つの地方局を監視し、記事の変更履歴を完全記録します。" />
    <meta property="og:image" content="https://nhk-news-tracker.netlify.app/ogp-image.png" />
    <meta property="og:url" content="https://nhk-news-tracker.netlify.app/" />
    <meta property="og:type" content="website" />
    <meta property="og:site_name" content="NHK記事追跡システム" />

    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:title" content="NHKニュース変更追跡システム" />
    <meta name="twitter:description" content="NHK地方局ニュースの訂正・変更を自動検出。7つの地方局を監視し、記事の変更履歴を完全記録します。" />
    <meta name="twitter:image" content="https://nhk-news-tracker.netlify.app/ogp-image.png" />

    <!-- Description -->
    <meta name="description" content="NHK地方局ニュースの訂正・変更を自動検出。首都圏・福岡・札幌・東海・広島・関西・東北の7地方局を監視し、記事の変更履歴を完全記録。訂正記事の自動検出機能付き。" />

    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Hiragino Sans', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 0;
            margin: 0;
            line-height: 1.4;
            padding-top: 60px; /* グローバルナビの高さ分 */
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 15px;
        }}

        /* グローバルナビゲーション */
        .global-nav {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: rgba(255, 255, 255, 0.98);
            backdrop-filter: blur(10px);
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            z-index: 1000;
            border-bottom: 2px solid #667eea;
        }}

        .global-nav-content {{
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 20px;
        }}

        .global-nav-logo {{
            font-size: 1.3em;
            font-weight: bold;
            color: #2d3748;
            text-decoration: none;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .global-nav-links {{
            display: flex;
            gap: 25px;
            align-items: center;
        }}

        .global-nav-link {{
            color: #4a5568;
            text-decoration: none;
            font-weight: 500;
            font-size: 0.95em;
            transition: color 0.2s;
            padding: 8px 12px;
            border-radius: 6px;
        }}

        .global-nav-link:hover {{
            color: #667eea;
            background: #f7fafc;
        }}

        .global-nav-link.active {{
            color: #667eea;
            background: #edf2f7;
        }}

        header {{
            background: white;
            padding: 25px 30px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            margin-bottom: 15px;
            text-align: center;
        }}

        h1 {{
            color: #2d3748;
            font-size: 2.2em;
            margin-bottom: 8px;
        }}

        .subtitle {{
            color: #718096;
            font-size: 1em;
            margin-bottom: 6px;
        }}

        .last-updated {{
            color: #a0aec0;
            font-size: 0.85em;
            margin-top: 6px;
        }}

        .main-nav {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 12px;
            margin-bottom: 15px;
        }}

        .nav-card {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 3px 10px rgba(0,0,0,0.08);
            transition: transform 0.2s, box-shadow 0.2s;
            text-decoration: none;
            color: inherit;
            display: block;
        }}

        .nav-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.15);
        }}

        .nav-card-icon {{
            font-size: 2.2em;
            margin-bottom: 8px;
        }}

        .nav-card-title {{
            font-size: 1.2em;
            font-weight: bold;
            color: #2d3748;
            margin-bottom: 6px;
        }}

        .nav-card-description {{
            color: #718096;
            font-size: 0.85em;
            line-height: 1.3;
        }}

        .nav-card-stat {{
            margin-top: 10px;
            padding-top: 10px;
            border-top: 2px solid #e2e8f0;
            font-size: 1.6em;
            font-weight: bold;
            color: #667eea;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 10px;
            margin-bottom: 15px;
        }}

        .stat-card {{
            background: white;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 3px 10px rgba(0,0,0,0.08);
            text-align: center;
        }}

        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 4px;
        }}

        .stat-label {{
            color: #718096;
            font-size: 0.85em;
        }}

        .section {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 15px;
            box-shadow: 0 3px 10px rgba(0,0,0,0.08);
        }}

        .section-title {{
            font-size: 1.5em;
            color: #2d3748;
            margin-bottom: 15px;
            padding-bottom: 8px;
            border-bottom: 2px solid #667eea;
        }}

        .source-list {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 10px;
            margin-top: 12px;
        }}

        .source-item {{
            background: #f7fafc;
            padding: 12px;
            border-radius: 6px;
            border-left: 3px solid #667eea;
        }}

        .source-name {{
            font-weight: bold;
            color: #2d3748;
            margin-bottom: 4px;
            font-size: 0.9em;
        }}

        .source-count {{
            color: #667eea;
            font-size: 1.1em;
            font-weight: bold;
        }}

        .recent-changes {{
            margin-top: 12px;
        }}

        .change-item {{
            background: #fff5f5;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 12px;
            border-left: 4px solid #dc2626;
        }}

        .correction-badge {{
            display: inline-block;
            background: #fee2e2;
            color: #991b1b;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.75em;
            font-weight: bold;
            margin-left: 8px;
        }}

        /* 訂正削除専用スタイル - 最も目立つように */
        .correction-removed-item {{
            background: #7f1d1d !important;
            border-left: 8px solid #dc2626 !important;
            border: 3px solid #dc2626;
            animation: pulse 2s ease-in-out infinite;
        }}

        @keyframes pulse {{
            0%, 100% {{
                box-shadow: 0 0 20px rgba(220, 38, 38, 0.5);
            }}
            50% {{
                box-shadow: 0 0 40px rgba(220, 38, 38, 0.8);
            }}
        }}

        .correction-removed-badge {{
            display: inline-block;
            background: #dc2626;
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 1em;
            font-weight: bold;
            margin-left: 8px;
            animation: blink 1.5s ease-in-out infinite;
        }}

        @keyframes blink {{
            0%, 100% {{
                opacity: 1;
            }}
            50% {{
                opacity: 0.6;
            }}
        }}

        .correction-removed-alert {{
            background: #dc2626;
            color: white;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
            font-size: 1em;
            font-weight: bold;
            text-align: center;
            border: 3px solid #991b1b;
            box-shadow: 0 4px 15px rgba(220, 38, 38, 0.4);
        }}

        .correction-removed-item .change-source,
        .correction-removed-item .change-title,
        .correction-removed-item .change-title a,
        .correction-removed-item .change-time {{
            color: white !important;
        }}

        .correction-removed-item .diff-old {{
            background: #fee2e2;
            border: 2px solid #ef4444;
            color: #7f1d1d;
            font-weight: bold;
        }}

        .change-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }}

        .change-type {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.75em;
            font-weight: bold;
            text-transform: uppercase;
        }}

        .type-title {{
            background: #fef3c7;
            color: #92400e;
        }}

        .type-description {{
            background: #fed7aa;
            color: #9a3412;
        }}

        .change-time {{
            color: #718096;
            font-size: 0.8em;
        }}

        .change-content {{
            margin-top: 8px;
        }}

        .change-source {{
            color: #4a5568;
            font-weight: bold;
            font-size: 0.85em;
            margin-bottom: 4px;
        }}

        .change-title {{
            color: #2d3748;
            font-size: 0.95em;
            margin-bottom: 6px;
            line-height: 1.3;
        }}

        .change-title a {{
            color: #2d3748;
            text-decoration: none;
            transition: color 0.2s;
        }}

        .change-title a:hover {{
            color: #667eea;
            text-decoration: underline;
        }}

        .change-diff {{
            font-size: 0.85em;
        }}

        .diff-old {{
            background: #fee;
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 6px;
            color: #c00;
            white-space: pre-wrap;
            word-wrap: break-word;
            line-height: 1.5;
        }}

        .diff-new {{
            background: #efe;
            padding: 10px;
            border-radius: 4px;
            color: #0a0;
            white-space: pre-wrap;
            word-wrap: break-word;
            line-height: 1.5;
        }}

        .correction-notice {{
            background: #ffeb3b;
            border-left: 3px solid #d32f2f;
            padding: 6px 10px;
            margin: 6px 0;
            display: inline-block;
            border-radius: 4px;
            font-weight: bold;
            color: #d32f2f;
        }}

        .reports-list {{
            margin-top: 20px;
            max-height: 500px;
            overflow-y: auto;
        }}

        .report-item {{
            background: #f7fafc;
            padding: 15px 20px;
            border-radius: 8px;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: background 0.2s;
        }}

        .report-item:hover {{
            background: #edf2f7;
        }}

        .report-link {{
            color: #667eea;
            text-decoration: none;
            font-weight: bold;
            flex: 1;
        }}

        .report-link:hover {{
            text-decoration: underline;
        }}

        .report-time {{
            color: #718096;
            font-size: 0.9em;
        }}

        .no-data {{
            text-align: center;
            padding: 40px;
            color: #718096;
            font-size: 1.1em;
        }}

        .about-section {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 15px;
            box-shadow: 0 3px 10px rgba(0,0,0,0.08);
            border-left: 4px solid #ef4444;
        }}

        .about-title {{
            font-size: 1.3em;
            color: #2d3748;
            margin-bottom: 10px;
            font-weight: bold;
        }}

        .about-content {{
            color: #4a5568;
            line-height: 1.5;
            font-size: 0.95em;
        }}

        .about-content p {{
            margin-bottom: 8px;
        }}

        .highlight-text {{
            background: #fef3c7;
            padding: 3px 6px;
            border-radius: 3px;
            font-weight: bold;
            color: #92400e;
            font-size: 1.05em;
        }}

        .note-articles-section {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 15px;
            box-shadow: 0 3px 10px rgba(0,0,0,0.08);
        }}

        .note-articles-title {{
            font-size: 1.3em;
            color: #2d3748;
            margin-bottom: 15px;
            font-weight: bold;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .note-articles-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 12px;
        }}

        .note-article-card {{
            border: 2px solid #e2e8f0;
            border-radius: 12px;
            overflow: hidden;
            transition: transform 0.2s, box-shadow 0.2s;
            background: white;
            text-decoration: none;
            color: inherit;
            display: block;
        }}

        .note-article-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.15);
            border-color: #667eea;
        }}

        .note-article-image {{
            width: 100%;
            aspect-ratio: 16 / 9;
            object-fit: cover;
            background: #f7fafc;
        }}

        .note-article-content {{
            padding: 15px;
        }}

        .note-article-title {{
            font-size: 1em;
            font-weight: bold;
            color: #2d3748;
            margin-bottom: 8px;
            line-height: 1.3;
        }}

        .note-article-summary {{
            color: #718096;
            font-size: 0.85em;
            line-height: 1.4;
            margin-bottom: 8px;
        }}

        .note-article-link {{
            color: #667eea;
            font-size: 0.8em;
            font-weight: bold;
        }}

        /* 週次レポート用スタイル */
        .weekly-report-section {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 15px;
            box-shadow: 0 3px 10px rgba(0,0,0,0.08);
        }}

        .weekly-report-section h1 {{
            color: #d32f2f;
            border-bottom: 3px solid #d32f2f;
            padding-bottom: 15px;
            margin-bottom: 30px;
            font-size: 2em;
        }}

        .weekly-report-section h2 {{
            color: #1976d2;
            margin-top: 40px;
            margin-bottom: 20px;
            font-size: 1.5em;
            border-left: 5px solid #1976d2;
            padding-left: 15px;
        }}

        .weekly-report-section h3 {{
            color: #424242;
            margin-top: 30px;
            margin-bottom: 15px;
            font-size: 1.3em;
            background: #f5f5f5;
            padding: 10px 15px;
            border-radius: 5px;
        }}

        .weekly-report-section h4 {{
            color: #616161;
            margin-top: 20px;
            margin-bottom: 10px;
            font-size: 1.1em;
        }}

        .weekly-report-section p {{
            margin-bottom: 15px;
            color: #424242;
        }}

        .weekly-report-section ul, .weekly-report-section ol {{
            margin-left: 25px;
            margin-bottom: 15px;
        }}

        .weekly-report-section li {{
            margin-bottom: 8px;
        }}

        .weekly-report-section hr {{
            border: none;
            border-top: 2px solid #e0e0e0;
            margin: 30px 0;
        }}

        .weekly-report-section strong {{
            color: #d32f2f;
            font-weight: bold;
        }}

        .weekly-report-section .abstract {{
            background: #fff3e0;
            padding: 20px;
            border-left: 5px solid #ff9800;
            margin: 20px 0;
            border-radius: 5px;
        }}

        .weekly-report-section .correction-item {{
            background: #fafafa;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            border-left: 4px solid #d32f2f;
        }}

        .weekly-report-section .problems, .weekly-report-section .recommendations {{
            background: #e3f2fd;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }}

        @media (max-width: 768px) {{
            .main-nav {{
                grid-template-columns: 1fr;
            }}

            .stats-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}

        /* アクセシビリティ - スクリーンリーダー用 */
        .visually-hidden {{
            position: absolute;
            width: 1px;
            height: 1px;
            padding: 0;
            margin: -1px;
            overflow: hidden;
            clip: rect(0, 0, 0, 0);
            border: 0;
        }}

        /* モバイルファースト対応（スマートフォン最適化） */
        @media (max-width: 480px) {{
            body {{
                padding-top: 55px;
            }}

            .global-nav-content {{
                padding: 10px 15px;
            }}

            .global-nav-logo {{
                font-size: 1.1em;
            }}

            .global-nav-links {{
                gap: 10px;
            }}

            .global-nav-link {{
                font-size: 0.85em;
                padding: 6px 8px;
            }}

            .correction-removed-alert {{
                font-size: 0.9rem;
                padding: 12px;
            }}

            /* タップしやすいリンクサイズ（iOS推奨44px） */
            .change-title a {{
                min-height: 44px;
                display: inline-block;
                padding: 8px 0;
            }}

            .diff-old, .diff-new {{
                font-size: 0.8rem;
                padding: 8px;
            }}

            .change-item {{
                padding: 12px;
            }}

            .stats-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
    </style>
</head>
<body>
    <!-- グローバルナビゲーション -->
    <nav class="global-nav">
        <div class="global-nav-content">
            <a href="index.html" class="global-nav-logo">📰 NHK記事追跡システム</a>
            <div class="global-nav-links">
                <a href="index.html" class="global-nav-link active">ポータル</a>
                <a href="history.html" class="global-nav-link">最近の変更</a>
                <a href="corrections.html" class="global-nav-link">おことわり</a>
                <a href="archive.html" class="global-nav-link">アーカイブ</a>
            </div>
        </div>
    </nav>

    <div class="container">
        <header>
            <h1>📰 NHK記事追跡システム</h1>
            <p class="subtitle">変更履歴・アーカイブ・レポート統合ポータル</p>
            <p class="last-updated">最終更新: {now.strftime('%Y年%m月%d日 %H:%M:%S')}</p>
        </header>

        <div class="about-section">
            <div class="about-title">🎯 このサイトの目的</div>
            <div class="about-content">
                <p><span class="highlight-text">NHKは頻繁に誤情報を発信しているが、その実態が知られていない！</span></p>
                <p>本システムは、NHK地方局ニュースの記事を24時間監視し、訂正・変更を自動検出することで、報道の透明性と正確性を可視化します。記事の変更履歴を完全に記録し、訂正記事を即座に発見することで、情報の信頼性を検証できる環境を提供します。</p>
            </div>
        </div>
"""

    # note記事セクション
    if note_articles:
        html += """
        <div class="note-articles-section">
            <div class="note-articles-title">📚 NHK問題の深掘り記事をチェック</div>
            <div class="note-articles-grid">
"""
        for article in note_articles:
            # 画像URLの処理
            image_url = article['ogp_image'] if article['ogp_image'] else 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="400" height="200"%3E%3Crect width="400" height="200" fill="%23f7fafc"/%3E%3Ctext x="50%25" y="50%25" dominant-baseline="middle" text-anchor="middle" fill="%23cbd5e0" font-size="20" font-family="sans-serif"%3ENo Image%3C/text%3E%3C/svg%3E'

            # 要約を短縮（150文字）
            summary = article['summary'][:150] + '...' if len(article['summary']) > 150 else article['summary']

            html += f"""
                <a href="{article['link']}" class="note-article-card" target="_blank">
                    <img src="{image_url}" alt="{article['title']}" class="note-article-image">
                    <div class="note-article-content">
                        <div class="note-article-title">{article['title']}</div>
                        <div class="note-article-summary">{summary}</div>
                        <div class="note-article-link">→ 続きを読む</div>
                    </div>
                </a>
"""

        html += """
            </div>
        </div>
"""

    html += f"""
        <div class="main-nav">
            <a href="history.html" class="nav-card">
                <div class="nav-card-icon">📚</div>
                <div class="nav-card-title">最近の変更</div>
                <div class="nav-card-description">全ての記事変更履歴を時系列で表示</div>
                <div class="nav-card-stat">{stats['total_changes']}件</div>
            </a>

            <a href="archive.html" class="nav-card">
                <div class="nav-card-icon">🗂️</div>
                <div class="nav-card-title">記事アーカイブ</div>
                <div class="nav-card-description">収集した全記事をソース別に表示</div>
                <div class="nav-card-stat">{stats['total_articles']}件</div>
            </a>

            <a href="{reports[0]['relative_path'] if reports else '#'}" class="nav-card">
                <div class="nav-card-icon">📊</div>
                <div class="nav-card-title">最新レポート</div>
                <div class="nav-card-description">直近の実行レポートを表示</div>
                <div class="nav-card-stat">{reports[0]['timestamp'] if reports else '未生成'}</div>
            </a>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{stats['total_articles']}</div>
                <div class="stat-label">総記事数</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats['total_changes']}</div>
                <div class="stat-label">総変更数</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats['title_changes']}</div>
                <div class="stat-label">タイトル変更</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats['description_changes']}</div>
                <div class="stat-label">説明文変更</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats['correction_articles']}</div>
                <div class="stat-label">訂正記事</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(stats['by_source'])}</div>
                <div class="stat-label">監視ソース</div>
            </div>
        </div>
"""

    # 🔴 最近の訂正セクション - 週次レポートより上に配置
    html += """
        <div class="section">
            <h2 class="section-title">🔴 最近の訂正（直近10件）</h2>
"""

    if stats['recent_corrections']:
        # articlesベースなので全て訂正記事
        html += """
            <div class="recent-changes">
"""

        # おことわりアイテムをレンダリング（全て訂正記事）
        for change in stats['recent_corrections']:
            # 訂正発生日時
            try:
                correction_dt = datetime.fromisoformat(change['detected_at'])
                correction_time_str = correction_dt.strftime('%Y年%m月%d日 %H:%M')
            except:
                correction_time_str = change['detected_at']

            # 記事公開日時
            pub_date_str = ''
            time_lag_str = ''
            try:
                pub_dt = datetime.fromisoformat(change['pub_date'])
                pub_date_str = pub_dt.strftime('%Y年%m月%d日 %H:%M')

                # タイムラグ計算
                if change.get('is_correction_added_later'):
                    correction_dt = datetime.fromisoformat(change['detected_at'])
                    time_diff = correction_dt - pub_dt

                    hours = int(time_diff.total_seconds() // 3600)
                    minutes = int((time_diff.total_seconds() % 3600) // 60)

                    if hours > 0:
                        time_lag_str = f'（公開から約{hours}時間{minutes}分後に訂正）'
                    else:
                        time_lag_str = f'（公開から約{minutes}分後に訂正）'
            except:
                pass

            # バッジ表示
            correction_keywords = change.get('correction_keywords', '')
            badge = f'<span class="correction-badge">🔴 おことわり: {correction_keywords}</span>' if correction_keywords else ''

            html += f"""                <div class="change-item">
                    <div class="change-header">
                        <span class="change-time">訂正検出: {correction_time_str}</span>
                    </div>
                    <div class="change-content">
                        <div class="change-source">{change['source']}</div>
                        <div class="change-title"><a href="{change['link']}" target="_blank">{change['title']}</a></div>
                        <div class="article-badges">{badge}</div>
"""

            # 記事公開日とタイムラグを表示
            if pub_date_str:
                html += f"""                        <div style="color: #718096; font-size: 0.85em; margin-top: 6px;">
                            記事公開: {pub_date_str} {time_lag_str}
                        </div>
"""

            # おことわり部分を抽出して表示（corrections.htmlと同じロジック）
            description = change.get('new_value', '')
            if description and ('※' in description or '失礼しました' in description):
                # corrections.htmlと同じextract_correction_summary関数を使用
                def extract_correction_summary(text, max_length=200):
                    """※や失礼しましたを含む文をすべて抽出（著作権対応）"""
                    if not text:
                        return ''

                    # 文を分割
                    sentences = text.replace('。', '。\n').split('\n')

                    # ※を含む文と「失礼しました」を含む文を抽出
                    correction_sentences = []
                    for sentence in sentences:
                        if '※' in sentence or '失礼しました' in sentence:
                            correction_sentences.append(sentence.strip())

                    if correction_sentences:
                        # 訂正文を結合
                        result = '\n'.join(correction_sentences)

                        # 長すぎる場合は各文を短縮
                        if len(result) > max_length:
                            shortened = []
                            for sent in correction_sentences:
                                if '失礼しました' in sent:
                                    # 訂正のおことわり文は全文表示
                                    shortened.append(sent)
                                elif '※' in sent:
                                    # ※を含む文は前後を含めて表示
                                    idx = sent.find('※')
                                    start = max(0, idx - 30)
                                    end = min(len(sent), idx + 50)
                                    excerpt = sent[start:end]
                                    if start > 0:
                                        excerpt = '...' + excerpt
                                    if end < len(sent):
                                        excerpt = excerpt + '...'
                                    shortened.append(excerpt)
                            result = '\n'.join(shortened)

                        return result
                    else:
                        # 訂正マーカーがない場合は先頭から
                        if len(text) > max_length:
                            return text[:max_length] + '...'
                        return text

                correction_summary = extract_correction_summary(description, 200)
                highlighted_correction = highlight_correction_notice(correction_summary)

                html += f"""                        <div class="change-diff">
                            <div class="diff-new">【引用】おことわり部分:\n{highlighted_correction}</div>
                            <div style="margin-top: 10px; text-align: right;">
                                <a href="{change['link']}" target="_blank" style="color: #667eea; text-decoration: none; font-weight: bold;">→ 元記事を読む（NHK）</a>
                            </div>
                        </div>
"""

            html += """                    </div>
                </div>
"""

        # Close section
        html += """            </div>
"""
    else:
        html += """                <div class="no-data">訂正記事がありません</div>
"""

    html += """        </div>
"""

    # 週次レポートセクション
    if weekly_report_content:
        html += f"""
        <div class="weekly-report-section">
            <h2 class="section-title">📊 今週の誤情報レポート</h2>
            <div class="report-content">
                {weekly_report_content}
            </div>
        </div>
"""

    # ソース別記事数セクション
    html += """
        <div class="section">
            <h2 class="section-title">📍 ソース別記事数</h2>
            <div class="source-list">
"""
    for source, count in stats['by_source']:
        html += f"""                <div class="source-item">
                    <div class="source-name">{source}</div>
                    <div class="source-count">{count}件</div>
                </div>
"""
    html += """            </div>
        </div>

        <div class="section">
            <h2 class="section-title">📋 直近のリサーチ結果</h2>
            <div class="reports-list">
"""

    if reports:
        for report in reports:
            html += f"""                <div class="report-item">
                    <a href="{report['relative_path']}" class="report-link">{report['timestamp']}</a>
                    <span class="report-time">📄</span>
                </div>
"""
    else:
        html += """                <div class="no-data">レポートがありません</div>
"""

    # システム情報
    if stats['first_record']:
        try:
            first_dt = datetime.fromisoformat(stats['first_record'])
            first_record_str = first_dt.strftime('%Y年%m月%d日 %H:%M:%S')
        except:
            first_record_str = stats['first_record']
    else:
        first_record_str = '不明'

    html += f"""            </div>
        </div>

        <div class="section">
            <h2 class="section-title">ℹ️ システム情報</h2>
            <div style="color: #4a5568; line-height: 2;">
                <p><strong>監視開始日時:</strong> {first_record_str}</p>
                <p><strong>総記事数:</strong> {stats['total_articles']}件</p>
                <p><strong>総変更数:</strong> {stats['total_changes']}件</p>
                <p><strong>訂正記事:</strong> {stats['correction_articles']}件</p>
            </div>
        </div>
    </div>

    <!-- NHKアクセストラッキング -->
    <script>
    (function() {{
        try {{
            var path = window.location.pathname + window.location.search;
            var referer = document.referrer || 'Direct';

            // トラッキング関数を呼び出し
            fetch('/.netlify/functions/track-access?path=' + encodeURIComponent(path), {{
                method: 'GET',
                headers: {{
                    'Content-Type': 'application/json'
                }}
            }}).catch(function(err) {{
                // エラーは無視（トラッキング失敗しても動作継続）
                console.log('Tracking skipped:', err);
            }});
        }} catch(e) {{
            console.log('Tracking error:', e);
        }}
    }})();
    </script>
</body>
</html>
"""

    # ファイル書き込み
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    logger.info(f"ポータルページ生成完了: {output_path}")
    print(f"✅ ポータルページを生成しました: {output_path.absolute()}")


def main():
    """メイン実行"""
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("NHK記事追跡システム - ポータルページ生成")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    generate_portal_html()

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("✅ 完了: reports/index.html")
    print("")
    print("次のコマンドで開きます:")
    print("  open reports/index.html")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


if __name__ == '__main__':
    main()
