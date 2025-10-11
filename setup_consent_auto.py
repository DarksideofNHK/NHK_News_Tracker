#!/usr/bin/env python3
"""
NHK東北専用プロファイル作成（同意ダイアログ自動クリック版）

重要: 同意ダイアログを確実にクリックしてJWT tokenを取得
"""
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import shutil

def setup_with_auto_consent():
    """同意ダイアログを自動クリック"""
    print("="*60)
    print("NHK東北専用プロファイル作成（自動同意版）")
    print("="*60)

    profile_dir = os.path.expanduser('~/nhk_scraper_chrome_profile')

    # 既存プロファイルを削除
    if os.path.exists(profile_dir):
        print(f"\n既存プロファイルを削除します: {profile_dir}")
        shutil.rmtree(profile_dir)
        print("✅ 削除完了")

    print(f"\n新規プロファイル: {profile_dir}")

    print("\n" + "="*60)
    print("手順:")
    print("="*60)
    print("\n1. Chromeウィンドウが開きます")
    print("2. 同意ダイアログが表示されたら自動でクリックを試みます")
    print("3. 自動クリックが失敗したら、手動でOKをクリックしてください")
    print("\n準備ができたらEnterキーを押してください...")
    input()

    driver = None

    try:
        # Chrome起動（画面表示モード - 重要！）
        print("\nChrome起動中（画面表示モード）...")

        options = uc.ChromeOptions()
        options.add_argument(f'--user-data-dir={profile_dir}')
        options.add_argument('--profile-directory=Default')
        # ヘッドレスモードOFF - 重要！

        driver = uc.Chrome(options=options, use_subprocess=True)

        # ステップ1: NHK news.web.nhk のトップページ
        print("\n" + "─"*60)
        print("ステップ1: NHK news.web.nhk のトップページ")
        print("─"*60)

        print("\nhttps://news.web.nhk/ にアクセスします...")
        driver.get('https://news.web.nhk/')

        print("\n同意ダイアログを探しています（10秒待機）...")
        time.sleep(10)

        # 同意ダイアログの自動クリックを試みる
        print("\n同意ダイアログの自動クリックを試みます...")

        consent_clicked = False

        # パターン1: ボタンのテキストで探す
        try:
            # 一般的な同意ボタンのテキスト
            button_texts = ['同意する', 'OK', '同意', 'はい', '了解', 'Accept', 'Agree']

            for text in button_texts:
                try:
                    button = driver.find_element(By.XPATH, f"//button[contains(text(), '{text}')]")
                    button.click()
                    print(f"✅ ボタンをクリックしました: '{text}'")
                    consent_clicked = True
                    break
                except:
                    pass

            if not consent_clicked:
                # aタグも試す
                for text in button_texts:
                    try:
                        link = driver.find_element(By.XPATH, f"//a[contains(text(), '{text}')]")
                        link.click()
                        print(f"✅ リンクをクリックしました: '{text}'")
                        consent_clicked = True
                        break
                    except:
                        pass

        except Exception as e:
            print(f"自動クリック失敗: {e}")

        if not consent_clicked:
            print("\n⚠️  自動クリックできませんでした")
            print("\n手動操作が必要です:")
            print("1. ブラウザに同意ダイアログが表示されている場合は「OK」をクリック")
            print("2. 表示されていない場合はそのままEnter")
            print("\n確認後、Enterキーを押してください...")
            input()
        else:
            print("\n✅ 同意ダイアログをクリックしました")
            print("\n5秒待機...")
            time.sleep(5)

        # ステップ2: NHK東北のXMLフィードにアクセス
        print("\n" + "─"*60)
        print("ステップ2: NHK東北のXMLフィード")
        print("─"*60)

        test_url = 'https://news.web.nhk/tohoku-news/news_all_search.xml'

        print(f"\n{test_url} にアクセスします...")
        driver.get(test_url)

        print("\n10秒待機...")
        time.sleep(10)

        # コンテンツを取得
        content = driver.page_source

        print(f"\nコンテンツサイズ: {len(content):,}文字")
        print(f"\n先頭500文字:")
        print("-" * 60)
        print(content[:500])
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
            print("\nJWT tokenが正しく保存されました！")
            success = True
        elif 'JWT token' in content or '"error"' in content:
            print("❌ JWT認証エラー")
            print("\n⚠️  同意ダイアログが正しくクリックされなかった可能性があります")
            print("\nブラウザを確認してください（30秒待機）...")
            print("必要であれば、手動で同意ダイアログをクリックしてください")
            time.sleep(30)
            success = False
        else:
            print("⚠️  不明な応答")
            success = False

        print("="*60)

        if not success:
            # 再度トップページにアクセスして、手動で同意を求める
            print("\n" + "─"*60)
            print("再試行: トップページに戻ります")
            print("─"*60)

            driver.get('https://news.web.nhk/')
            print("\n同意ダイアログが表示されている場合は、手動でOKをクリックしてください")
            print("\n完了後、Enterキーを押してください...")
            input()

            # 再度XMLにアクセス
            print(f"\n再度 {test_url} にアクセスします...")
            driver.get(test_url)
            time.sleep(10)

            content = driver.page_source

            if '<?xml' in content and '<search' in content:
                record_count = content.count('<record>')
                print(f"✅ 再試行成功: {record_count}件の記事を検出")
                success = True
            else:
                print("❌ 再試行も失敗")
                success = False

        print("\nブラウザを閉じるまで10秒待機します...")
        time.sleep(10)

        if driver:
            driver.quit()

        return success, profile_dir

    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()

        if driver:
            driver.quit()

        return False, profile_dir

def main():
    """メイン実行"""
    print("\n" + "#"*60)
    print("# NHK東北専用プロファイル作成")
    print("# 同意ダイアログ自動クリック版")
    print("#"*60)
    print("\n【重要】")
    print("同意ダイアログをクリックすることで、JWT tokenが保存されます")
    print("これがないと、NHK東北のXMLフィードにアクセスできません")
    print("#"*60)

    success, profile_dir = setup_with_auto_consent()

    print("\n" + "="*60)
    if success:
        print("✅ セットアップ成功！")
        print(f"\nプロファイル: {profile_dir}")
        print("\n次のステップ:")
        print("1. python test_tohoku_only.py でテスト")
        print("2. python test_hybrid.py で7ソース全体テスト")
        print("3. ./run.sh で完全パイプライン実行")
        print("\n🎉 NHK東北完全自動化達成！")
    else:
        print("❌ セットアップ失敗")
        print("\nトラブルシューティング:")
        print("1. ブラウザで同意ダイアログをOKしましたか？")
        print("2. XMLフィードが表示されましたか？")
        print("3. 再度このスクリプトを実行してください")

    print("="*60)

if __name__ == '__main__':
    main()
