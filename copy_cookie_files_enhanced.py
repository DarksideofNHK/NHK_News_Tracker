#!/usr/bin/env python3
"""
ChromeのCookie + LocalStorage + SessionStorageを完全コピー

Chromeを閉じる必要なし！
"""
import shutil
import os
from pathlib import Path

def copy_all_auth_data():
    """Chrome認証データを完全コピー"""
    print("="*60)
    print("Chrome認証データを完全コピー")
    print("Cookie + LocalStorage + SessionStorage + その他")
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

    print(f"\n" + "─"*60)
    print("認証データをコピー中...")
    print("─"*60)

    copied_count = 0

    # 1. Cookieファイル
    print("\n【1. Cookieファイル】")
    cookie_files = [
        'Cookies',
        'Cookies-journal',
        'Network/Cookies',
        'Network/Cookies-journal',
    ]

    for file_name in cookie_files:
        src = main_profile / file_name
        dst = dedicated_profile / file_name

        if src.exists():
            try:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                file_size = src.stat().st_size
                print(f"✅ {file_name} ({file_size:,}バイト)")
                copied_count += 1
            except Exception as e:
                print(f"⚠️  {file_name}: {e}")
        else:
            print(f"⚠️  {file_name}: ファイルが見つかりません")

    # 2. LocalStorage（重要！）
    print("\n【2. LocalStorage】")
    local_storage_src = main_profile / "Local Storage/leveldb"
    local_storage_dst = dedicated_profile / "Local Storage/leveldb"

    if local_storage_src.exists():
        try:
            local_storage_dst.parent.mkdir(parents=True, exist_ok=True)

            # leveldbディレクトリ全体をコピー
            if local_storage_dst.exists():
                shutil.rmtree(local_storage_dst)

            shutil.copytree(local_storage_src, local_storage_dst)

            # ファイル数とサイズを表示
            file_count = sum(1 for _ in local_storage_dst.glob('*'))
            total_size = sum(f.stat().st_size for f in local_storage_dst.glob('*') if f.is_file())

            print(f"✅ Local Storage/leveldb ({file_count}ファイル, {total_size:,}バイト)")
            copied_count += 1
        except Exception as e:
            print(f"⚠️  Local Storage: {e}")
    else:
        print(f"⚠️  Local Storage: ディレクトリが見つかりません")

    # 3. SessionStorage（あれば）
    print("\n【3. SessionStorage】")
    session_storage_src = main_profile / "Session Storage"
    session_storage_dst = dedicated_profile / "Session Storage"

    if session_storage_src.exists():
        try:
            if session_storage_dst.exists():
                shutil.rmtree(session_storage_dst)

            shutil.copytree(session_storage_src, session_storage_dst)

            file_count = sum(1 for _ in session_storage_dst.glob('**/*') if _.is_file())
            print(f"✅ Session Storage ({file_count}ファイル)")
            copied_count += 1
        except Exception as e:
            print(f"⚠️  Session Storage: {e}")
    else:
        print(f"⚠️  Session Storage: ディレクトリが見つかりません（問題なし）")

    # 4. IndexedDB（あれば）
    print("\n【4. IndexedDB】")
    indexeddb_src = main_profile / "IndexedDB"
    indexeddb_dst = dedicated_profile / "IndexedDB"

    if indexeddb_src.exists():
        try:
            if indexeddb_dst.exists():
                shutil.rmtree(indexeddb_dst)

            shutil.copytree(indexeddb_src, indexeddb_dst)

            file_count = sum(1 for _ in indexeddb_dst.glob('**/*') if _.is_file())
            print(f"✅ IndexedDB ({file_count}ファイル)")
            copied_count += 1
        except Exception as e:
            print(f"⚠️  IndexedDB: {e}")
    else:
        print(f"⚠️  IndexedDB: ディレクトリが見つかりません（問題なし）")

    # 5. Preferences（ブラウザ設定）
    print("\n【5. Preferences】")
    prefs_src = main_profile / "Preferences"
    prefs_dst = dedicated_profile / "Preferences"

    if prefs_src.exists():
        try:
            shutil.copy2(prefs_src, prefs_dst)
            file_size = prefs_src.stat().st_size
            print(f"✅ Preferences ({file_size:,}バイト)")
            copied_count += 1
        except Exception as e:
            print(f"⚠️  Preferences: {e}")
    else:
        print(f"⚠️  Preferences: ファイルが見つかりません")

    print(f"\n" + "─"*60)
    print(f"✅ {copied_count}個の項目をコピーしました")
    print("─"*60)

    if copied_count > 0:
        print("\n✅ 認証データのコピー完了！")
        return True
    else:
        print("\n❌ 認証データをコピーできませんでした")
        return False

def test_with_copied_data():
    """コピーしたデータでテスト"""
    print("\n" + "="*60)
    print("テスト: コピーした認証データでNHK東北にアクセス")
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
        options.add_argument('--headless=new')

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
            print("  認証データが正しくコピーされていないか、")
            print("  手動で同意ダイアログをクリックする必要があります")
            success = False

        elif '<?xml' in content and '<search' in content:
            record_count = content.count('<record>')
            print(f"\n✅ 成功: {record_count}件の記事を検出")
            print("\n認証データのコピーが成功しました！")
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
    print("# Chrome認証データを完全コピー")
    print("# Cookie + LocalStorage + SessionStorage + その他")
    print("# Chromeを閉じる必要なし！")
    print("#"*60)
    print("\nこの方法は:")
    print("1. 通常のChromeプロファイルから認証データを読み取り")
    print("2. 専用プロファイルにコピー")
    print("3. Chromeを閉じる必要なし")
    print("\n前提条件:")
    print("✅ https://news.web.nhk/ で同意ダイアログをOK済み")
    print("\n" + "#"*60)

    # 認証データコピー
    if not copy_all_auth_data():
        print("\n❌ 失敗")
        return

    # テスト実行
    print("\n⚠️  注意:")
    print("認証データは暗号化されている可能性があります。")
    print("同じマシン、同じユーザーなら復号化できるはずです。")
    print("\n準備ができたらEnterキーを押してください...")
    input()

    success = test_with_copied_data()

    print("\n" + "="*60)
    if success:
        print("✅ 完全成功！")
        print("\n専用プロファイルでNHK東北にアクセスできました！")
        print("\n次のステップ:")
        print("1. python test_tohoku_only.py でテスト")
        print("2. python test_hybrid.py で7ソース全部テスト")
        print("3. ./run.sh で完全パイプライン実行")
        print("\n🎉 東北ニュース完全自動化達成！")
    else:
        print("❌ 失敗")
        print("\n認証データのコピーだけでは不十分です。")
        print("\n次の対策:")
        print("1. python setup_undetected.py を実行")
        print("2. 手動で同意ダイアログをクリック")
        print("3. これで完全な認証データが専用プロファイルに保存されます")

    print("="*60)

if __name__ == '__main__':
    main()
