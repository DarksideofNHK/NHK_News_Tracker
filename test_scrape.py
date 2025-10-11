#!/usr/bin/env python3
"""
NHK RSS取得テスト - 最小PoC
ローカルPCのIPで403エラーが出ないか確認
"""
import requests
from datetime import datetime

# NHKソース一覧
SOURCES = {
    'NHK東北ニュース': 'https://news.web.nhk/tohoku-news/news_all_search.xml',
    'NHK首都圏ニュース': 'https://news.web.nhk/shutoken-news/news_all_search.xml',
    'NHK関西ニュース': 'https://news.web.nhk/kansai-news/news_all_search.xml',
    'NHK福岡ニュース': 'https://news.web.nhk/fukuoka-news/news_all_search.xml',
}

def test_scrape(name, url):
    """単一ソースの取得テスト"""
    print(f"\n{'='*60}")
    print(f"テスト: {name}")
    print(f"URL: {url}")
    print(f"{'='*60}")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)

        print(f"ステータスコード: {response.status_code}")
        print(f"コンテンツサイズ: {len(response.text):,}文字")
        print(f"エンコーディング: {response.encoding}")

        if response.status_code == 200:
            # 先頭500文字を表示
            print(f"\n先頭500文字:")
            print("-" * 60)
            print(response.text[:500])
            print("-" * 60)

            # <record>タグの数をカウント
            record_count = response.text.count('<record>')
            print(f"\n✅ 成功: {record_count}件の記事を検出")

            return True, response.text
        else:
            print(f"\n❌ 失敗: HTTPエラー {response.status_code}")
            return False, None

    except requests.exceptions.Timeout:
        print(f"\n❌ 失敗: タイムアウト（30秒）")
        return False, None
    except Exception as e:
        print(f"\n❌ 失敗: {type(e).__name__}: {e}")
        return False, None

def main():
    """全ソースのテスト実行"""
    print(f"\n{'#'*60}")
    print(f"# NHK RSS取得テスト - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*60}")

    results = {}

    for name, url in SOURCES.items():
        success, content = test_scrape(name, url)
        results[name] = success

    # 結果サマリー
    print(f"\n{'='*60}")
    print("テスト結果サマリー")
    print(f"{'='*60}")

    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)

    for name, success in results.items():
        status = "✅ 成功" if success else "❌ 失敗"
        print(f"{status}: {name}")

    print(f"\n成功率: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")

    if success_count == total_count:
        print("\n🎉 すべてのソースで取得成功！")
        print("→ Python実装で完全自動化が可能です")
    elif success_count > 0:
        print(f"\n⚠️  {total_count - success_count}個のソースで失敗")
        print("→ 成功したソースはPython実装可能、失敗したソースは要調査")
    else:
        print("\n❌ すべてのソースで失敗")
        print("→ ヘッドレスブラウザ（Playwright/Selenium）の使用を検討")

if __name__ == '__main__':
    main()
