#!/usr/bin/env python3
"""
NHK RSS取得テスト - 正しいURL版
"""
import requests
from datetime import datetime

# 正しいNHK RSSフィードURL
SOURCES = {
    'NHK首都圏ニュース': 'https://www.nhk.or.jp/shutoken-news/news_all_search.xml',
    'NHK福岡ニュース': 'https://www.nhk.or.jp/fukuoka-news/news_all_search.xml',
    'NHK札幌ニュース': 'https://www.nhk.or.jp/sapporo-news/news_all_search.xml',
    'NHK東海ニュース': 'https://www.nhk.or.jp/tokai-news/news_all_search.xml',
    'NHK広島ニュース': 'https://www.nhk.or.jp/hiroshima-news/news_all_search.xml',
    'NHK関西ニュース': 'https://www.nhk.or.jp/kansai-news/news_all_search.xml',
    'NHK東北ニュース': 'https://news.web.nhk/tohoku-news/news_all_search.xml',
}

def test_scrape(name, url):
    """単一ソースの取得テスト"""
    print(f"\n{'='*60}")
    print(f"テスト: {name}")
    print(f"URL: {url}")
    print(f"ドメイン: {'www.nhk.or.jp' if 'www.nhk.or.jp' in url else 'news.web.nhk'}")
    print(f"{'='*60}")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
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
            content = response.text

            # エラーチェック
            if 'JWT token' in content or '"error"' in content[:500]:
                print(f"\n❌ 認証エラー検出")
                print(f"先頭500文字:\n{content[:500]}")
                return False, None

            # XMLチェック
            if '<?xml' in content and '<search' in content:
                # <record>タグの数をカウント
                record_count = content.count('<record>')
                print(f"\n先頭500文字:")
                print("-" * 60)
                print(content[:500])
                print("-" * 60)
                print(f"\n✅ 成功: {record_count}件の記事を検出")
                return True, content
            else:
                print(f"\n⚠️  XML形式が不明")
                print(f"先頭500文字:\n{content[:500]}")
                return False, None
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
    print(f"# NHK RSS取得テスト（正しいURL版）")
    print(f"# {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*60}")

    results = {}
    www_nhk_results = {}
    news_web_results = {}

    for name, url in SOURCES.items():
        success, content = test_scrape(name, url)
        results[name] = success

        # ドメイン別に分類
        if 'www.nhk.or.jp' in url:
            www_nhk_results[name] = success
        else:
            news_web_results[name] = success

    # 結果サマリー
    print(f"\n{'='*60}")
    print("テスト結果サマリー")
    print(f"{'='*60}")

    # ドメイン別サマリー
    print(f"\n【www.nhk.or.jp ドメイン】")
    www_success = sum(1 for v in www_nhk_results.values() if v)
    www_total = len(www_nhk_results)
    for name, success in www_nhk_results.items():
        status = "✅ 成功" if success else "❌ 失敗"
        print(f"{status}: {name}")
    print(f"成功率: {www_success}/{www_total} ({www_success/www_total*100:.1f}%)")

    print(f"\n【news.web.nhk ドメイン】")
    news_success = sum(1 for v in news_web_results.values() if v)
    news_total = len(news_web_results)
    for name, success in news_web_results.items():
        status = "✅ 成功" if success else "❌ 失敗"
        print(f"{status}: {name}")
    if news_total > 0:
        print(f"成功率: {news_success}/{news_total} ({news_success/news_total*100:.1f}%)")

    # 全体サマリー
    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)

    print(f"\n【全体】")
    print(f"成功率: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")

    # 結論
    if www_success == www_total and news_success == 0:
        print(f"\n🎉 www.nhk.or.jpドメインはすべて成功！")
        print(f"❌ news.web.nhkドメイン（東北）のみ失敗")
        print(f"\n推奨アプローチ:")
        print(f"1. www.nhk.or.jpの6ソース: requests で完全自動化")
        print(f"2. news.web.nhk（東北）: Selenium/手動インポート")
    elif success_count == total_count:
        print(f"\n🎉 すべてのソースで取得成功！")
        print(f"→ Python実装で完全自動化が可能です")
    elif success_count > 0:
        print(f"\n⚠️  {total_count - success_count}個のソースで失敗")
    else:
        print(f"\n❌ すべてのソースで失敗")

if __name__ == '__main__':
    main()
