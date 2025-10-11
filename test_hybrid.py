#!/usr/bin/env python3
"""
ハイブリッドスクレイパーテスト
requests（6ソース）+ Selenium（東北）
"""
from scraper_hybrid import NhkRssScraperHybrid
from datetime import datetime

# テスト対象ソース
SOURCES = {
    'NHK首都圏ニュース': 'https://www.nhk.or.jp/shutoken-news/news_all_search.xml',
    'NHK福岡ニュース': 'https://www.nhk.or.jp/fukuoka-news/news_all_search.xml',
    'NHK札幌ニュース': 'https://www.nhk.or.jp/sapporo-news/news_all_search.xml',
    'NHK東海ニュース': 'https://www.nhk.or.jp/tokai-news/news_all_search.xml',
    'NHK広島ニュース': 'https://www.nhk.or.jp/hiroshima-news/news_all_search.xml',
    'NHK関西ニュース': 'https://www.nhk.or.jp/kansai-news/news_all_search.xml',
    'NHK東北ニュース': 'https://news.web.nhk/tohoku-news/news_all_search.xml',
}

def main():
    """テスト実行"""
    print("="*60)
    print("ハイブリッドスクレイパーテスト")
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    scraper = NhkRssScraperHybrid()

    print("\n一括取得開始（requests + Selenium自動切り替え）...\n")

    # 一括取得
    results = scraper.fetch_batch(SOURCES)

    # 結果表示
    print("\n" + "="*60)
    print("結果サマリー")
    print("="*60)

    requests_count = 0
    selenium_count = 0
    success_count = 0

    for name, content in results.items():
        url = SOURCES[name]
        method = "Selenium" if 'news.web.nhk' in url else "requests"

        if content:
            record_count = content.count('<record>')
            print(f"✅ {name} ({method}): {record_count}件")
            success_count += 1

            if method == "requests":
                requests_count += 1
            else:
                selenium_count += 1
        else:
            print(f"❌ {name} ({method}): 失敗")

    print(f"\n成功率: {success_count}/{len(SOURCES)} ({success_count/len(SOURCES)*100:.1f}%)")
    print(f"requests: {requests_count}ソース")
    print(f"Selenium: {selenium_count}ソース")

    if success_count == len(SOURCES):
        print("\n🎉 すべてのソースで取得成功！")
        print("→ 完全自動化が可能です")
        print("\n次のステップ:")
        print("1. python main_hybrid.py でデータ蓄積テスト")
        print("2. cronで1時間ごとに自動実行")
    elif success_count == len(SOURCES) - 1 and selenium_count == 0:
        print("\n⚠️  NHK東北（Selenium）のみ失敗")
        print("\nSeleniumプロファイルのセットアップが必要です:")
        print("  python setup_selenium_profile.py")
    else:
        print(f"\n❌ {len(SOURCES) - success_count}個のソースで失敗")

if __name__ == '__main__':
    main()
