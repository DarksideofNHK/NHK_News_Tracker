#!/usr/bin/env python3
"""
ChromeのCookieファイルを直接コピー

Chromeを閉じる必要なし！
"""
import shutil
import os
from pathlib import Path

def copy_cookie_files():
    """ChromeのCookieファイルをコピー"""
    print("="*60)
    print("ChromeのCookieファイルを直接コピー")
    print("="*60)

    # 通常のChromeプロファイル
    main_profile = Path.home() / "Library/Application Support/Google/Chrome/Default"

    # 専用プロファイル
    dedicated_profile = Path.home() / "nhk_scraper_chrome_profile/Default"

    print(f"\nコピー元: {main_profile}")
    print(f"コピー先: {dedicated_profile}")

    if not main_profile.exists():
        print(f"\n❌ 通常のChromeプロファイルが見つかりません")
        return False

    if not dedicated_profile.exists():
        print(f"\n専用プロファイルを作成します...")
        dedicated_profile.mkdir(parents=True, exist_ok=True)

    # コピーするファイル
    files_to_copy = [
        'Cookies',
        'Cookies-journal',
        'Network/Cookies',
        'Network/Cookies-journal',
    ]

    print(f"\n" + "─"*60)
    print("Cookieファイルをコピー中...")
    print("─"*60)

    copied_count = 0

    for file_name in files_to_copy:
        src = main_profile / file_name
        dst = dedicated_profile / file_name

        if src.exists():
            try:
                # コピー先のディレクトリを作成
                dst.parent.mkdir(parents=True, exist_ok=True)

                # ファイルコピー
                shutil.copy2(src, dst)

                file_size = src.stat().st_size
                print(f"✅ {file_name} ({file_size:,}バイト)")
                copied_count += 1

            except Exception as e:
                print(f"⚠️  {file_name}: {e}")
        else:
            print(f"⚠️  {file_name}: ファイルが見つかりません")

    print(f"\n{copied_count}個のファイルをコピーしました")

    if copied_count > 0:
        print("\n✅ Cookieファイルのコピー完了！")
        return True
    else:
        print("\n❌ Cookieファイルをコピーできませんでした")
        return False

def test_with_copied_cookies():
    """コピーしたCookieでテスト"""
    print("\n" + "="*60)
    print("テスト: コピーしたCookieでNHK東北にアクセス")
    print("="*60)

    import undetected_chromedriver as uc
    import time

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

def main():
    """メイン実行"""
    print("\n" + "#"*60)
    print("# ChromeのCookieファイルを直接コピー")
    print("# Chromeを閉じる必要なし！")
    print("#"*60)
    print("\nこの方法は:")
    print("1. 通常のChromeプロファイルのCookieファイルを読み取り")
    print("2. 専用プロファイルにコピー")
    print("3. Chromeを閉じる必要なし")
    print("\n" + "#"*60)

    # Cookieファイルコピー
    if not copy_cookie_files():
        print("\n❌ 失敗")
        return

    # テスト実行
    print("\n⚠️  注意:")
    print("Cookieファイルは暗号化されている可能性があります。")
    print("同じマシン、同じユーザーなら復号化できるはずです。")
    print("\n準備ができたらEnterキーを押してください...")
    input()

    success = test_with_copied_cookies()

    print("\n" + "="*60)
    if success:
        print("✅ 完全成功！")
        print("\n専用プロファイルでNHK東北にアクセスできました！")
        print("\n次のステップ:")
        print("1. python test_dedicated_profile.py でヘッドレステスト")
        print("2. scraper_hybrid.py を undetected-chromedriver 使用に変更")
        print("3. python test_hybrid.py で7ソース全部テスト")
        print("\n🎉 東北ニュース完全自動化達成！")
    else:
        print("❌ 失敗")
        print("\nCookieファイルだけでは不十分かもしれません。")
        print("次の対策を試します...")

    print("="*60)

if __name__ == '__main__':
    main()
