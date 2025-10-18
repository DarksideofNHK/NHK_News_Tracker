#!/bin/bash
#
# NHK記事追跡システム - 自動実行＆デプロイスクリプト
# 4時間ごとに実行され、記事を収集してNetlifyにデプロイ
#

# スクリプトのディレクトリに移動
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ログファイル
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/auto_deploy_$(date +%Y%m%d_%H%M%S).log"

echo "========================================" | tee -a "$LOG_FILE"
echo "NHK記事追跡システム - 自動実行開始" | tee -a "$LOG_FILE"
echo "実行時刻: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

# 1. 記事収集と変更検出
echo "" | tee -a "$LOG_FILE"
echo "📡 記事収集中..." | tee -a "$LOG_FILE"
/usr/bin/python3 main_hybrid.py >> "$LOG_FILE" 2>&1
if [ $? -eq 0 ]; then
    echo "✅ 記事収集完了" | tee -a "$LOG_FILE"
else
    echo "❌ 記事収集エラー" | tee -a "$LOG_FILE"
    exit 1
fi

# 2. ポータルページ生成
echo "" | tee -a "$LOG_FILE"
echo "🎨 ポータルページ生成中..." | tee -a "$LOG_FILE"
/usr/bin/python3 generate_portal.py >> "$LOG_FILE" 2>&1
if [ $? -eq 0 ]; then
    echo "✅ ポータルページ生成完了" | tee -a "$LOG_FILE"
else
    echo "❌ ポータルページ生成エラー" | tee -a "$LOG_FILE"
fi

# 3. 変更履歴ページ生成
echo "" | tee -a "$LOG_FILE"
echo "🎨 変更履歴ページ生成中..." | tee -a "$LOG_FILE"
/usr/bin/python3 generate_history.py >> "$LOG_FILE" 2>&1
if [ $? -eq 0 ]; then
    echo "✅ 変更履歴ページ生成完了" | tee -a "$LOG_FILE"
else
    echo "❌ 変更履歴ページ生成エラー" | tee -a "$LOG_FILE"
fi

# 4. アーカイブページ生成
echo "" | tee -a "$LOG_FILE"
echo "🎨 アーカイブページ生成中..." | tee -a "$LOG_FILE"
/usr/bin/python3 generate_archive.py >> "$LOG_FILE" 2>&1
if [ $? -eq 0 ]; then
    echo "✅ アーカイブページ生成完了" | tee -a "$LOG_FILE"
else
    echo "❌ アーカイブページ生成エラー" | tee -a "$LOG_FILE"
fi

# 5. おことわりページ生成
echo "" | tee -a "$LOG_FILE"
echo "🎨 おことわりページ生成中..." | tee -a "$LOG_FILE"
/usr/bin/python3 generate_corrections.py >> "$LOG_FILE" 2>&1
if [ $? -eq 0 ]; then
    echo "✅ おことわりページ生成完了" | tee -a "$LOG_FILE"
else
    echo "❌ おことわりページ生成エラー" | tee -a "$LOG_FILE"
fi

# 6. Netlifyへデプロイ
echo "" | tee -a "$LOG_FILE"
echo "🚀 Netlifyへデプロイ中..." | tee -a "$LOG_FILE"
netlify deploy --prod --dir=reports >> "$LOG_FILE" 2>&1
if [ $? -eq 0 ]; then
    echo "✅ デプロイ完了: https://nhk-news-tracker.netlify.app" | tee -a "$LOG_FILE"
else
    echo "❌ デプロイエラー" | tee -a "$LOG_FILE"
fi

echo "" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo "実行完了: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"
echo "ログファイル: $LOG_FILE" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

# 古いログファイルを削除（30日以上前）
find "$LOG_DIR" -name "auto_deploy_*.log" -mtime +30 -delete
