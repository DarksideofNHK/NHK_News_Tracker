#!/usr/bin/env python3
"""
NHK RSS差分追跡システム - ハイブリッド版メインスクリプト
requests（6ソース）+ Selenium（東北）
"""
import yaml
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# .envファイルから環境変数を読み込み
load_dotenv()

from scraper_hybrid import NhkRssScraperHybrid
from parser import NhkXmlParser
from storage import ArticleStorage
from visualizer import ChangeVisualizer
from gemini_analyzer import GeminiAnalyzer

def setup_logging(config: dict):
    """ログ設定"""
    log_config = config.get('logging', {})
    log_file = Path(log_config.get('file', 'logs/nhk_tracker.log'))
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, log_config.get('level', 'INFO')),
        format=log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def load_config(config_path: str = 'config.yaml') -> dict:
    """設定ファイル読み込み"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def main():
    """メイン実行"""
    print("="*60)
    print("NHK RSS差分追跡システム - ハイブリッド版")
    print("requests（6ソース）+ Selenium（東北）")
    print("="*60)
    print(f"実行開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 設定読み込み
    config = load_config()
    setup_logging(config)
    logger = logging.getLogger(__name__)

    # 初期化
    scraper = NhkRssScraperHybrid()
    parser = NhkXmlParser()

    # Gemini Analyzer（環境変数GEMINI_API_KEYが必要）
    gemini = GeminiAnalyzer()

    storage = ArticleStorage(db_path=config['database']['path'], gemini_analyzer=gemini)
    visualizer = ChangeVisualizer()

    # 統計
    total_stats = {'new': 0, 'updated': 0, 'unchanged': 0}

    # URLリストを作成（一括取得用）
    sources_dict = {}
    for source_config in config['sources']:
        if source_config.get('enabled', True):
            sources_dict[source_config['name']] = source_config['url']

    print(f"{'─'*60}")
    print(f"一括取得開始: {len(sources_dict)}ソース")
    print(f"{'─'*60}\n")

    # 一括取得（requests + Selenium自動切り替え）
    contents = scraper.fetch_batch(sources_dict)

    # 各ソースを処理
    for source_config in config['sources']:
        if not source_config.get('enabled', True):
            continue

        name = source_config['name']
        xml_content = contents.get(name)

        print(f"\n{'─'*60}")
        print(f"処理中: {name}")
        print(f"{'─'*60}")

        if xml_content is None:
            print(f"❌ 取得失敗: {name}")
            continue

        # 解析
        articles = parser.parse(xml_content)
        if not articles:
            print(f"❌ 解析失敗: {name}")
            continue

        print(f"✅ 記事取得: {len(articles)}件")

        # 保存と変更検出
        stats = storage.save_articles(name, articles)

        print(f"📊 結果:")
        print(f"  - 新規: {stats['new']}件")
        print(f"  - 更新: {stats['updated']}件")
        print(f"  - 変更なし: {stats['unchanged']}件")

        # 統計集計
        for key in total_stats:
            total_stats[key] += stats[key]

    # 全体サマリー
    print(f"\n{'='*60}")
    print("全体サマリー")
    print(f"{'='*60}")
    print(f"新規記事: {total_stats['new']}件")
    print(f"更新記事: {total_stats['updated']}件")
    print(f"変更なし: {total_stats['unchanged']}件")

    # HTMLレポート生成
    print(f"\n{'─'*60}")
    print("HTMLレポート生成中...")
    print(f"{'─'*60}")

    hours = config['report'].get('hours', 24)
    changes = storage.get_recent_changes(hours=hours)

    if changes:
        output_dir = Path(config['report']['output_dir'])
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = output_dir / f'changes_{timestamp}.html'

        visualizer.generate_html_report(changes, str(output_path), hours=hours)

        print(f"✅ HTMLレポート: {output_path.absolute()}")
        print(f"📊 変更件数: {len(changes)}件（過去{hours}時間）")
    else:
        print(f"ℹ️  過去{hours}時間に変更はありませんでした")

    # JSONエクスポート
    print(f"\n{'─'*60}")
    print("データエクスポート中...")
    print(f"{'─'*60}")

    export_path = f"data/export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    storage.export_to_json(export_path)
    print(f"✅ JSONエクスポート: {Path(export_path).absolute()}")

    # 全変更履歴ビューアー生成
    print(f"\n{'─'*60}")
    print("全変更履歴ビューアー生成中...")
    print(f"{'─'*60}")

    try:
        import generate_history
        generate_history.main()
    except Exception as e:
        print(f"⚠️ 履歴ビューアー生成エラー: {e}")
        logger.warning(f"履歴ビューアー生成失敗: {e}")

    # 記事アーカイブビューアー生成
    print(f"\n{'─'*60}")
    print("記事アーカイブビューアー生成中...")
    print(f"{'─'*60}")

    try:
        import generate_archive
        generate_archive.main()
    except Exception as e:
        print(f"⚠️ アーカイブビューアー生成エラー: {e}")
        logger.warning(f"アーカイブビューアー生成失敗: {e}")

    print(f"\n{'='*60}")
    print(f"実行完了: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
