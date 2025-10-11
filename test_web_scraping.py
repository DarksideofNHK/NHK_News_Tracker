#!/usr/bin/env python3
"""
NHKウェブサイトスクレイピングテスト
RSSフィードが使えない場合の代替案
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import datetime

# NHK地方ニュースサイト
SOURCES = {
    'NHK東北ニュース': 'https://www3.nhk.or.jp/tohoku-news/',
    'NHK首都圏ニュース': 'https://www3.nhk.or.jp/shutoken-news/',
    'NHK関西ニュース': 'https://www3.nhk.or.jp/kansai-news/',
    'NHK福岡ニュース': 'https://www3.nhk.or.jp/fukuoka-news/',
}

def test_web_scraping(name, url):
    """ウェブサイトから記事一覧を取得"""
    print(f"\n{'='*60}")
    print(f"テスト: {name}")
    print(f"URL: {url}")
    print(f"{'='*60}")

    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')

    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)

        # ページ読み込み待機
        time.sleep(3)

        # ページタイトル確認
        print(f"ページタイトル: {driver.title}")

        # HTMLサイズ
        html_size = len(driver.page_source)
        print(f"HTMLサイズ: {html_size:,}文字")

        # 401エラーチェック
        if '401' in driver.page_source or 'JWT token' in driver.page_source:
            print(f"❌ 認証エラー検出")
            driver.quit()
            return False

        # 記事リンクを検出
        # NHKの記事リンクは通常 /news/html/YYYYMMDD/kXXXXXXXXXXX.html 形式
        links = driver.find_elements(By.TAG_NAME, 'a')

        article_links = []
        for link in links:
            href = link.get_attribute('href')
            if href and '/html/' in href and '.html' in href:
                article_links.append(href)

        # 重複除去
        article_links = list(set(article_links))

        print(f"\n検出された記事リンク数: {len(article_links)}")

        if article_links:
            print(f"\n最初の5件:")
            for i, link in enumerate(article_links[:5], 1):
                print(f"  {i}. {link}")

            print(f"\n✅ 成功: ウェブサイトから記事取得可能")
            driver.quit()
            return True
        else:
            print(f"\n⚠️  記事リンクが見つかりませんでした")
            print(f"\nHTML先頭1000文字:")
            print(driver.page_source[:1000])
            driver.quit()
            return False

    except Exception as e:
        print(f"\n❌ エラー: {e}")
        return False

def main():
    """メインテスト"""
    print(f"\n{'#'*60}")
    print(f"# NHKウェブサイトスクレイピングテスト")
    print(f"# {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*60}")

    results = {}

    for name, url in SOURCES.items():
        success = test_web_scraping(name, url)
        results[name] = success
        time.sleep(2)  # リクエスト間隔

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

    if success_count > 0:
        print(f"\n✅ ウェブサイトスクレイピングで代替可能")
        print(f"\n次のステップ:")
        print(f"1. 各記事ページから詳細を取得")
        print(f"2. タイトル・本文を抽出")
        print(f"3. URLをキーとして変更検出")

if __name__ == '__main__':
    main()
