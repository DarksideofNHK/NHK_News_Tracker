#!/usr/bin/env python3
"""
通常のChromeプロファイルからCookieをコピー

手順:
1. 通常のChromeでNHK東北にアクセスできるプロファイルからCookieを取得
2. 専用プロファイルにCookieを追加
3. テスト実行
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import undetected_chromedriver as uc
import time
import os
import json

def get_cookies_from_main_profile():
    """通常のChromeプロファイルからCookieを取得"""
    print("="*60)
    print("ステップ1: 通常のChromeプロファイルからCookie取得")
    print("="*60)

    main_profile = os.path.expanduser('~/Library/Application Support/Google/Chrome')

    print(f"\n通常のChromeプロファイル: {main_profile}")
    print(f"使用プロファイル: Default")

    print("\n⚠️  重要:")
    print("1. 既存の通常のChromeをすべて閉じてください")
    print("2. Chromeが起動中だとプロファイルがロックされます")
    print("\nChromeを閉じましたか？ (y/n)")
    response = input().strip().lower()
    if response != 'y':
        print("Chromeを閉じてから再実行してください")
        return None

    print("\n通常のChromeプロファイルを起動中...")

    try:
        # 通常のChromeプロファイルで起動
        options = Options()
        options.add_argument(f'user-data-dir={main_profile}')
        options.add_argument('profile-directory=Default')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        driver = webdriver.Chrome(options=options)

        # NHK東北にアクセス
        test_url = 'https://news.web.nhk/tohoku-news/news_all_search.xml'

        print(f"アクセス中: {test_url}")
        driver.get(test_url)
        time.sleep(5)

        # Cookie取得
        cookies = driver.get_cookies()

        print(f"\n✅ {len(cookies)}個のCookieを取得しました")

        # NHK関連のCookieを表示
        nhk_cookies = [c for c in cookies if 'nhk' in c.get('domain', '').lower()]
        print(f"NHK関連Cookie: {len(nhk_cookies)}個")

        for cookie in nhk_cookies:
            print(f"  - {cookie['name']} (domain: {cookie['domain']})")

        # すべてのCookieを保存
        cookie_file = 'nhk_cookies.json'
        with open(cookie_file, 'w') as f:
            json.dump(cookies, f, indent=2)

        print(f"\nCookieを保存しました: {cookie_file}")

        driver.quit()

        return cookies

    except Exception as e:
        print(f"\n❌ エラー: {e}")
        print("\n原因:")
        print("  Chromeが起動中の可能性があります")
        print("\n対処:")
        print("  pkill -9 'Google Chrome'")
        print("  その後、再実行してください")
        return None

def add_cookies_to_dedicated_profile(cookies):
    """専用プロファイルにCookieを追加"""
    print("\n" + "="*60)
    print("ステップ2: 専用プロファイルにCookie追加")
    print("="*60)

    profile_dir = os.path.expanduser('~/nhk_scraper_chrome_profile')

    print(f"\n専用プロファイル: {profile_dir}")

    if not os.path.exists(profile_dir):
        print(f"\n❌ 専用プロファイルが見つかりません")
        print("\n先に以下を実行してください:")
        print("  python setup_undetected.py")
        return False

    print("\n専用Chrome起動中（undetected-chromedriver）...")

    try:
        # undetected-chromedriver で起動
        options = uc.ChromeOptions()
        options.add_argument(f'--user-data-dir={profile_dir}')
        options.add_argument('--profile-directory=Default')

        driver = uc.Chrome(options=options, use_subprocess=True)

        # まず任意のページを開く（Cookieを追加するため）
        driver.get('https://news.web.nhk')
        time.sleep(3)

        # Cookieを追加
        print(f"\nCookie追加中...")
        added_count = 0

        for cookie in cookies:
            try:
                # Seleniumで追加できる形式に変換
                cookie_dict = {
                    'name': cookie['name'],
                    'value': cookie['value'],
                    'domain': cookie.get('domain', ''),
                    'path': cookie.get('path', '/'),
                    'secure': cookie.get('secure', False),
                }

                # sameSiteがある場合のみ追加
                if 'sameSite' in cookie:
                    cookie_dict['sameSite'] = cookie['sameSite']

                driver.add_cookie(cookie_dict)
                added_count += 1

            except Exception as e:
                # 一部のCookieは追加できない場合がある（無視）
                pass

        print(f"✅ {added_count}個のCookieを追加しました")

        # NHK東北にアクセスしてテスト
        print("\n" + "─"*60)
        print("ステップ3: NHK東北にアクセステスト")
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
            print("  必要なCookieが不足している可能性があります")
            success = False

        elif '<?xml' in content and '<search' in content:
            record_count = content.count('<record>')
            print(f"\n✅ 成功: {record_count}件の記事を検出")
            print("\nCookieコピーが成功しました！")
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
        import traceback
        traceback.print_exc()
        return False

def main():
    """メイン実行"""
    print("\n" + "#"*60)
    print("# 通常のChromeプロファイルからCookieコピー")
    print("#"*60)
    print("\nこのスクリプトは:")
    print("1. 通常のChromeプロファイル（アクセス可能）からCookieを取得")
    print("2. 専用プロファイルにCookieを追加")
    print("3. NHK東北にアクセステスト")
    print("\n" + "#"*60)

    # ステップ1: Cookie取得
    cookies = get_cookies_from_main_profile()

    if cookies is None:
        print("\n❌ Cookie取得失敗")
        print("\nChromeを完全に閉じてから再実行してください:")
        print("  pkill -9 'Google Chrome'")
        print("  python copy_cookies.py")
        return

    # ステップ2: Cookie追加とテスト
    success = add_cookies_to_dedicated_profile(cookies)

    print("\n" + "="*60)
    if success:
        print("✅ Cookie コピー成功！")
        print("\n専用プロファイルでNHK東北にアクセスできました！")
        print("\n次のステップ:")
        print("1. python test_dedicated_profile.py でヘッドレステスト")
        print("2. scraper_hybrid.py を undetected-chromedriver 使用に変更")
        print("3. python test_hybrid.py で7ソース全部テスト")
        print("\n🎉 完全自動化達成！")
    else:
        print("❌ Cookie コピー失敗")
        print("\n対処:")
        print("1. 通常のChromeでNHK東北に本当にアクセスできるか確認")
        print("2. 再度このスクリプトを実行")

    print("="*60)

if __name__ == '__main__':
    main()
