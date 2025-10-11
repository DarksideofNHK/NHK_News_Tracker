#!/usr/bin/env python3
"""
週次レポート生成スクリプト

使用方法:
    python3 generate_weekly_report.py [日数]

例:
    python3 generate_weekly_report.py 7   # 過去7日間のレポート
    python3 generate_weekly_report.py     # デフォルト7日間
"""
import sys
from weekly_report import WeeklyReportGenerator

def main():
    """メイン実行"""
    # 日数（デフォルト: 7日間）
    days = 7
    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
        except ValueError:
            print(f"エラー: 日数は整数で指定してください")
            sys.exit(1)

    print("="*60)
    print("NHK誤情報モニタリング - 週次レポート生成")
    print("="*60)
    print(f"対象期間: 過去{days}日間\n")

    # レポート生成
    generator = WeeklyReportGenerator()

    print("データ取得中...")
    corrections = generator.get_corrections(days)
    removals = generator.get_correction_removals(days)
    serious_changes = generator.get_serious_changes(days)

    print(f"\n統計:")
    print(f"  訂正記事: {len(corrections)}件")
    print(f"  訂正削除: {len(removals)}件 ← 最重要！")
    print(f"  深刻な変更: {len(serious_changes)}件")

    if removals:
        print(f"\n⚠️  警告: {len(removals)}件の訂正削除を検出しました！")
        print("これらの記事は訂正後、短時間で削除された可能性があります。")

    print("\nHTMLレポート生成中...")
    output_path = generator.generate_report(days)

    print(f"\n✅ レポート生成完了!")
    print(f"出力先: {output_path}")
    print(f"\nブラウザで開く:")
    print(f"  open {output_path}")

    print("\n" + "="*60)

if __name__ == '__main__':
    main()
