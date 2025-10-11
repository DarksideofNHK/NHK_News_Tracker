#!/usr/bin/env python3
"""
保存されたプロファイルでNHK東北にアクセステスト

ヘッドレスモードで動作確認
"""
import undetected_chromedriver as uc
import time
import os

def test_headless():
    """ヘッドレスモードでテスト"""
    print("="*60)
    print("保存されたプロファイルでテスト（ヘッドレス）")
    print("="*60)

    profile_dir = os.path.expanduser('~/nhk_scraper_chrome_profile')

    if not os.path.exists(profile_dir):
        print(f"\n❌ プロファイルが見つかりません: {profile_dir}")
        print("\n先に setup_consent_auto.py を実行してください")
        return False

    print(f"\nプロファイル: {profile_dir}")
    print("\nChrome起動中（ヘッドレスモード）...")

    try:
        # ヘッドレスモードで起動
        options = uc.ChromeOptions()
        options.add_argument(f'--user-data-dir={profile_dir}')
        options.add_argument('--profile-directory=Default')
        options.add_argument('--headless=new')  # ヘッドレスモード

        driver = uc.Chrome(options=options, use_subprocess=True)

        # NHK東北にアクセス
        test_url = 'https://news.web.nhk/tohoku-news/news_all_search.xml'

        print(f"\nアクセス中: {test_url}")
        driver.get(test_url)
        time.sleep(5)

        content = driver.page_source

        print(f"\nコンテンツサイズ: {len(content):,}文字")

        # 詳細チェック
        print("\n" + "="*60)
        print("詳細チェック")
        print("="*60)

        # 修正版のチェック（<?xmlは不要）
        checks = {
            "<search": "searchタグ",
            "<record>": "recordタグ",
            "<title>": "titleタグ",
            "<detail>": "detailタグ",
            "JWT token": "JWT認証エラー",
            '"error"': "エラーメッセージ",
        }

        for keyword, description in checks.items():
            if keyword in content:
                count = content.count(keyword)
                print(f"✅ {description} ({keyword}): {count}回出現")
            else:
                print(f"❌ {description} ({keyword}): 見つかりません")

        # 結果判定（修正版）
        print("\n" + "="*60)
        if '<search' in content and '<record>' in content:
            record_count = content.count('<record>')
            print(f"✅ 成功: {record_count}件の記事を検出")
            print("\nJWT tokenが正しく保存されています！")
            print("ヘッドレスモードで正常に動作します。")
            success = True
        elif 'JWT token' in content or '"error"' in content:
            print("❌ JWT認証エラー")
            print("\nプロファイルに認証情報が保存されていません")
            success = False
        else:
            print("⚠️  不明な応答")
            print("\n先頭500文字:")
            print("-" * 60)
            print(content[:500])
            print("-" * 60)
            success = False

        print("="*60)

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
    print("# 保存されたプロファイルで動作確認")
    print("# ヘッドレスモードテスト")
    print("#"*60)

    success = test_headless()

    print("\n" + "="*60)
    if success:
        print("✅ テスト成功！")
        print("\nプロファイルが正しく保存されています。")
        print("ヘッドレスモードで自動実行が可能です。")
        print("\n次のステップ:")
        print("1. python test_hybrid.py で7ソース全体テスト")
        print("2. ./run.sh で完全パイプライン実行")
        print("\n🎉 NHK東北完全自動化達成！")
    else:
        print("❌ テスト失敗")
        print("\n対策:")
        print("1. python setup_consent_auto.py を再実行")
        print("2. ブラウザで同意ダイアログをOK")
        print("3. このスクリプトを再度実行")

    print("="*60)

if __name__ == '__main__':
    main()
