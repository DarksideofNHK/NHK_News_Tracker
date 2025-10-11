#!/usr/bin/env python3
"""
Remote Debugging経由でChromeに接続してテスト

前提条件:
1. Chromeが --remote-debugging-port=9222 で起動済み
2. または、start_chrome_debug.sh を実行済み
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import requests

def check_chrome_debug_port():
    """Remote Debugging Portが有効か確認"""
    try:
        response = requests.get('http://localhost:9222/json', timeout=5)
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, None
    except Exception as e:
        return False, None

def test_with_remote_debug():
    """Remote Debugging経由でテスト"""
    print("="*60)
    print("Remote Debugging経由テスト")
    print("="*60)

    # Remote Debugging Port確認
    print("\n1. Remote Debugging Port確認中...")
    is_running, debug_info = check_chrome_debug_port()

    if not is_running:
        print("\n❌ Chromeが Remote Debugging モードで起動していません")
        print("\n起動方法:")
        print("  bash start_chrome_debug.sh")
        print("\nまたは手動起動:")
        print('  /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome \\')
        print('    --remote-debugging-port=9222 \\')
        print('    --user-data-dir="$HOME/Library/Application Support/Google/Chrome" \\')
        print('    --profile-directory="Default" &')
        return False

    print("✅ Remote Debugging Port有効")
    print(f"   接続可能なタブ数: {len(debug_info)}")

    # Chromeオプション
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "localhost:9222")

    print("\n2. Seleniumから接続中...")

    try:
        driver = webdriver.Chrome(options=chrome_options)

        # 現在のURL確認
        print(f"   現在のURL: {driver.current_url}")

        # テストURL（NHK東北）
        test_url = 'https://news.web.nhk/tohoku-news/news_all_search.xml'

        print(f"\n3. アクセス中: {test_url}")
        driver.get(test_url)

        # ページ読み込み待機
        time.sleep(5)

        # コンテンツ取得
        content = driver.page_source

        print(f"\nコンテンツサイズ: {len(content):,}文字")
        print(f"\n先頭500文字:")
        print("-" * 60)
        print(content[:500])
        print("-" * 60)

        # 結果判定
        if 'JWT token' in content or '"error"' in content:
            print("\n❌ 失敗: JWT認証エラー")
            print("\n対処:")
            print("1. 通常のChromeで https://news.web.nhk/tohoku-news/news_all_search.xml を開く")
            print("2. XMLが正常に表示されることを確認")
            print("3. 再度このスクリプトを実行")
            success = False

        elif '<?xml' in content and '<search' in content:
            record_count = content.count('<record>')
            print(f"\n✅ 成功: {record_count}件の記事を検出")
            print("\nRemote Debugging経由で認証情報が使えました！")
            success = True

        else:
            print("\n⚠️  不明な応答")
            success = False

        # 注意: driver.quit() は呼ばない（Chromeを閉じてしまうため）
        print("\n注意: Chromeは開いたままです（意図的）")

        return success

    except Exception as e:
        print(f"\n❌ エラー: {e}")
        return False

def main():
    """メイン実行"""
    success = test_with_remote_debug()

    print("\n" + "="*60)
    if success:
        print("✅ テスト成功！")
        print("\n次のステップ:")
        print("1. scraper_hybrid.py をRemote Debugging使用に変更")
        print("2. python test_hybrid.py で7ソース全部テスト")
        print("3. python main_hybrid.py で本番実行")
        print("\nRemote Debuggingの利点:")
        print("- Chromeを閉じる必要なし")
        print("- 通常のブラウジングと並行可能")
        print("- 1時間ごとの自動実行が可能")
    else:
        print("❌ テスト失敗")

    print("="*60)

if __name__ == '__main__':
    main()
