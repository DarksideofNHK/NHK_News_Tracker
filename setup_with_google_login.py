#!/usr/bin/env python3
"""
NHK東北専用プロファイル作成（Googleログイン付き）

重要: NHK東北RSSフィードはGoogleアカウントログインが必要
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import os

def setup_with_google_login():
    """Googleログイン後、NHK東北にアクセス"""
    print("="*60)
    print("NHK東北専用プロファイル作成（Googleログイン付き）")
    print("="*60)

    profile_dir = os.path.expanduser('~/nhk_scraper_chrome_profile')

    print(f"\n専用プロファイル: {profile_dir}")

    # 既存プロファイルの処理
    if os.path.exists(profile_dir):
        print(f"\n既存プロファイルが見つかりました。")
        print(f"削除して再作成しますか？ (y/n)")
        response = input().strip().lower()
        if response == 'y':
            import shutil
            shutil.rmtree(profile_dir)
            print(f"✅ 削除しました")

    print("\n" + "="*60)
    print("手順:")
    print("="*60)
    print("\n1. Chromeウィンドウが開きます")
    print("2. Googleログインページが表示されます")
    print("3. **Googleアカウントにログインしてください**")
    print("4. ログイン完了後、このスクリプトが自動でNHK東北にアクセスします")
    print("\n準備ができたらEnterキーを押してください...")
    input()

    # Chromeオプション
    chrome_options = Options()
    chrome_options.add_argument(f'user-data-dir={profile_dir}')
    chrome_options.add_argument('profile-directory=Default')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')

    # ブラウザを表示（ログイン用）
    # chrome_options.add_argument('--headless')

    print("\nChromeを起動中...")

    try:
        driver = webdriver.Chrome(options=chrome_options)

        # ステップ1: Googleログインページを開く
        print("\n" + "─"*60)
        print("ステップ1: Googleログイン")
        print("─"*60)
        print("\nGoogleログインページを開きます...")

        driver.get('https://accounts.google.com/signin')

        print("\n⚠️  重要:")
        print("1. ブラウザでGoogleアカウントにログインしてください")
        print("2. ログインが完了したら、このターミナルに戻ってください")
        print("3. Enterキーを押すと、NHK東北にアクセスします")
        print("\nログイン完了後、Enterキーを押してください...")
        input()

        # ステップ2: NHK東北にアクセス
        print("\n" + "─"*60)
        print("ステップ2: NHK東北にアクセス")
        print("─"*60)

        test_url = 'https://news.web.nhk/tohoku-news/news_all_search.xml'

        print(f"\nアクセス中: {test_url}\n")
        driver.get(test_url)

        time.sleep(5)

        content = driver.page_source

        print(f"コンテンツサイズ: {len(content):,}文字")
        print(f"\n先頭500文字:")
        print("-" * 60)
        print(content[:500])
        print("-" * 60)

        # 結果判定
        if 'JWT token' in content or '"error"' in content:
            print("\n❌ まだJWT認証エラー")
            print("\n原因:")
            print("  Googleログインが完了していない可能性があります")
            print("\n対処:")
            print("1. ブラウザウィンドウを確認")
            print("2. Googleにログインしているか確認")
            print("3. 再度 https://news.web.nhk/tohoku-news/news_all_search.xml にアクセス")
            print("\n30秒間ブラウザを開いたままにします...")
            print("手動でURLにアクセスして、XMLが表示されるか確認してください")
            time.sleep(30)
            success = False

        elif '<?xml' in content and '<search' in content:
            record_count = content.count('<record>')
            print(f"\n✅ 成功: {record_count}件の記事を検出")
            print("\nGoogleログイン情報とセッションが保存されました！")
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
    print("# 重要: NHK東北RSSはGoogleログインが必要です")
    print("#"*60)
    print("\nこのスクリプトは:")
    print("1. 専用Chromeプロファイルを作成")
    print("2. Googleログインページを開く")
    print("3. ログイン後、NHK東北にアクセス")
    print("4. セッション/Cookieを保存")
    print("\n" + "#"*60)

    success, profile_dir = setup_with_google_login()

    print("\n" + "="*60)
    if success:
        print("✅ セットアップ成功！")
        print(f"\nプロファイル: {profile_dir}")
        print("\n保存された情報:")
        print("  - Googleログイン情報")
        print("  - NHK東北アクセス用セッション/Cookie")
        print("\n次のステップ:")
        print("1. python test_dedicated_profile.py でテスト")
        print("2. python test_hybrid.py で7ソース全部テスト")
        print("3. python main_hybrid.py で本番実行")
        print("4. cronで1時間ごとに自動実行")
        print("\n🎉 完全自動化達成！")
    else:
        print("❌ セットアップ失敗")
        print("\nトラブルシューティング:")
        print("1. Googleアカウントにログインできましたか？")
        print("2. ブラウザで https://news.web.nhk/tohoku-news/news_all_search.xml が開けますか？")
        print("3. 再度このスクリプトを実行してください")

    print("="*60)

if __name__ == '__main__':
    main()
