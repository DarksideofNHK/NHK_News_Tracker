#!/usr/bin/env python3
"""
専用プロファイルでのテスト
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import os

def test_dedicated_profile():
    """専用プロファイルでアクセステスト"""
    print("="*60)
    print("専用プロファイルテスト")
    print("="*60)

    profile_dir = os.path.expanduser('~/nhk_scraper_chrome_profile')

    if not os.path.exists(profile_dir):
        print(f"\n❌ プロファイルが見つかりません: {profile_dir}")
        print("\n先に以下を実行してください:")
        print("  python setup_dedicated_profile.py")
        return False

    print(f"\nプロファイル: {profile_dir}")

    # Chromeオプション
    chrome_options = Options()
    chrome_options.add_argument(f'user-data-dir={profile_dir}')
    chrome_options.add_argument('profile-directory=Default')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--headless')  # ヘッドレスモード
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

    print("\n専用Chrome起動中（ヘッドレスモード）...")

    try:
        driver = webdriver.Chrome(options=chrome_options)

        test_url = 'https://news.web.nhk/tohoku-news/news_all_search.xml'

        print(f"アクセス中: {test_url}\n")
        driver.get(test_url)

        time.sleep(3)

        content = driver.page_source

        print(f"コンテンツサイズ: {len(content):,}文字")
        print(f"\n先頭500文字:")
        print("-" * 60)
        print(content[:500])
        print("-" * 60)

        # 結果判定
        if 'JWT token' in content or '"error"' in content:
            print("\n❌ JWT認証エラー")
            print("\n原因:")
            print("  セッション/Cookieが保存されていません")
            print("\n対処:")
            print("  python setup_dedicated_profile.py を再実行")
            success = False

        elif '<?xml' in content and '<search' in content:
            record_count = content.count('<record>')
            print(f"\n✅ 成功: {record_count}件の記事を検出")
            print("\n専用プロファイルで自動アクセスできました！")
            success = True

        else:
            print("\n⚠️  不明な応答")
            success = False

        driver.quit()
        return success

    except Exception as e:
        print(f"\n❌ エラー: {e}")
        return False

def main():
    """メイン実行"""
    success = test_dedicated_profile()

    print("\n" + "="*60)
    if success:
        print("✅ テスト成功！")
        print("\n専用プロファイルが正常に動作しています。")
        print("\n次のステップ:")
        print("1. scraper_hybrid.py を専用プロファイル使用に変更")
        print("2. python test_hybrid.py で7ソース全部テスト")
        print("3. python main_hybrid.py で本番実行")
        print("4. cronで1時間ごとに自動実行")
        print("\n🎉 完全自動化達成！")
    else:
        print("❌ テスト失敗")

    print("="*60)

if __name__ == '__main__':
    main()
