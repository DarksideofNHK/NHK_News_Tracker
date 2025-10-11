#!/usr/bin/env python3
"""
NHK記事アーカイブビューアー
取得した全記事を表示（変更の有無に関わらず）
"""

import sqlite3
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
    return relative_path

def get_all_articles(db_path, limit=None):
    """全記事を取得（新しい順）"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = """
    SELECT
        *,
        (SELECT COUNT(*) FROM changes WHERE changes.link = articles.link) as change_count
    FROM articles
    ORDER BY last_seen DESC
    """

    if limit:
        query += f" LIMIT {limit}"

    cursor.execute(query)
    articles = cursor.fetchall()
    conn.close()

    return articles

def get_source_stats(db_path):
    """ソース別統計を取得"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        source,
        COUNT(*) as count,
        MIN(first_seen) as oldest,
        MAX(last_seen) as newest
    FROM articles
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
    <title>NHK記事アーカイブ - 全記事</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Hiragino Sans', sans-serif;
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            padding: 20px;
            line-height: 1.6;
        }}

        .container {{
            max-width: 1400px;
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
            flex-wrap: wrap;
        }}

        .stat-item {{
            text-align: center;
        }}

        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            color: #4facfe;
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
            border-color: #4facfe;
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
            background: #4facfe;
            color: white;
            border-color: #4facfe;
        }}

        .article-card {{
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
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
            background: #e3f2fd;
            color: #1976d2;
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
            color: #4facfe;
            text-decoration: none;
            font-size: 0.85em;
            word-break: break-all;
            display: inline-block;
            margin-bottom: 10px;
        }}

        .article-link:hover {{
            text-decoration: underline;
        }}

        .article-description {{
            color: #4a5568;
            line-height: 1.6;
            margin-top: 10px;
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

        .badge-changed {{
            background: #fef3c7;
            color: #92400e;
        }}

        .badge-correction {{
            background: #fecaca;
            color: #991b1b;
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
            background: #4facfe;
            color: white;
            text-decoration: none;
            border-radius: 8px;
            font-weight: bold;
            transition: background-color 0.2s;
        }}

        .nav-link:hover {{
            background: #3d8fd9;
        }}

        .nav-link.secondary {{
            background: #667eea;
        }}

        .nav-link.secondary:hover {{
            background: #5568d3;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🗂️ NHK記事アーカイブ</h1>
            <p class="subtitle">取得した全ての記事を表示</p>
            <div class="stats">
                <div class="stat-item">
                    <div class="stat-number">{len(articles)}</div>
                    <div class="stat-label">総記事数</div>
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

        <div class="nav-links">
            <a href="history.html" class="nav-link secondary">📜 全変更履歴</a>
        </div>

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

            <div class="filter-section">
                <label class="filter-label">🏷️ フィルター</label>
                <div class="filter-buttons">
                    <button class="filter-btn type-filter active" data-type="all">すべて</button>
                    <button class="filter-btn type-filter" data-type="changed">変更あり</button>
                    <button class="filter-btn type-filter" data-type="correction">訂正関連</button>
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
                まだ記事が記録されていません。<br>
                システムが1時間ごとに自動でチェックしています。
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
            data_attrs += f' data-changed="{1 if article["change_count"] > 0 else 0}"'
            data_attrs += f' data-correction="{1 if article["has_correction"] else 0}"'
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
                <a href="{full_url}" class="article-link" target="_blank">{full_url}</a>

                <div class="article-description">{article['description'] or ''}</div>

                <div class="article-badges">
"""

            if article['change_count'] > 0:
                html += f'                    <span class="badge badge-changed">変更 {article["change_count"]}回</span>\n'

            if article['has_correction']:
                html += f'                    <span class="badge badge-correction">訂正あり: {article["correction_keywords"]}</span>\n'

            html += """
                </div>
            </div>
"""

    html += """
        </div>
    </div>

    <script>
        const searchBox = document.getElementById('searchBox');
        const sourceFilters = document.querySelectorAll('.source-filter');
        const typeFilters = document.querySelectorAll('.type-filter');
        const articles = document.querySelectorAll('.article-card');
        const resultCount = document.getElementById('resultCount');

        let currentSource = 'all';
        let currentType = 'all';
        let currentSearch = '';

        function filterArticles() {
            let visibleCount = 0;

            articles.forEach(article => {
                const articleSource = article.getAttribute('data-source');
                const hasChanged = article.getAttribute('data-changed') === '1';
                const hasCorrection = article.getAttribute('data-correction') === '1';
                const searchText = article.getAttribute('data-search').toLowerCase();

                // ソースフィルター
                const sourceMatch = currentSource === 'all' || articleSource === currentSource;

                // タイプフィルター
                let typeMatch = true;
                if (currentType === 'changed') {
                    typeMatch = hasChanged;
                } else if (currentType === 'correction') {
                    typeMatch = hasCorrection;
                }

                // 検索フィルター
                const searchMatch = currentSearch === '' || searchText.includes(currentSearch);

                // すべての条件を満たす場合のみ表示
                if (sourceMatch && typeMatch && searchMatch) {
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

        // タイプフィルター
        typeFilters.forEach(btn => {
            btn.addEventListener('click', () => {
                typeFilters.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentType = btn.getAttribute('data-type');
                filterArticles();
            });
        });

        // 初期表示
        filterArticles();
    </script>
</body>
</html>
"""

    # HTMLファイルを書き込み
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✅ アーカイブHTMLを生成しました: {output_path}")
    print(f"📊 総記事数: {len(articles)}件")

def main():
    """メイン処理"""
    db_path = PROJECT_ROOT / 'data' / 'articles.db'
    output_path = PROJECT_ROOT / 'reports' / 'archive.html'

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("NHK記事アーカイブビューアー")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()

    # データベースから記事を取得
    print("📖 データベースから記事を取得中...")
    articles = get_all_articles(db_path)
    stats = get_source_stats(db_path)

    print(f"✅ {len(articles)}件の記事を取得しました")
    print()

    # HTMLを生成
    print("🎨 HTMLアーカイブを生成中...")
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
