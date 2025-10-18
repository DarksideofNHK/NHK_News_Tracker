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

def setup_with_auto_consent(auto_mode=False):
    """同意ダイアログを自動クリック

    Args:
        auto_mode: True の場合、対話プロンプトをスキップ
    """
    print("="*60)
    print("NHK東北専用プロファイル作成（自動同意版）")
    print("="*60)

    profile_dir = os.path.expanduser('~/nhk_scraper_chrome_profile')

    # 既存プロファイルの確認（削除はしない - 上書きモード）
    if os.path.exists(profile_dir):
        if not auto_mode:
            print(f"\n既存プロファイルを使用します: {profile_dir}")
            print("（既存の認証情報を上書きします）")
    else:
        print(f"\n新規プロファイル作成: {profile_dir}")

    if not auto_mode:
        print("\n" + "="*60)
        print("手順:")
        print("="*60)
        print("\n1. Chromeウィンドウが開きます")
        print("2. 同意ダイアログが表示されたら2段階の自動クリックを試みます")
        print("   - チェックボックスにチェック")
        print("   - 「次へ」ボタンをクリック")
        print("   - 「サービスの利用を開始する」ボタンをクリック")
        print("3. 自動クリックが失敗したら、手動で上記の操作を実行してください")
        print("\n準備ができたらEnterキーを押してください...")
        input()
    else:
        print("\n自動モード: 対話プロンプトをスキップします")

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

        # 2段階の同意ダイアログの自動クリック
        print("\n【2段階の同意操作を実行します】")
        print("1. チェックボックス「内容について確認しました」をチェック")
        print("2. 「次へ」ボタンをクリック")
        print("3. 「サービスの利用を開始する」ボタンをクリック")

        consent_clicked = False

        try:
            # ステップ1: チェックボックスを探してクリック
            print("\n[ステップ1] チェックボックスを探しています...")
            checkbox_found = False

            try:
                # パターン1: input[type="checkbox"]を探す
                checkboxes = driver.find_elements(By.XPATH, "//input[@type='checkbox']")
                for checkbox in checkboxes:
                    if not checkbox.is_selected():
                        checkbox.click()
                        print("✅ チェックボックスをクリックしました")
                        checkbox_found = True
                        time.sleep(2)
                        break
            except Exception as e:
                print(f"  チェックボックス検索エラー: {e}")

            if not checkbox_found:
                # パターン2: labelに「確認」というテキストを含む要素を探してクリック
                try:
                    labels = driver.find_elements(By.XPATH, "//label[contains(text(), '確認')]")
                    if labels:
                        labels[0].click()
                        print("✅ チェックボックスのlabelをクリックしました")
                        checkbox_found = True
                        time.sleep(2)
                except Exception as e:
                    print(f"  label検索エラー: {e}")

            # ステップ2: 「次へ」ボタンをクリック
            print("\n[ステップ2] 「次へ」ボタンを探しています...")
            next_button_clicked = False

            next_button_texts = ['次へ', '次', 'Next', '次のページ']
            for text in next_button_texts:
                try:
                    # buttonタグ
                    button = driver.find_element(By.XPATH, f"//button[contains(text(), '{text}')]")
                    button.click()
                    print(f"✅ 「{text}」ボタンをクリックしました")
                    next_button_clicked = True
                    time.sleep(3)  # 次のページの読み込みを待つ
                    break
                except:
                    try:
                        # aタグ
                        link = driver.find_element(By.XPATH, f"//a[contains(text(), '{text}')]")
                        link.click()
                        print(f"✅ 「{text}」リンクをクリックしました")
                        next_button_clicked = True
                        time.sleep(3)
                        break
                    except:
                        pass

            # ステップ3: 「サービスの利用を開始する」ボタンをクリック
            if next_button_clicked:
                print("\n[ステップ3] 「サービスの利用を開始する」ボタンを探しています...")

                confirm_button_texts = [
                    'サービスの利用を開始する',
                    'サービスの利用を開始',
                    '利用を開始する',
                    '利用を開始',
                    '開始する',
                    '開始'
                ]

                for text in confirm_button_texts:
                    try:
                        # buttonタグ
                        button = driver.find_element(By.XPATH, f"//button[contains(text(), '{text}')]")
                        button.click()
                        print(f"✅ 「{text}」ボタンをクリックしました")
                        consent_clicked = True
                        time.sleep(3)
                        break
                    except:
                        try:
                            # aタグ
                            link = driver.find_element(By.XPATH, f"//a[contains(text(), '{text}')]")
                            link.click()
                            print(f"✅ 「{text}」リンクをクリックしました")
                            consent_clicked = True
                            time.sleep(3)
                            break
                        except:
                            pass

        except Exception as e:
            print(f"\n自動クリック処理エラー: {e}")
            import traceback
            traceback.print_exc()

        if not consent_clicked:
            print("\n⚠️  自動クリックできませんでした")
            if not auto_mode:
                print("\n手動操作が必要です:")
                print("1. 「内容について確認しました」チェックボックスにチェック")
                print("2. 「次へ」ボタンをクリック")
                print("3. 「サービスの利用を開始する」ボタンをクリック")
                print("4. 表示されていない場合はそのままEnter")
                print("\n確認後、Enterキーを押してください...")
                input()
            else:
                print("\n自動モード: 手動操作はスキップされました")
                print("5秒待機後、次のステップに進みます...")
                time.sleep(5)
        else:
            print("\n✅ 2段階の同意操作が完了しました！")
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

        # 結果判定（修正版: <?xmlは不要、<search>と<record>があればOK）
        print("\n" + "="*60)
        if '<search' in content and '<record>' in content:
            record_count = content.count('<record>')
            print(f"✅ 成功: {record_count}件の記事を検出")
            print("\nJWT tokenが正しく保存されました！")
            print("\n【注意】ChromeがXMLをHTMLでラップするため、<?xmlヘッダーは表示されませんが、")
            print("     <search>と<record>タグが確認できれば正常に動作しています。")
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

            if '<search' in content and '<record>' in content:
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
