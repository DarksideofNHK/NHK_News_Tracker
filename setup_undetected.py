#!/usr/bin/env python3
"""
NHK東北専用プロファイル作成（undetected-chromedriver使用）

undetected-chromedriverはSeleniumの検出を回避します
→ Googleログインが可能になります
"""
import undetected_chromedriver as uc
import time
import os

def setup_undetected():
    """undetected-chromedriverでセットアップ"""
    print("="*60)
    print("NHK東北専用プロファイル作成（検出回避版）")
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
    print("\n1. Chromeウィンドウが開きます（検出回避モード）")
    print("2. Googleログインページが表示されます")
    print("3. **Googleアカウントにログインしてください**")
    print("4. ログイン完了後、ターミナルでEnterキーを押してください")
    print("\n準備ができたらEnterキーを押してください...")
    input()

    print("\nChrome起動中（検出回避モード）...")

    try:
        # undetected-chromedriver オプション
        options = uc.ChromeOptions()
        options.add_argument(f'--user-data-dir={profile_dir}')
        options.add_argument('--profile-directory=Default')

        # undetected-chromedriver で起動
        driver = uc.Chrome(options=options, use_subprocess=True)

        # ステップ1: NHK news.web.nhk の同意
        print("\n" + "─"*60)
        print("ステップ1: NHK news.web.nhk の同意（最重要！）")
        print("─"*60)
        print("\nNHK news.web.nhk のトップページを開きます...")

        driver.get('https://news.web.nhk/')

        print("\n⚠️  最重要:")
        print("1. ブラウザに同意ダイアログが表示されたら「OK」をクリック")
        print("2. この同意情報がCookieに保存されます")
        print("3. 同意完了後、Enterキーを押してください")
        print("\n同意完了後、Enterキーを押してください...")
        input()

        # ステップ2: Googleログイン（必要に応じて）
        print("\n" + "─"*60)
        print("ステップ2: Googleログイン（必要に応じて）")
        print("─"*60)
        print("\nGoogleログインページを開きます...")

        driver.get('https://accounts.google.com/signin')

        print("\n⚠️  重要:")
        print("1. Googleアカウントにログインしてください")
        print("2. 今回は「このブラウザは安全でない」エラーが出ないはずです")
        print("3. ログイン完了後、Enterキーを押してください")
        print("   （既にログイン済みの場合はそのままEnter）")
        print("\nログイン完了後、Enterキーを押してください...")
        input()

        # ステップ3: NHK東北にアクセス
        print("\n" + "─"*60)
        print("ステップ3: NHK東北にアクセス")
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
            print("\n⚠️  まだJWT認証エラー")
            print("\n手動確認:")
            print("ブラウザで https://news.web.nhk/tohoku-news/news_all_search.xml に")
            print("手動でアクセスしてみてください（30秒待機）")
            time.sleep(30)

            # 再度取得
            content = driver.page_source
            if '<?xml' in content and '<search' in content:
                record_count = content.count('<record>')
                print(f"\n✅ 成功: {record_count}件の記事を検出")
                success = True
            else:
                print("\n❌ まだエラーです")
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
        import traceback
        traceback.print_exc()
        return False, profile_dir

def main():
    """メイン実行"""
    print("\n" + "#"*60)
    print("# NHK東北専用プロファイル作成")
    print("# 重要: news.web.nhk の同意が必須！")
    print("#"*60)
    print("\n【重要な発見】")
    print("NHK東北のXMLフィードにアクセスするには:")
    print("1. https://news.web.nhk/ で同意ダイアログをOK")
    print("2. この同意情報がCookieに保存される")
    print("3. その後、XMLフィードにアクセス可能になる")
    print("#"*60)

    success, profile_dir = setup_undetected()

    print("\n" + "="*60)
    if success:
        print("✅ セットアップ成功！")
        print(f"\nプロファイル: {profile_dir}")
        print("\n次のステップ:")
        print("1. python test_dedicated_profile.py でテスト")
        print("2. scraper_hybrid.py を undetected-chromedriver 使用に変更")
        print("3. python test_hybrid.py で7ソース全部テスト")
        print("\n🎉 完全自動化達成！")
    else:
        print("❌ セットアップ失敗")
        print("\nトラブルシューティング:")
        print("1. Googleログインができましたか？")
        print("2. 再度このスクリプトを実行してください")

    print("="*60)

if __name__ == '__main__':
    main()
