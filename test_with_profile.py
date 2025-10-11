#!/usr/bin/env python3
"""
NHK RSS取得テスト - Chromeプロファイル使用版

事前準備:
1. 通常のChromeで https://news.web.nhk/tohoku-news/news_all_search.xml を開く
2. 正常にXMLが表示されることを確認
3. Chromeを閉じずにこのスクリプトを実行

注意: Chromeプロファイルが使用中だとエラーになるため、
      専用プロファイルを作成します。
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
import os

# NHKソース一覧
SOURCES = {
    'NHK東北ニュース': 'https://news.web.nhk/tohoku-news/news_all_search.xml',
    'NHK首都圏ニュース': 'https://news.web.nhk/shutoken-news/news_all_search.xml',
    'NHK関西ニュース': 'https://news.web.nhk/kansai-news/news_all_search.xml',
    'NHK福岡ニュース': 'https://news.web.nhk/fukuoka-news/news_all_search.xml',
}

def create_chrome_driver_with_profile():
    """Chromeプロファイルを使用したドライバー作成"""
    chrome_options = Options()

    # ユーザーデータディレクトリ（専用プロファイル）
    user_data_dir = os.path.expanduser('~/Library/Application Support/Google/Chrome_NHK_Scraper')
    chrome_options.add_argument(f'user-data-dir={user_data_dir}')

    # プロファイル名（新規作成）
    chrome_options.add_argument('profile-directory=Default')

    # その他のオプション
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')

    # ヘッドレスモードは一旦無効（初回セットアップ時はブラウザを表示）
    # chrome_options.add_argument('--headless')

    driver = webdriver.Chrome(options=chrome_options)
    return driver

def test_with_profile(url, driver):
    """プロファイルを使ってアクセス"""
    try:
        driver.get(url)
        time.sleep(3)  # ページ読み込み待機

        content = driver.page_source

        print(f"コンテンツサイズ: {len(content):,}文字")

        # JWT認証エラーチェック
        if 'JWT token' in content or '"error"' in content:
            print(f"❌ JWT認証エラー検出")
            print(f"先頭500文字:\n{content[:500]}\n")
            return False, None

        # XMLチェック
        if '<?xml' in content or '<search' in content:
            record_count = content.count('<record>')
            print(f"✅ 成功: {record_count}件の記事を検出")
            print(f"先頭200文字: {content[:200]}...")
            return True, content
        else:
            print(f"❌ XMLが見つかりません")
            print(f"先頭500文字:\n{content[:500]}\n")
            return False, None

    except Exception as e:
        print(f"❌ エラー: {e}")
        return False, None

def main():
    """メインテスト"""
    print("="*60)
    print("NHK RSS取得テスト - Chromeプロファイル使用")
    print("="*60)
    print("\n初回実行時の手順:")
    print("1. Chromeウィンドウが自動で開きます")
    print("2. 各URLに自動でアクセスします")
    print("3. 401エラーが出た場合:")
    print("   - ブラウザで手動ログインが必要な可能性があります")
    print("   - その場合、ブラウザ上で認証を完了してください\n")

    input("準備ができたらEnterキーを押してください...")

    # ドライバー作成
    driver = create_chrome_driver_with_profile()

    results = {}

    try:
        for name, url in SOURCES.items():
            print(f"\n{'─'*60}")
            print(f"テスト: {name}")
            print(f"URL: {url}")
            print(f"{'─'*60}")

            success, content = test_with_profile(url, driver)
            results[name] = success

            time.sleep(2)  # 次のリクエストまで待機

    finally:
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
            print("\n次のステップ:")
            print("1. scraper_selenium.pyのheadless=Trueに変更")
            print("2. main_selenium.pyで自動実行")
            print("3. cronで1時間ごとに実行")
        elif success_count > 0:
            print(f"\n⚠️  {total_count - success_count}個のソースで失敗")
        else:
            print("\n❌ すべてのソースで失敗")
            print("\n対処方法:")
            print("1. ブラウザで手動でhttps://news.web.nhkにアクセス")
            print("2. 必要に応じてログイン/認証")
            print("3. 再度このスクリプトを実行")

        print("\nブラウザを閉じます（10秒後）...")
        time.sleep(10)
        driver.quit()

if __name__ == '__main__':
    main()
