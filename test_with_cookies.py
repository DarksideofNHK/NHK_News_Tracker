#!/usr/bin/env python3
"""
NHK RSS取得テスト - Cookie使用版

使い方:
1. Chromeでhttps://news.web.nhk/tohoku-news/news_all_search.xmlを開く
2. DevToolsでCookieをコピー
3. このスクリプトのCOOKIES変数に貼り付け
4. 実行
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

# ここにブラウザのCookieを貼り付け
# 取得方法: Chrome DevTools → Application → Cookies → news.web.nhk
COOKIES = [
    # 例: {'name': 'cookie_name', 'value': 'cookie_value', 'domain': '.web.nhk'},
]

def test_with_cookies(url):
    """Cookieを使ってアクセス"""
    print(f"アクセス: {url}\n")

    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(options=chrome_options)

    # まず一度アクセス（Cookieを設定するため）
    driver.get('https://news.web.nhk')
    time.sleep(1)

    # Cookieを追加
    if COOKIES:
        for cookie in COOKIES:
            try:
                driver.add_cookie(cookie)
                print(f"Cookie追加: {cookie['name']}")
            except Exception as e:
                print(f"Cookie追加失敗: {e}")
    else:
        print("⚠️  COOKIES変数が空です。ブラウザからCookieを取得してください。")
        print("\n取得方法:")
        print("1. Chromeでhttps://news.web.nhk/tohoku-news/news_all_search.xmlを開く")
        print("2. F12 → Application → Cookies → news.web.nhk")
        print("3. すべてのCookieをコピーしてCOOKIES変数に貼り付け")

    # 目的のURLにアクセス
    driver.get(url)
    time.sleep(2)

    content = driver.page_source
    print(f"\nコンテンツサイズ: {len(content):,}文字")
    print(f"先頭500文字:\n{content[:500]}\n")

    record_count = content.count('<record>')
    if record_count > 0:
        print(f"✅ 成功: {record_count}件の記事を検出")
    elif '<?xml' in content:
        print(f"✅ 成功: XML検出")
    elif 'JWT token' in content:
        print(f"❌ 失敗: JWT認証エラー（Cookieが必要）")
    else:
        print(f"❌ 失敗: XMLが見つかりません")

    driver.quit()

if __name__ == '__main__':
    test_with_cookies('https://news.web.nhk/tohoku-news/news_all_search.xml')
