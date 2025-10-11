#!/bin/bash
#
# cron設定セットアップスクリプト
#

echo "============================================================"
echo "cron設定セットアップ"
echo "============================================================"

# 現在のディレクトリ
CURRENT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Python実行パス
PYTHON_PATH=$(which python3)

echo ""
echo "プロジェクトディレクトリ: $CURRENT_DIR"
echo "Python実行パス: $PYTHON_PATH"

# logsディレクトリ作成
echo ""
echo "logsディレクトリを作成..."
mkdir -p "$CURRENT_DIR/logs"
echo "✅ 完了"

# cron設定を一時ファイルに作成
CRON_FILE=$(mktemp)

echo ""
echo "cron設定を作成中..."

cat > "$CRON_FILE" << EOF
# NHK RSS差分追跡システム - 1時間ごとに自動実行
# 毎時0分に実行
0 * * * * cd $CURRENT_DIR && $CURRENT_DIR/run.sh >> $CURRENT_DIR/logs/cron.log 2>&1

# 週次レポート - 毎週月曜0時に実行（オプション）
# 0 0 * * 1 cd $CURRENT_DIR && source ~/.zshrc && $PYTHON_PATH $CURRENT_DIR/generate_weekly_report.py >> $CURRENT_DIR/logs/weekly.log 2>&1
EOF

echo ""
echo "─────────────────────────────────────────────────────────"
echo "以下のcron設定を追加します:"
echo "─────────────────────────────────────────────────────────"
cat "$CRON_FILE"
echo "─────────────────────────────────────────────────────────"

echo ""
echo "この設定で良いですか？ (y/n)"
read -r response

if [[ "$response" == "y" ]]; then
    # 既存のcrontabを取得
    if crontab -l > /dev/null 2>&1; then
        # 既存のcrontabがある場合
        (crontab -l 2>/dev/null; cat "$CRON_FILE") | crontab -
    else
        # 既存のcrontabがない場合
        crontab "$CRON_FILE"
    fi

    echo ""
    echo "✅ cron設定を追加しました"

    echo ""
    echo "現在のcrontab:"
    echo "─────────────────────────────────────────────────────────"
    crontab -l
    echo "─────────────────────────────────────────────────────────"

    echo ""
    echo "✅ セットアップ完了！"
    echo ""
    echo "次のステップ:"
    echo "1. 1時間待機して、logs/cron.log を確認"
    echo "2. tail -f logs/cron.log で実行状況を監視"
    echo ""
    echo "⚠️  注意:"
    echo "- macOSの場合、ターミナルにcronの実行権限が必要です"
    echo "- システム環境設定 > セキュリティとプライバシー > フルディスクアクセス"
    echo "  でターミナル（またはcron）を追加してください"
else
    echo ""
    echo "❌ キャンセルしました"
fi

# 一時ファイル削除
rm -f "$CRON_FILE"

echo "============================================================"
