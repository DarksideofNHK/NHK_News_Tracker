#!/usr/bin/env python3
"""
コピーしたCookieでNHK東北にアクセステスト（詳細版）
"""
import undetected_chromedriver as uc
import time
import os

def test_with_copied_cookies():
    """コピーしたCookieでテスト"""
    print("="*60)
    print("テスト: コピーしたCookieでNHK東北にアクセス")
    print("="*60)

    profile_dir = os.path.expanduser('~/nhk_scraper_chrome_profile')

    print(f"\n専用プロファイル: {profile_dir}")
    print("\nChrome起動中（ヘッドレスモード）...")

    try:
        # undetected-chromedriver で起動
        options = uc.ChromeOptions()
        options.add_argument(f'--user-data-dir={profile_dir}')
        options.add_argument('--profile-directory=Default')
        options.add_argument('--headless=new')  # 新しいヘッドレスモード

        driver = uc.Chrome(options=options, use_subprocess=True)

        # NHK東北にアクセス
        test_url = 'https://news.web.nhk/tohoku-news/news_all_search.xml'

        print(f"アクセス中: {test_url}\n")
        driver.get(test_url)
        time.sleep(5)

        content = driver.page_source

        print(f"コンテンツサイズ: {len(content):,}文字\n")

        # JWTエラーチェック
        if 'JWT token' in content or '"error"' in content:
            print("❌ JWT認証エラー")
            print("\n先頭1000文字:")
            print("-" * 60)
            print(content[:1000])
            print("-" * 60)
            driver.quit()
            return False

        # XMLコンテンツの検出（HTMLラッパー内にある場合も含む）
        if '<search' in content and '<record>' in content:
            record_count = content.count('<record>')
            print(f"✅ 成功: {record_count}件の記事を検出")

            # <search>タグの位置を探す
            search_pos = content.find('<search')
            if search_pos > 0:
                print(f"\n<search>タグの位置: {search_pos}文字目")
                print("\n<search>タグ付近（200文字）:")
                print("-" * 60)
                print(content[max(0, search_pos-100):search_pos+100])
                print("-" * 60)

            # 最初の<record>を表示
            record_pos = content.find('<record>')
            if record_pos > 0:
                print("\n最初の<record>（500文字）:")
                print("-" * 60)
                print(content[record_pos:record_pos+500])
                print("-" * 60)

            print("\n✅ Cookieファイルのコピーが成功しました！")
            print("XMLデータは取得できています（HTMLラッパー内）")
            success = True

        elif '<?xml' in content:
            print("✅ XMLデータを検出")
            record_count = content.count('<record>')
            print(f"記事数: {record_count}件")
            print("\n先頭1000文字:")
            print("-" * 60)
            print(content[:1000])
            print("-" * 60)
            success = True

        else:
            print("⚠️  不明な応答")
            print("\n先頭1000文字:")
            print("-" * 60)
            print(content[:1000])
            print("-" * 60)

            # 末尾もチェック
            print("\n末尾1000文字:")
            print("-" * 60)
            print(content[-1000:])
            print("-" * 60)
            success = False

        driver.quit()
        return success

    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("\n" + "#"*60)
    print("# コピーしたCookieのテスト（詳細版）")
    print("#"*60 + "\n")

    success = test_with_copied_cookies()

    print("\n" + "="*60)
    if success:
        print("✅ 完全成功！")
        print("\n専用プロファイルでNHK東北にアクセスできました！")
        print("\n次のステップ:")
        print("1. scraper_hybrid.py を調整（HTMLラッパー対応）")
        print("2. python test_hybrid.py で7ソース全部テスト")
        print("3. python main_hybrid.py で本番実行")
        print("\n🎉 東北ニュース完全自動化達成！")
    else:
        print("❌ 失敗")
        print("\nCookieファイルだけでは不十分かもしれません。")
    print("="*60)
