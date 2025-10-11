#!/usr/bin/env python3
"""
NHK RSS取得テスト - Selenium版
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from datetime import datetime
import time

# NHKソース一覧
SOURCES = {
    'NHK東北ニュース': 'https://news.web.nhk/tohoku-news/news_all_search.xml',
    'NHK首都圏ニュース': 'https://news.web.nhk/shutoken-news/news_all_search.xml',
    'NHK関西ニュース': 'https://news.web.nhk/kansai-news/news_all_search.xml',
    'NHK福岡ニュース': 'https://news.web.nhk/fukuoka-news/news_all_search.xml',
}

def test_scrape_with_selenium(name, url):
    """Seleniumでスクレイピングテスト"""
    print(f"\n{'='*60}")
    print(f"テスト: {name}")
    print(f"URL: {url}")
    print(f"{'='*60}")

    try:
        # Chrome オプション設定
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # ヘッドレスモード
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        # ドライバー起動
        driver = webdriver.Chrome(options=chrome_options)

        # URLにアクセス
        driver.get(url)

        # ページ読み込み待機
        time.sleep(2)

        # コンテンツ取得
        content = driver.page_source

        print(f"コンテンツサイズ: {len(content):,}文字")

        # 先頭500文字を表示
        print(f"\n先頭500文字:")
        print("-" * 60)
        print(content[:500])
        print("-" * 60)

        # <record>タグの数をカウント
        record_count = content.count('<record>')

        if record_count > 0:
            print(f"\n✅ 成功: {record_count}件の記事を検出")
            driver.quit()
            return True, content
        else:
            # XMLチェック
            if '<?xml' in content:
                print(f"\n✅ 成功: XML形式を検出（{content[:100]}...）")
                driver.quit()
                return True, content
            else:
                print(f"\n❌ 失敗: XMLが見つかりません")
                driver.quit()
                return False, None

    except Exception as e:
        print(f"\n❌ 失敗: {type(e).__name__}: {e}")
        return False, None

def main():
    """全ソースのテスト実行"""
    print(f"\n{'#'*60}")
    print(f"# NHK RSS取得テスト (Selenium) - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*60}")

    results = {}

    for name, url in SOURCES.items():
        success, content = test_scrape_with_selenium(name, url)
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
        print("→ Selenium実装で完全自動化が可能です")
    elif success_count > 0:
        print(f"\n⚠️  {total_count - success_count}個のソースで失敗")
        print("→ 成功したソースはSelenium実装可能")
    else:
        print("\n❌ すべてのソースで失敗")

if __name__ == '__main__':
    main()
