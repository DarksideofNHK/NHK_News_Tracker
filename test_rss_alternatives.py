#!/usr/bin/env python3
"""
NHK RSSフィード代替手段の調査

以下をテスト:
1. 別のRSSフィードURL（地域ニュース以外）
2. NHKのサイトマップ
3. JSON APIの存在確認
"""
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

# テスト対象URL
TEST_URLS = {
    # 標準的なRSSフィード
    'NHK主要ニュース': 'https://www.nhk.or.jp/rss/news/cat0.xml',
    'NHK社会': 'https://www.nhk.or.jp/rss/news/cat1.xml',
    'NHK政治': 'https://www.nhk.or.jp/rss/news/cat4.xml',

    # 地方ニュース（別パターン）
    '東北ニュース(alt1)': 'https://www3.nhk.or.jp/rss/news/cat16.xml',
    '東北ニュース(alt2)': 'https://www.nhk.or.jp/tohoku/rss/news.xml',

    # JSON API候補
    'JSON API候補1': 'https://www3.nhk.or.jp/news/json16/new_001.json',
    'JSON API候補2': 'https://www3.nhk.or.jp/news/json16/news_list.json',
}

def test_with_requests(name, url):
    """requestsでテスト"""
    print(f"\n{'─'*60}")
    print(f"[requests] {name}")
    print(f"URL: {url}")

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)

        print(f"ステータス: {response.status_code}")
        print(f"サイズ: {len(response.text):,}文字")

        if response.status_code == 200:
            print(f"先頭200文字: {response.text[:200]}")

            # 内容チェック
            if '<?xml' in response.text or '<rss' in response.text:
                print(f"✅ RSS検出")
                return True
            elif response.text.startswith('{') or response.text.startswith('['):
                print(f"✅ JSON検出")
                return True
            else:
                print(f"⚠️  不明な形式")
                return False
        else:
            print(f"❌ HTTPエラー")
            return False

    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

def test_with_selenium(name, url):
    """Seleniumでテスト（JavaScriptレンダリング必要な場合）"""
    print(f"\n{'─'*60}")
    print(f"[Selenium] {name}")
    print(f"URL: {url}")

    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        time.sleep(2)

        content = driver.page_source
        print(f"サイズ: {len(content):,}文字")
        print(f"先頭200文字: {content[:200]}")

        # 認証エラーチェック
        if 'JWT token' in content or '"status": 401' in content:
            print(f"❌ JWT認証エラー")
            driver.quit()
            return False

        # コンテンツチェック
        if '<?xml' in content or '<rss' in content:
            print(f"✅ RSS検出")
            driver.quit()
            return True
        elif '{' in content[:100]:
            print(f"✅ JSON検出")
            driver.quit()
            return True
        else:
            print(f"⚠️  不明な形式")
            driver.quit()
            return False

    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

def main():
    """メインテスト"""
    print("="*60)
    print("NHK RSSフィード代替手段の調査")
    print("="*60)

    results_requests = {}
    results_selenium = {}

    # まずrequestsでテスト（高速）
    print("\n" + "#"*60)
    print("# Phase 1: requests でテスト")
    print("#"*60)

    for name, url in TEST_URLS.items():
        results_requests[name] = test_with_requests(name, url)
        time.sleep(1)

    # requestsで失敗したものをSeleniumでテスト
    print("\n" + "#"*60)
    print("# Phase 2: Selenium でテスト（requests失敗分のみ）")
    print("#"*60)

    failed_urls = {name: url for name, url in TEST_URLS.items()
                   if not results_requests.get(name, False)}

    if failed_urls:
        for name, url in failed_urls.items():
            results_selenium[name] = test_with_selenium(name, url)
            time.sleep(2)
    else:
        print("\nすべてrequestsで成功 - Seleniumテストをスキップ")

    # 結果サマリー
    print("\n" + "="*60)
    print("結果サマリー")
    print("="*60)

    for name in TEST_URLS.keys():
        req_ok = results_requests.get(name, False)
        sel_ok = results_selenium.get(name, False)

        if req_ok:
            print(f"✅ {name} (requests)")
        elif sel_ok:
            print(f"✅ {name} (Selenium)")
        else:
            print(f"❌ {name}")

    # 成功したURLをリスト
    successful = []
    for name in TEST_URLS.keys():
        if results_requests.get(name) or results_selenium.get(name):
            successful.append((name, TEST_URLS[name]))

    if successful:
        print(f"\n🎉 {len(successful)}個のURL取得成功！")
        print(f"\n利用可能なフィード:")
        for name, url in successful:
            print(f"  - {name}: {url}")
    else:
        print(f"\n❌ すべてのURLで失敗")
        print(f"\n→ ウェブサイトスクレイピングへ切り替えが必要")

if __name__ == '__main__':
    main()
