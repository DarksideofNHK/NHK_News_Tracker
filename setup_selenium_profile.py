#!/usr/bin/env python3
"""
Seleniumプロファイルセットアップ（NHK東北用）

このスクリプトは一度だけ実行すればOK:
1. Chromeウィンドウが開く
2. NHK東北ニュースにアクセス
3. セッション/Cookieを保存
4. 以降は自動でアクセス可能
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import os

def setup_profile():
    """Seleniumプロファイルを作成"""
    print("="*60)
    print("Seleniumプロファイルセットアップ（NHK東北用）")
    print("="*60)
    print("\n手順:")
    print("1. Chromeウィンドウが自動で開きます")
    print("2. NHK東北ニュースのRSSフィードにアクセスします")
    print("3. XMLが正常に表示されれば成功です")
    print("4. セッション/Cookieが保存されます")
    print("\n準備ができたらEnterキーを押してください...")
    input()

    # プロファイルディレクトリ
    profile_dir = os.path.expanduser('~/Library/Application Support/Google/Chrome_NHK_Scraper')

    print(f"\nプロファイルディレクトリ: {profile_dir}")

    # Chromeオプション
    chrome_options = Options()
    chrome_options.add_argument(f'user-data-dir={profile_dir}')
    chrome_options.add_argument('profile-directory=Default')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')

    # ヘッドレスモードは無効（初回セットアップ時はブラウザを表示）
    # chrome_options.add_argument('--headless')

    print("\nChromeを起動中...")
    driver = webdriver.Chrome(options=chrome_options)

    # テストURL
    test_url = 'https://news.web.nhk/tohoku-news/news_all_search.xml'

    print(f"\nアクセス中: {test_url}")
    driver.get(test_url)

    # ページ読み込み待機
    time.sleep(5)

    # コンテンツ取得
    content = driver.page_source

    print(f"\nコンテンツサイズ: {len(content):,}文字")
    print(f"先頭500文字:\n{content[:500]}\n")

    # 結果判定
    if 'JWT token' in content or '"error"' in content:
        print("❌ 失敗: JWT認証エラー")
        print("\n対処方法:")
        print("1. ブラウザウィンドウを確認してください")
        print("2. 認証画面が表示されている場合は、ログインしてください")
        print("3. XMLが表示されたら、このスクリプトを再実行してください")
        print("\nブラウザを30秒間開いたままにします...")
        time.sleep(30)
        success = False

    elif '<?xml' in content or '<search' in content:
        record_count = content.count('<record>')
        print(f"✅ 成功: {record_count}件の記事を検出")
        print("\nセッション/Cookieが保存されました！")
        success = True

    else:
        print("⚠️  不明な応答")
        print("\nブラウザを確認してください（30秒待機）...")
        time.sleep(30)
        success = False

    print("\nブラウザを閉じます...")
    driver.quit()

    print("\n" + "="*60)
    if success:
        print("✅ セットアップ完了！")
        print("\n次のステップ:")
        print("1. python test_hybrid.py でテスト実行")
        print("2. python main_hybrid.py で本番実行")
        print("3. cronで1時間ごとに自動実行")
    else:
        print("❌ セットアップ失敗")
        print("\n再試行してください:")
        print("  python setup_selenium_profile.py")

    print("="*60)

if __name__ == '__main__':
    setup_profile()
