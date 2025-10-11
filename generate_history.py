#!/usr/bin/env python3
"""
NHK RSS変更履歴ビューアー
全変更履歴をdiffスタイルで表示
"""

import sqlite3
import difflib
from datetime import datetime
from pathlib import Path

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent

# ソース名からベースURLへのマッピング
SOURCE_BASE_URLS = {
    'NHK首都圏ニュース': 'https://www.nhk.or.jp/shutoken-news/',
    'NHK福岡ニュース': 'https://www.nhk.or.jp/fukuoka-news/',
    'NHK札幌ニュース': 'https://www.nhk.or.jp/sapporo-news/',
    'NHK東海ニュース': 'https://www.nhk.or.jp/tokai-news/',
    'NHK広島ニュース': 'https://www.nhk.or.jp/hiroshima-news/',
    'NHK関西ニュース': 'https://www.nhk.or.jp/kansai-news/',
    'NHK東北ニュース': 'https://news.web.nhk/tohoku-news/',
}

def get_full_url(source, relative_path):
    """ソース名と相対パスから完全URLを生成"""
    base_url = SOURCE_BASE_URLS.get(source, '')
    if base_url:
        return base_url + relative_path
    return relative_path  # フォールバック

def get_all_changes(db_path, limit=None):
    """全変更履歴を取得（新しい順）"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = """
    WITH change_timeline AS (
        SELECT
            c.*,
            a.title as current_title,
            a.description as current_description,
            a.first_seen,
            LAG(c.detected_at) OVER (PARTITION BY c.link ORDER BY c.detected_at) as previous_check_time
        FROM changes c
        LEFT JOIN articles a ON c.link = a.link
        WHERE c.change_type IN ('title_changed', 'description_changed', 'correction_removed')
    )
    SELECT
        *,
        COALESCE(previous_check_time, first_seen) as before_change_time,
        detected_at as after_change_time
    FROM change_timeline
    ORDER BY detected_at DESC
    """

    if limit:
        query += f" LIMIT {limit}"

    cursor.execute(query)
    changes = cursor.fetchall()
    conn.close()

    return changes

def generate_diff_html(old_text, new_text):
    """テキストの差分をHTML形式で生成"""
    if not old_text:
        old_text = ""
    if not new_text:
        new_text = ""

    # 行ごとに分割
    old_lines = old_text.splitlines()
    new_lines = new_text.splitlines()

    # diffを生成
    differ = difflib.Differ()
    diff = list(differ.compare(old_lines, new_lines))

    html_parts = []
    html_parts.append('<div class="diff-container">')

    for line in diff:
        if line.startswith('- '):
            # 削除された行（赤）
            html_parts.append(f'<div class="diff-line deleted">{line[2:]}</div>')
        elif line.startswith('+ '):
            # 追加された行（緑）
            html_parts.append(f'<div class="diff-line added">{line[2:]}</div>')
        elif line.startswith('  '):
            # 変更なし（グレー）
            html_parts.append(f'<div class="diff-line unchanged">{line[2:]}</div>')

    html_parts.append('</div>')
    return '\n'.join(html_parts)

def generate_inline_diff_html(old_text, new_text):
    """インライン形式の差分（文字単位）"""
    if not old_text:
        old_text = ""
    if not new_text:
        new_text = ""

    html_parts = []
    html_parts.append('<div class="inline-diff">')

    # 削除部分
    if old_text:
        html_parts.append('<div class="diff-old">')
        html_parts.append('<span class="label">変更前:</span> ')
        html_parts.append(f'<span class="text">{old_text}</span>')
        html_parts.append('</div>')

    # 追加部分
    if new_text:
        html_parts.append('<div class="diff-new">')
        html_parts.append('<span class="label">変更後:</span> ')
        html_parts.append(f'<span class="text">{new_text}</span>')
        html_parts.append('</div>')

    html_parts.append('</div>')
    return '\n'.join(html_parts)

def generate_html(changes, output_path):
    """HTMLファイルを生成"""

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NHK記事変更履歴 - 全履歴</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Hiragino Sans', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            line-height: 1.6;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        header {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
            text-align: center;
        }}

        h1 {{
            color: #2d3748;
            font-size: 2.5em;
            margin-bottom: 10px;
        }}

        .subtitle {{
            color: #718096;
            font-size: 1.1em;
        }}

        .stats {{
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-top: 20px;
        }}

        .stat-item {{
            text-align: center;
        }}

        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}

        .stat-label {{
            color: #718096;
            font-size: 0.9em;
        }}

        .change-card {{
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }}

        .change-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.15);
        }}

        .change-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 15px;
            padding-bottom: 15px;
            border-bottom: 2px solid #e2e8f0;
        }}

        .change-type {{
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.85em;
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

        .type-correction {{
            background: #fecaca;
            color: #991b1b;
        }}

        .change-time {{
            color: #718096;
            font-size: 0.85em;
            text-align: right;
        }}

        .change-time div {{
            margin: 2px 0;
        }}

        .change-source {{
            color: #4a5568;
            font-weight: bold;
            margin-bottom: 10px;
        }}

        .change-link {{
            color: #667eea;
            text-decoration: none;
            font-size: 0.9em;
            word-break: break-all;
        }}

        .change-link:hover {{
            text-decoration: underline;
        }}

        .inline-diff {{
            margin: 20px 0;
        }}

        .diff-old, .diff-new {{
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        }}

        .diff-old {{
            background: #fee;
            border-left: 4px solid #f00;
        }}

        .diff-new {{
            background: #efe;
            border-left: 4px solid #0a0;
        }}

        .label {{
            font-weight: bold;
            margin-right: 10px;
        }}

        .diff-old .label {{
            color: #c00;
        }}

        .diff-new .label {{
            color: #0a0;
        }}

        .text {{
            color: #2d3748;
        }}

        .diff-container {{
            background: #1e1e1e;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            font-family: 'Monaco', 'Courier New', monospace;
            font-size: 0.9em;
            overflow-x: auto;
        }}

        .diff-line {{
            padding: 2px 10px;
            white-space: pre-wrap;
            word-break: break-all;
        }}

        .diff-line.deleted {{
            background: #4d1f1f;
            color: #ff9999;
        }}

        .diff-line.added {{
            background: #1f4d1f;
            color: #99ff99;
        }}

        .diff-line.unchanged {{
            color: #999;
        }}

        .no-changes {{
            text-align: center;
            padding: 60px;
            color: #718096;
            font-size: 1.2em;
        }}

        .correction-keywords {{
            background: #fef3c7;
            padding: 10px 15px;
            border-radius: 8px;
            margin: 10px 0;
            color: #92400e;
        }}

        .filter-bar {{
            background: white;
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}

        .filter-buttons {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }}

        .filter-btn {{
            padding: 10px 20px;
            border: 2px solid #e2e8f0;
            background: white;
            border-radius: 20px;
            cursor: pointer;
            transition: all 0.2s;
            font-weight: bold;
        }}

        .filter-btn:hover {{
            background: #f7fafc;
        }}

        .filter-btn.active {{
            background: #667eea;
            color: white;
            border-color: #667eea;
        }}

        .nav-links {{
            background: white;
            padding: 15px;
            border-radius: 15px;
            margin-bottom: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            display: flex;
            gap: 12px;
            justify-content: center;
            flex-wrap: wrap;
        }}

        .nav-link {{
            padding: 10px 20px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 8px;
            font-weight: bold;
            transition: background-color 0.2s;
        }}

        .nav-link:hover {{
            background: #5568d3;
        }}

        .nav-link.secondary {{
            background: #48bb78;
        }}

        .nav-link.secondary:hover {{
            background: #38a169;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📰 NHK記事変更履歴</h1>
            <p class="subtitle">全ての変更を新しい順に表示</p>
            <div class="stats">
                <div class="stat-item">
                    <div class="stat-number">{len(changes)}</div>
                    <div class="stat-label">総変更数</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">{len([c for c in changes if c['change_type'] == 'title_changed'])}</div>
                    <div class="stat-label">タイトル変更</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">{len([c for c in changes if c['change_type'] == 'description_changed'])}</div>
                    <div class="stat-label">説明文変更</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">{len([c for c in changes if c['has_correction']])}</div>
                    <div class="stat-label">訂正関連</div>
                </div>
            </div>
        </header>

        <div class="nav-links">
            <a href="archive.html" class="nav-link secondary">🗂️ 全記事アーカイブ</a>
        </div>

        <div class="filter-bar">
            <div class="filter-buttons">
                <button class="filter-btn active" onclick="filterChanges('all')">すべて</button>
                <button class="filter-btn" onclick="filterChanges('title')">タイトル変更</button>
                <button class="filter-btn" onclick="filterChanges('description')">説明文変更</button>
                <button class="filter-btn" onclick="filterChanges('correction')">訂正関連</button>
            </div>
        </div>
"""

    if not changes:
        html += """
        <div class="change-card">
            <div class="no-changes">
                まだ変更が記録されていません。<br>
                システムが1時間ごとに自動でチェックしています。
            </div>
        </div>
"""
    else:
        for change in changes:
            change_type_class = {
                'title_changed': 'type-title',
                'description_changed': 'type-description',
                'correction_removed': 'type-correction'
            }.get(change['change_type'], 'type-title')

            change_type_label = {
                'title_changed': 'タイトル変更',
                'description_changed': '説明文変更',
                'correction_removed': '訂正削除'
            }.get(change['change_type'], change['change_type'])

            detected_at = datetime.fromisoformat(change['detected_at'])
            time_str = detected_at.strftime('%Y年%m月%d日 %H:%M:%S')

            # 変更前後の確認日時
            before_time = datetime.fromisoformat(change['before_change_time'])
            after_time = datetime.fromisoformat(change['after_change_time'])
            before_time_str = before_time.strftime('%Y年%m月%d日 %H:%M:%S')
            after_time_str = after_time.strftime('%Y年%m月%d日 %H:%M:%S')

            data_filter = []
            data_filter.append(change['change_type'].split('_')[0])
            if change['has_correction']:
                data_filter.append('correction')

            # 完全URLを生成
            full_url = get_full_url(change['source'], change['link'])

            html += f"""
        <div class="change-card" data-filter="{' '.join(data_filter)}">
            <div class="change-header">
                <div>
                    <span class="change-type {change_type_class}">{change_type_label}</span>
                    {f'<span class="change-type type-correction">訂正あり</span>' if change['has_correction'] else ''}
                </div>
                <div class="change-time">
                    <div>🕐 変更前確認: {before_time_str}</div>
                    <div>🕐 変更後確認: {after_time_str}</div>
                </div>
            </div>

            <div class="change-source">{change['source']}</div>
            <a href="{full_url}" class="change-link" target="_blank">{full_url}</a>

            {f'<div class="correction-keywords">🔴 訂正キーワード: {change["correction_keywords"]}</div>' if change['correction_keywords'] else ''}

            {generate_inline_diff_html(change['old_value'], change['new_value'])}
        </div>
"""

    html += """
    </div>

    <script>
        function filterChanges(type) {
            // ボタンのアクティブ状態を更新
            document.querySelectorAll('.filter-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            event.target.classList.add('active');

            // カードをフィルタリング
            const cards = document.querySelectorAll('.change-card');
            cards.forEach(card => {
                if (type === 'all') {
                    card.style.display = 'block';
                } else {
                    const filters = card.getAttribute('data-filter');
                    if (filters && filters.includes(type)) {
                        card.style.display = 'block';
                    } else {
                        card.style.display = 'none';
                    }
                }
            });
        }
    </script>
</body>
</html>
"""

    # HTMLファイルを書き込み
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✅ 変更履歴HTMLを生成しました: {output_path}")
    print(f"📊 総変更数: {len(changes)}件")

def main():
    """メイン処理"""
    db_path = PROJECT_ROOT / 'data' / 'articles.db'
    output_path = PROJECT_ROOT / 'reports' / 'history.html'

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("NHK記事変更履歴ビューアー")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()

    # データベースから変更履歴を取得
    print("📖 データベースから変更履歴を取得中...")
    changes = get_all_changes(db_path)

    print(f"✅ {len(changes)}件の変更を取得しました")
    print()

    # HTMLを生成
    print("🎨 HTMLレポートを生成中...")
    generate_html(changes, output_path)

    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"✅ 完了: {output_path}")
    print()
    print("次のコマンドで開きます:")
    print(f"  open {output_path}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

if __name__ == '__main__':
    main()
