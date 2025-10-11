#!/usr/bin/env python3
"""
NHK東北専用Chromeプロファイル作成

このスクリプトの目的:
1. 既存Chromeとは完全に独立したプロファイルを作成
2. NHK東北にアクセスしてセッション/Cookie保存
3. 以降、Seleniumから自動アクセス可能
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
import os
from pathlib import Path

def setup_dedicated_profile():
    """専用プロファイル作成"""
    print("="*60)
    print("NHK東北専用Chromeプロファイル作成")
    print("="*60)

    # 専用プロファイルディレクトリ
    profile_dir = os.path.expanduser('~/nhk_scraper_chrome_profile')

    print(f"\n専用プロファイル作成先:")
    print(f"  {profile_dir}")
    print(f"\nこれは既存のChromeとは完全に独立しています。")

    # 既に存在する場合は確認
    if os.path.exists(profile_dir):
        print(f"\n⚠️  既にプロファイルが存在します。")
        print(f"削除して再作成しますか？ (y/n)")
        response = input().strip().lower()
        if response == 'y':
            import shutil
            shutil.rmtree(profile_dir)
            print(f"✅ 既存プロファイルを削除しました")
        else:
            print(f"既存プロファイルを使用します")

    print(f"\n準備ができたらEnterキーを押してください...")
    input()

    # Chromeオプション
    chrome_options = Options()
    chrome_options.add_argument(f'user-data-dir={profile_dir}')
    chrome_options.add_argument('profile-directory=Default')

    # その他のオプション
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')

    # 初回はブラウザを表示（ヘッドレスなし）
    # chrome_options.add_argument('--headless')

    print("\n専用Chromeを起動中...")
    print("（既存のChromeとは別のウィンドウが開きます）\n")

    try:
        driver = webdriver.Chrome(options=chrome_options)

        # テストURL
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
            print("\n❌ JWT認証エラー")
            print("\n次の手順:")
            print("1. ブラウザウィンドウを確認してください")
            print("2. もし認証画面が表示されていたら、ログインしてください")
            print("3. その後、このプロファイルは保存されます")
            print("\nブラウザウィンドウを確認してください（30秒待機）...")
            time.sleep(30)

            # 再度コンテンツ取得
            content = driver.page_source
            if '<?xml' in content and '<search' in content:
                record_count = content.count('<record>')
                print(f"\n✅ 認証成功！{record_count}件の記事を検出")
                success = True
            else:
                print("\n❌ まだ認証エラーです")
                success = False

        elif '<?xml' in content and '<search' in content:
            record_count = content.count('<record>')
            print(f"\n✅ 成功: {record_count}件の記事を検出")
            print("\nセッション/Cookieが保存されました！")
            success = True

        else:
            print("\n⚠️  不明な応答")
            success = False

        print("\n10秒後にブラウザを閉じます...")
        time.sleep(10)
        driver.quit()

        return success, profile_dir

    except Exception as e:
        print(f"\n❌ エラー: {e}")
        return False, profile_dir

def main():
    """メイン実行"""
    print("\n" + "#"*60)
    print("# 重要な注意事項")
    print("#"*60)
    print("\nこのスクリプトは:")
    print("1. 既存のChromeとは別の、独立したプロファイルを作成します")
    print("2. 既存のChromeは影響を受けません")
    print("3. macOSの自動再起動の影響も受けません")
    print("\n" + "#"*60)

    success, profile_dir = setup_dedicated_profile()

    print("\n" + "="*60)
    if success:
        print("✅ セットアップ成功！")
        print(f"\nプロファイル保存先:")
        print(f"  {profile_dir}")
        print("\n次のステップ:")
        print("1. python test_dedicated_profile.py でテスト")
        print("2. python test_hybrid.py で7ソース全部テスト")
        print("3. python main_hybrid.py で本番実行")
        print("\n完全自動化達成！")
    else:
        print("❌ セットアップ失敗")
        print("\n対処方法:")
        print("1. ブラウザウィンドウで認証が必要か確認")
        print("2. 再度このスクリプトを実行")

    print("="*60)

if __name__ == '__main__':
    main()
