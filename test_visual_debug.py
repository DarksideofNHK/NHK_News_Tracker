#!/usr/bin/env python3
"""
NHK東北アクセステスト（画面表示版）

ヘッドレスモードをオフにして、実際に何が起きているかを確認
"""
import undetected_chromedriver as uc
import time
import os

def test_visual():
    """画面表示でテスト"""
    print("="*60)
    print("NHK東北アクセステスト（画面表示版）")
    print("="*60)

    profile_dir = os.path.expanduser('~/nhk_scraper_chrome_profile')

    print(f"\n専用プロファイル: {profile_dir}")
    print("\nChrome起動中（画面表示モード）...")
    print("\n⚠️  注意:")
    print("1. Chromeウィンドウが開きます")
    print("2. 画面を見て何が起きているかを確認してください")
    print("3. 同意ダイアログが表示されたらOKをクリック")
    print("4. その後、XMLが表示されるかを確認")
    print("\n準備ができたらEnterキーを押してください...")
    input()

    try:
        # undetected-chromedriver で起動（ヘッドレスモードOFF）
        options = uc.ChromeOptions()
        options.add_argument(f'--user-data-dir={profile_dir}')
        options.add_argument('--profile-directory=Default')
        # ヘッドレスモードをオフ（画面表示）

        driver = uc.Chrome(options=options, use_subprocess=True)

        # ステップ1: NHK news.web.nhk のトップページ
        print("\n" + "─"*60)
        print("ステップ1: NHK news.web.nhk のトップページ")
        print("─"*60)
        print("\nhttps://news.web.nhk/ を開きます...")

        driver.get('https://news.web.nhk/')

        print("\n⚠️  ブラウザを確認:")
        print("1. 同意ダイアログが表示されていますか？")
        print("2. 表示されている場合は「OK」をクリック")
        print("3. 表示されていない場合はそのままEnter")
        print("\n確認後、Enterキーを押してください...")
        input()

        # ステップ2: NHK東北のXMLフィードに直接アクセス
        print("\n" + "─"*60)
        print("ステップ2: NHK東北のXMLフィード")
        print("─"*60)

        test_url = 'https://news.web.nhk/tohoku-news/news_all_search.xml'

        print(f"\n{test_url} を開きます...")
        driver.get(test_url)

        print("\n⚠️  ブラウザを確認:")
        print("1. XMLが表示されていますか？")
        print("2. エラーページが表示されていますか？")
        print("3. 同意ダイアログが表示されていますか？")
        print("\n画面を確認してください（30秒待機）...")

        # 30秒待機して、ユーザーが画面を確認できるようにする
        for i in range(30, 0, -1):
            print(f"\r残り {i}秒... ", end='', flush=True)
            time.sleep(1)
        print()

        # コンテンツを取得
        content = driver.page_source

        print(f"\nコンテンツサイズ: {len(content):,}文字")
        print(f"\n先頭1000文字:")
        print("-" * 60)
        print(content[:1000])
        print("-" * 60)

        print(f"\n末尾1000文字:")
        print("-" * 60)
        print(content[-1000:])
        print("-" * 60)

        # 詳細チェック
        print("\n" + "="*60)
        print("詳細チェック")
        print("="*60)

        checks = {
            "<?xml": "XMLヘッダー",
            "<search": "searchタグ",
            "<record>": "recordタグ",
            "JWT token": "JWT認証エラー",
            '"error"': "エラーメッセージ",
            "同意": "同意ダイアログ",
            "利用規約": "利用規約",
        }

        for keyword, description in checks.items():
            if keyword in content:
                count = content.count(keyword)
                print(f"✅ {description} ({keyword}): {count}回出現")
            else:
                print(f"❌ {description} ({keyword}): 見つかりません")

        # 結果判定
        print("\n" + "="*60)
        if '<?xml' in content and '<search' in content:
            record_count = content.count('<record>')
            print(f"✅ 成功: {record_count}件の記事を検出")
            success = True
        elif 'JWT token' in content or '"error"' in content:
            print("❌ JWT認証エラー")
            success = False
        else:
            print("⚠️  不明な応答")
            success = False

        print("="*60)

        print("\nブラウザを閉じるまで30秒待機します...")
        print("（画面をスクリーンショットするなどしてください）")
        time.sleep(30)

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
    print("# NHK東北アクセステスト（画面表示版）")
    print("# 実際に何が起きているかを確認します")
    print("#"*60)

    success = test_visual()

    print("\n" + "="*60)
    if success:
        print("✅ 成功！")
        print("\n次のステップ:")
        print("1. python test_tohoku_only.py でヘッドレステスト")
        print("2. ./run.sh で完全パイプライン実行")
    else:
        print("❌ 失敗")
        print("\n画面で確認したこと:")
        print("1. どのようなページが表示されましたか？")
        print("2. 同意ダイアログは表示されましたか？")
        print("3. エラーメッセージは表示されましたか？")

    print("="*60)

if __name__ == '__main__':
    main()
