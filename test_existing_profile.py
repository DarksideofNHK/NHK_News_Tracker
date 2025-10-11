#!/usr/bin/env python3
"""
既存Chromeプロファイルを使用したテスト

重要: このスクリプトを実行する前に、Chromeを完全に閉じてください
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from pathlib import Path
import time

def test_with_existing_profile():
    """既存Chromeプロファイルでアクセステスト"""
    print("="*60)
    print("既存Chromeプロファイル使用テスト")
    print("="*60)
    print("\n⚠️  重要:")
    print("1. Chromeを完全に閉じてください")
    print("2. Chromeが起動中だとエラーになります")
    print("\nChromeを閉じましたか？（Enter で続行）")
    input()

    # Chromeプロファイルパス
    home = Path.home()
    chrome_user_data = home / "Library/Application Support/Google/Chrome"

    print(f"\nChromeプロファイル: {chrome_user_data}")
    print(f"使用プロファイル: Default\n")

    # Chromeオプション
    chrome_options = Options()

    # 既存プロファイルを使用
    chrome_options.add_argument(f"user-data-dir={chrome_user_data}")
    chrome_options.add_argument("profile-directory=Default")

    # その他のオプション
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    # 初回はヘッドレスなし（確認のため）
    # chrome_options.add_argument("--headless")

    print("Chromeを起動中...")

    try:
        driver = webdriver.Chrome(options=chrome_options)

        # テストURL（NHK東北）
        test_url = 'https://news.web.nhk/tohoku-news/news_all_search.xml'

        print(f"アクセス中: {test_url}\n")
        driver.get(test_url)

        # ページ読み込み待機
        time.sleep(5)

        # コンテンツ取得
        content = driver.page_source

        print(f"コンテンツサイズ: {len(content):,}文字")
        print(f"\n先頭500文字:")
        print("-" * 60)
        print(content[:500])
        print("-" * 60)

        # 結果判定
        if 'JWT token' in content or '"error"' in content:
            print("\n❌ 失敗: JWT認証エラー")
            print("\n原因:")
            print("- 既存Chromeプロファイルでも認証情報が不足")
            print("- または、プロファイル選択が間違っている")
            print("\n対処:")
            print("1. 通常のChromeでどのプロファイルを使っているか確認")
            print("2. chrome://version で「プロフィール パス」を確認")
            success = False

        elif '<?xml' in content and '<search' in content:
            record_count = content.count('<record>')
            print(f"\n✅ 成功: {record_count}件の記事を検出")
            print("\n既存Chromeプロファイルの認証情報が使えました！")
            success = True

        else:
            print("\n⚠️  不明な応答")
            success = False

        print("\n10秒後にブラウザを閉じます...")
        time.sleep(10)
        driver.quit()

        return success

    except Exception as e:
        print(f"\n❌ エラー: {e}")

        if "user data directory is already in use" in str(e):
            print("\n原因: Chromeが起動中です")
            print("\n対処:")
            print("1. すべてのChromeウィンドウを閉じる")
            print("2. アクティビティモニタでChromeプロセスを確認")
            print("3. 必要なら強制終了: pkill -9 'Google Chrome'")
            print("4. 再度このスクリプトを実行")

        return False

def main():
    """メイン実行"""
    success = test_with_existing_profile()

    print("\n" + "="*60)
    if success:
        print("✅ テスト成功！")
        print("\n次のステップ:")
        print("1. scraper_hybrid.py を既存プロファイル使用に変更")
        print("2. python test_hybrid.py で7ソース全部テスト")
        print("3. python main_hybrid.py で本番実行")
    else:
        print("❌ テスト失敗")
        print("\nトラブルシューティング:")
        print("1. 通常のChromeで chrome://version を開く")
        print("2. 「プロフィール パス」を確認（例: Default or Profile 1）")
        print("3. そのプロファイル名を使ってテスト")

    print("="*60)

if __name__ == '__main__':
    main()
