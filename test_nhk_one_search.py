#!/usr/bin/env python3
"""
NHK ONE検索のテストスクリプト（デバッグ用）
"""
import logging
from scraper_hybrid import NhkRssScraperHybrid

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    print("="*60)
    print("NHK ONE検索テスト - デバッグモード")
    print("="*60)

    scraper = NhkRssScraperHybrid()

    print("\n検索実行中...")
    articles = scraper.search_nhk_one(query="失礼しました")

    print(f"\n検索結果: {len(articles)}件")

    if articles:
        print("\n取得した記事:")
        for i, article in enumerate(articles, 1):
            print(f"\n【記事 {i}】")
            print(f"  タイトル: {article['title'][:80]}...")
            print(f"  URL: {article['link']}")
            print(f"  本文: {article['description'][:150]}...")
    else:
        print("\n訂正記事は見つかりませんでした。")
        print("スクリーンショットを /tmp/ ディレクトリで確認してください。")

if __name__ == '__main__':
    main()
