#!/usr/bin/env python3
"""
コピーしたCookieでNHK東北にアクセステスト
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

        print(f"コンテンツサイズ: {len(content):,}文字")
        print(f"\n先頭500文字:")
        print("-" * 60)
        print(content[:500])
        print("-" * 60)

        # 結果判定
        if 'JWT token' in content or '"error"' in content:
            print("\n❌ JWT認証エラー")
            print("\n原因:")
            print("  Cookieが正しくコピーされていないか、")
            print("  Cookieだけでは不十分な可能性があります")
            success = False

        elif '<?xml' in content and '<search' in content:
            record_count = content.count('<record>')
            print(f"\n✅ 成功: {record_count}件の記事を検出")
            print("\nCookieファイルのコピーが成功しました！")
            success = True

        else:
            print("\n⚠️  不明な応答")
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
    print("# コピーしたCookieのテスト")
    print("#"*60 + "\n")

    success = test_with_copied_cookies()

    print("\n" + "="*60)
    if success:
        print("✅ 完全成功！")
        print("\n専用プロファイルでNHK東北にアクセスできました！")
        print("\n次のステップ:")
        print("1. python test_hybrid.py で7ソース全部テスト")
        print("2. python main_hybrid.py で本番実行")
        print("\n🎉 東北ニュース完全自動化達成！")
    else:
        print("❌ 失敗")
        print("\nCookieファイルだけでは不十分かもしれません。")
    print("="*60)
