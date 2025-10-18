#!/usr/bin/env python3
"""
NHKおことわり記事ビューアー
訂正・おことわり記事のみを表示（削除されたものも含む）
"""

import sqlite3
import re
from datetime import datetime
from pathlib import Path

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent

def highlight_correction_notice(text: str) -> str:
    """※から始まる文（訂正のおことわり）をハイライト"""
    if not text:
        return text

    # ※から始まる文を検出
    pattern = r'(※[^※]*?失礼しました[^\n]*?。|※[^。\n]+[。\n]?)'

    def replace_func(match):
        notice = match.group(1)
        return f'<span class="correction-notice">{notice}</span>'

    return re.sub(pattern, replace_func, text)

def extract_correction_summary(text, max_length=150):
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

# ソース名からベースURLへのマッピング
SOURCE_BASE_URLS = {
    'NHK首都圏ニュース': 'https://www3.nhk.or.jp/shutoken-news/',
    'NHK福岡ニュース': 'https://www3.nhk.or.jp/fukuoka-news/',
    'NHK札幌ニュース': 'https://www3.nhk.or.jp/sapporo-news/',
    'NHK東海ニュース': 'https://www3.nhk.or.jp/tokai-news/',
    'NHK広島ニュース': 'https://www3.nhk.or.jp/hiroshima-news/',
    'NHK関西ニュース': 'https://www3.nhk.or.jp/kansai-news/',
    'NHK東北ニュース': 'https://news.web.nhk/tohoku-news/',
    'NHK ONE検索': '',  # 完全URLで保存されているため、ベースURLは不要
}

def get_full_url(source, relative_path):
    """ソース名と相対パスから完全URLを生成"""
    # 既に完全URLの場合はそのまま返す
    if relative_path.startswith('http://') or relative_path.startswith('https://'):
        return relative_path

    # NHK東北ニュースの特別処理（Selenium経由で取得した記事）
    if source == 'NHK東北ニュース':
        # 20251009/6000033450.html から 6000033450 を抽出
        match = re.search(r'(\d+)\.html$', relative_path)
        if match:
            article_id = match.group(1)
            return f'https://news.web.nhk/newsweb/na/nb-{article_id}'

    # 通常のベースURL結合
    base_url = SOURCE_BASE_URLS.get(source, '')
    if base_url:
        return base_url + relative_path
    return relative_path

def get_correction_articles(db_path, limit=None):
    """おことわり記事のみを取得（新しい順）"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = """
    SELECT
        *,
        (SELECT COUNT(*) FROM changes WHERE changes.link = articles.link) as change_count
    FROM articles
    WHERE has_correction = 1
    ORDER BY last_seen DESC
    """

    if limit:
        query += f" LIMIT {limit}"

    cursor.execute(query)
    articles = cursor.fetchall()
    conn.close()

    return articles

def get_correction_stats(db_path):
    """おことわり記事のソース別統計を取得"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        source,
        COUNT(*) as count,
        MIN(first_seen) as oldest,
        MAX(last_seen) as newest
    FROM articles
    WHERE has_correction = 1
    GROUP BY source
    ORDER BY source
    """)

    stats = cursor.fetchall()
    conn.close()

    return stats

def generate_html(articles, stats, output_path):
    """HTMLファイルを生成"""

    # 全ソースのリスト
    all_sources = sorted(SOURCE_BASE_URLS.keys())

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NHKおことわり記事一覧 - 訂正記事</title>

    <!-- Favicon -->
    <link rel="icon" type="image/x-icon" href="favicon.ico">
    <link rel="apple-touch-icon" href="apple-touch-icon.png">

    <!-- OGP (Open Graph Protocol) -->
    <meta property="og:title" content="NHKおことわり記事一覧 - 訂正記事" />
    <meta property="og:description" content="NHK地方局ニュースの訂正・おことわり記事を一覧表示。削除されたものも含めて追跡。" />
    <meta property="og:image" content="https://nhk-news-tracker.netlify.app/ogp-image.png" />
    <meta property="og:url" content="https://nhk-news-tracker.netlify.app/corrections.html" />
    <meta property="og:type" content="website" />

    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:title" content="NHKおことわり記事一覧 - 訂正記事" />
    <meta name="twitter:description" content="NHK地方局ニュースの訂正・おことわり記事を一覧表示。削除されたものも含めて追跡。" />
    <meta name="twitter:image" content="https://nhk-news-tracker.netlify.app/ogp-image.png" />

    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Hiragino Sans', sans-serif;
            background: linear-gradient(135deg, #fc4a1a 0%, #f7b733 100%);
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
            flex-wrap: wrap;
        }}

        .stat-item {{
            text-align: center;
        }}

        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            color: #fc4a1a;
        }}

        .stat-label {{
            color: #718096;
            font-size: 0.9em;
        }}

        .filter-bar {{
            background: white;
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}

        .filter-section {{
            margin-bottom: 15px;
        }}

        .filter-label {{
            font-weight: bold;
            color: #2d3748;
            margin-bottom: 8px;
            display: block;
        }}

        .search-box {{
            width: 100%;
            padding: 12px 20px;
            border: 2px solid #e2e8f0;
            border-radius: 10px;
            font-size: 1em;
            transition: border-color 0.2s;
        }}

        .search-box:focus {{
            outline: none;
            border-color: #fc4a1a;
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
            font-size: 0.9em;
        }}

        .filter-btn:hover {{
            background: #f7fafc;
        }}

        .filter-btn.active {{
            background: #fc4a1a;
            color: white;
            border-color: #fc4a1a;
        }}

        .article-card {{
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
            border-left: 5px solid #fc4a1a;
        }}

        .article-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.15);
        }}

        .article-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 12px;
            padding-bottom: 12px;
            border-bottom: 2px solid #e2e8f0;
        }}

        .article-source {{
            display: inline-block;
            padding: 6px 14px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.8em;
            background: #fee2e2;
            color: #991b1b;
        }}

        .article-meta {{
            text-align: right;
            font-size: 0.8em;
            color: #718096;
        }}

        .article-title {{
            font-size: 1.3em;
            font-weight: bold;
            color: #2d3748;
            margin-bottom: 12px;
            line-height: 1.4;
        }}

        .article-link {{
            color: #fc4a1a;
            text-decoration: none;
            font-size: 0.85em;
            word-break: break-all;
            display: inline-block;
            margin-bottom: 10px;
        }}

        .article-link:hover {{
            text-decoration: underline;
        }}

        .article-badges {{
            margin-top: 12px;
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }}

        .badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.75em;
            font-weight: bold;
        }}

        .badge-correction {{
            background: #fecaca;
            color: #991b1b;
        }}

        .correction-notice {{
            background: #ffeb3b;
            border-left: 4px solid #d32f2f;
            padding: 8px 12px;
            margin: 8px 0;
            display: inline-block;
            border-radius: 4px;
            font-weight: bold;
            color: #d32f2f;
        }}

        .change-diff {{
            margin-top: 15px;
            font-size: 0.9em;
        }}

        .diff-new {{
            background: #fffbeb;
            padding: 12px;
            border-radius: 4px;
            border: 2px solid #f59e0b;
            white-space: pre-wrap;
            word-wrap: break-word;
            line-height: 1.8;
        }}

        .no-results {{
            text-align: center;
            padding: 60px;
            color: #718096;
            font-size: 1.2em;
            background: white;
            border-radius: 15px;
        }}

        .results-info {{
            background: white;
            padding: 15px 20px;
            border-radius: 10px;
            margin-bottom: 15px;
            font-weight: bold;
            color: #2d3748;
        }}
    </style>
</head>
<body>
    <!-- グローバルナビゲーション -->
    <nav class="global-nav">
        <div class="global-nav-content">
            <a href="index.html" class="global-nav-logo">📰 NHK記事追跡システム</a>
            <div class="global-nav-links">
                <a href="index.html" class="global-nav-link">ポータル</a>
                <a href="history.html" class="global-nav-link">最近の変更</a>
                <a href="corrections.html" class="global-nav-link active">おことわり</a>
                <a href="archive.html" class="global-nav-link">アーカイブ</a>
            </div>
        </div>
    </nav>

    <div class="container">
        <header>
            <h1>🔴 おことわり記事一覧</h1>
            <p class="subtitle">訂正・おことわりが含まれた記事（削除されたものも含む）</p>
            <div class="stats">
                <div class="stat-item">
                    <div class="stat-number">{len(articles)}</div>
                    <div class="stat-label">おことわり記事数</div>
                </div>
"""

    # ソース別統計
    for stat in stats:
        source_name = stat[0]
        count = stat[1]
        html += f"""
                <div class="stat-item">
                    <div class="stat-number">{count}</div>
                    <div class="stat-label">{source_name.replace('NHK', '')}</div>
                </div>
"""

    html += """
            </div>
        </header>

        <div class="filter-bar">
            <div class="filter-section">
                <label class="filter-label">🔍 検索</label>
                <input type="text" id="searchBox" class="search-box" placeholder="タイトルや説明文で検索...">
            </div>

            <div class="filter-section">
                <label class="filter-label">📰 ニュースソース</label>
                <div class="filter-buttons">
                    <button class="filter-btn source-filter active" data-source="all">すべて</button>
"""

    for source in all_sources:
        html += f'                    <button class="filter-btn source-filter" data-source="{source}">{source.replace("NHK", "")}</button>\n'

    html += """
                </div>
            </div>
        </div>

        <div class="results-info">
            表示中: <span id="resultCount">0</span>件
        </div>

        <div id="articlesContainer">
"""

    if not articles:
        html += """
            <div class="no-results">
                おことわり記事はまだ記録されていません。<br>
                システムが自動でチェックしています。
            </div>
"""
    else:
        for article in articles:
            first_seen = datetime.fromisoformat(article['first_seen'])
            last_seen = datetime.fromisoformat(article['last_seen'])

            first_seen_str = first_seen.strftime('%Y年%m月%d日 %H:%M')
            last_seen_str = last_seen.strftime('%Y年%m月%d日 %H:%M')

            full_url = get_full_url(article['source'], article['link'])

            # データ属性
            data_attrs = f'data-source="{article["source"]}"'
            data_attrs += f' data-search="{article["title"]} {article["description"] or ""}"'

            html += f"""
            <div class="article-card" {data_attrs}>
                <div class="article-header">
                    <span class="article-source">{article['source']}</span>
                    <div class="article-meta">
                        <div>初回確認: {first_seen_str}</div>
                        <div>最終確認: {last_seen_str}</div>
                    </div>
                </div>

                <div class="article-title">{article['title']}</div>
                <a href="{full_url}" class="article-link" target="_blank">→ 元記事を読む（NHK）</a>
                <div class="article-badges"><span class="badge badge-correction">🔴 おことわり: {article["correction_keywords"]}</span></div>
"""

            # おことわり部分を抽出して表示
            if article['description'] and ('※' in article['description'] or '失礼しました' in article['description']):
                correction_summary = extract_correction_summary(article['description'], 200)
                highlighted_correction = highlight_correction_notice(correction_summary)

                html += f"""                <div class="change-diff">
                    <div class="diff-new">【引用】おことわり部分:\n{highlighted_correction}</div>
                    <div style="margin-top: 10px; text-align: right;">
                        <a href="{full_url}" target="_blank" style="color: #fc4a1a; text-decoration: none; font-weight: bold;">→ 元記事を読む（NHK）</a>
                    </div>
                </div>
"""

            html += """
            </div>
"""

    html += """
        </div>
    </div>

    <script>
        const searchBox = document.getElementById('searchBox');
        const sourceFilters = document.querySelectorAll('.source-filter');
        const articles = document.querySelectorAll('.article-card');
        const resultCount = document.getElementById('resultCount');

        let currentSource = 'all';
        let currentSearch = '';

        function filterArticles() {
            let visibleCount = 0;

            articles.forEach(article => {
                const articleSource = article.getAttribute('data-source');
                const searchText = article.getAttribute('data-search').toLowerCase();

                // ソースフィルター
                const sourceMatch = currentSource === 'all' || articleSource === currentSource;

                // 検索フィルター
                const searchMatch = currentSearch === '' || searchText.includes(currentSearch);

                // すべての条件を満たす場合のみ表示
                if (sourceMatch && searchMatch) {
                    article.style.display = 'block';
                    visibleCount++;
                } else {
                    article.style.display = 'none';
                }
            });

            resultCount.textContent = visibleCount;
        }

        // 検索ボックス
        searchBox.addEventListener('input', (e) => {
            currentSearch = e.target.value.toLowerCase();
            filterArticles();
        });

        // ソースフィルター
        sourceFilters.forEach(btn => {
            btn.addEventListener('click', () => {
                sourceFilters.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentSource = btn.getAttribute('data-source');
                filterArticles();
            });
        });

        // 初期表示
        filterArticles();
    </script>

    <!-- NHKアクセストラッキング -->
    <script>
    (function() {
        try {
            var path = window.location.pathname + window.location.search;
            fetch('/.netlify/functions/track-access?path=' + encodeURIComponent(path), {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            }).catch(function(err) {
                console.log('Tracking skipped:', err);
            });
        } catch(e) {
            console.log('Tracking error:', e);
        }
    })();
    </script>
</body>
</html>
"""

    # HTMLファイルを書き込み
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✅ おことわり記事HTMLを生成しました: {output_path}")
    print(f"📊 おことわり記事数: {len(articles)}件")

def main():
    """メイン処理"""
    db_path = PROJECT_ROOT / 'data' / 'articles.db'
    output_path = PROJECT_ROOT / 'reports' / 'corrections.html'

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("NHKおことわり記事ビューアー")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()

    # データベースから訂正記事を取得
    print("📖 データベースからおことわり記事を取得中...")
    articles = get_correction_articles(db_path)
    stats = get_correction_stats(db_path)

    print(f"✅ {len(articles)}件のおことわり記事を取得しました")
    print()

    # HTMLを生成
    print("🎨 HTMLを生成中...")
    generate_html(articles, stats, output_path)

    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"✅ 完了: {output_path}")
    print()
    print("次のコマンドで開きます:")
    print(f"  open {output_path}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

if __name__ == '__main__':
    main()
