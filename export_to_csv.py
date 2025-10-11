#!/usr/bin/env python3
"""
記事データをCSVにエクスポート

使用方法:
    python3 export_to_csv.py                    # 全記事をエクスポート
    python3 export_to_csv.py --days 7           # 過去7日間のみ
    python3 export_to_csv.py --corrections      # 訂正記事のみ
"""
import sqlite3
import csv
from pathlib import Path
from datetime import datetime, timedelta
import argparse

def export_articles_to_csv(output_path: str = None, days: int = None, corrections_only: bool = False):
    """記事データをCSVにエクスポート"""
    db_path = 'data/articles.db'

    if output_path is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = f'data/articles_{timestamp}.csv'

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # クエリ構築
    query = 'SELECT source, link, title, description, pub_date, first_seen, last_seen, has_correction, correction_keywords FROM articles'
    conditions = []
    params = []

    if days:
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        conditions.append('first_seen >= ?')
        params.append(cutoff)

    if corrections_only:
        conditions.append('has_correction = 1')

    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)

    query += ' ORDER BY first_seen DESC'

    cursor.execute(query, params)

    # CSV出力
    with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['ソース', 'URL', 'タイトル', '説明', '公開日時', '初回検出', '最終確認', '訂正あり', '訂正キーワード'])

        count = 0
        for row in cursor.fetchall():
            writer.writerow(row)
            count += 1

    conn.close()

    print(f"✅ {count}件の記事をエクスポートしました")
    print(f"出力先: {output_path}")
    return output_path

def export_changes_to_csv(output_path: str = None, days: int = None):
    """変更履歴をCSVにエクスポート"""
    db_path = 'data/articles.db'

    if output_path is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = f'data/changes_{timestamp}.csv'

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    query = 'SELECT source, link, change_type, old_value, new_value, detected_at, change_summary, has_correction, correction_keywords FROM changes'
    params = []

    if days:
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        query += ' WHERE detected_at >= ?'
        params.append(cutoff)

    query += ' ORDER BY detected_at DESC'

    cursor.execute(query, params)

    # CSV出力
    with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['ソース', 'URL', '変更タイプ', '変更前', '変更後', '検出時刻', 'AI分析', '訂正あり', '訂正キーワード'])

        count = 0
        for row in cursor.fetchall():
            writer.writerow(row)
            count += 1

    conn.close()

    print(f"✅ {count}件の変更をエクスポートしました")
    print(f"出力先: {output_path}")
    return output_path

def main():
    parser = argparse.ArgumentParser(description='記事データをCSVにエクスポート')
    parser.add_argument('--days', type=int, help='過去N日間のデータのみ')
    parser.add_argument('--corrections', action='store_true', help='訂正記事のみ')
    parser.add_argument('--changes', action='store_true', help='変更履歴をエクスポート')
    parser.add_argument('--output', type=str, help='出力ファイルパス')

    args = parser.parse_args()

    print("="*60)
    print("NHK記事データ CSVエクスポート")
    print("="*60)

    if args.changes:
        print(f"\n変更履歴をエクスポート中...")
        if args.days:
            print(f"対象期間: 過去{args.days}日間")
        export_changes_to_csv(args.output, args.days)
    else:
        print(f"\n記事データをエクスポート中...")
        if args.days:
            print(f"対象期間: 過去{args.days}日間")
        if args.corrections:
            print(f"対象: 訂正記事のみ")
        export_articles_to_csv(args.output, args.days, args.corrections)

    print("\n" + "="*60)

if __name__ == '__main__':
    main()
