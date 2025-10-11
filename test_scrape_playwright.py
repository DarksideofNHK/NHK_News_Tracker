#!/usr/bin/env python3
"""
NHK RSS取得テスト - Playwright版
本物のChromeブラウザでアクセス
"""
from playwright.sync_api import sync_playwright
from datetime import datetime

# NHKソース一覧
SOURCES = {
    'NHK東北ニュース': 'https://news.web.nhk/tohoku-news/news_all_search.xml',
    'NHK首都圏ニュース': 'https://news.web.nhk/shutoken-news/news_all_search.xml',
    'NHK関西ニュース': 'https://news.web.nhk/kansai-news/news_all_search.xml',
    'NHK福岡ニュース': 'https://news.web.nhk/fukuoka-news/news_all_search.xml',
}

def test_scrape_with_playwright(name, url):
    """Playwrightでスクレイピングテスト"""
    print(f"\n{'='*60}")
    print(f"テスト: {name}")
    print(f"URL: {url}")
    print(f"{'='*60}")

    try:
        with sync_playwright() as p:
            # Chromiumブラウザを起動（ヘッドレスモード）
            browser = p.chromium.launch(headless=True)

            # 新しいページを開く
            page = browser.new_page()

            # URLにアクセス
            response = page.goto(url, wait_until='networkidle', timeout=30000)

            # コンテンツ取得
            content = page.content()

            print(f"ステータスコード: {response.status}")
            print(f"コンテンツサイズ: {len(content):,}文字")

            if response.status == 200:
                # 先頭500文字を表示
                print(f"\n先頭500文字:")
                print("-" * 60)
                print(content[:500])
                print("-" * 60)

                # <record>タグの数をカウント
                record_count = content.count('<record>')
                print(f"\n✅ 成功: {record_count}件の記事を検出")

                browser.close()
                return True, content
            else:
                print(f"\n❌ 失敗: HTTPエラー {response.status}")
                browser.close()
                return False, None

    except Exception as e:
        print(f"\n❌ 失敗: {type(e).__name__}: {e}")
        return False, None

def main():
    """全ソースのテスト実行"""
    print(f"\n{'#'*60}")
    print(f"# NHK RSS取得テスト (Playwright) - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*60}")

    results = {}

    for name, url in SOURCES.items():
        success, content = test_scrape_with_playwright(name, url)
        results[name] = success

    # 結果サマリー
    print(f"\n{'='*60}")
    print("テスト結果サマリー")
    print(f"{'='*60}")

    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)

    for name, success in results.items():
        status = "✅ 成功" if success else "❌ 失敗"
        print(f"{status}: {name}")

    print(f"\n成功率: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")

    if success_count == total_count:
        print("\n🎉 すべてのソースで取得成功！")
        print("→ Playwright実装で完全自動化が可能です")
    elif success_count > 0:
        print(f"\n⚠️  {total_count - success_count}個のソースで失敗")
        print("→ 成功したソースはPlaywright実装可能")
    else:
        print("\n❌ すべてのソースで失敗")
        print("→ ブラウザで手動アクセスして確認してください")

if __name__ == '__main__':
    main()
