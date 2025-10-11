#!/bin/bash
# Chrome起動スクリプト（Remote Debugging有効）

echo "============================================================"
echo "Chrome起動（Remote Debugging有効）"
echo "============================================================"

# Chromeプロセスが既に起動しているか確認
if pgrep -x "Google Chrome" > /dev/null
then
    echo ""
    echo "⚠️  Chromeが既に起動しています"
    echo ""
    echo "選択肢:"
    echo "1. 既存のChromeを閉じて、このスクリプトを再実行"
    echo "2. 既存のChromeがRemote Debuggingで起動済みなら何もしない"
    echo ""
    echo "確認方法:"
    echo "  open http://localhost:9222"
    echo "  → JSONが表示されればOK"
    echo ""
    exit 1
fi

echo ""
echo "Chromeを起動中..."
echo "Remote Debugging Port: 9222"
echo ""

# Chromeを起動（バックグラウンド）
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/Library/Application Support/Google/Chrome" \
  --profile-directory="Default" \
  > /dev/null 2>&1 &

sleep 3

echo "✅ Chrome起動完了"
echo ""
echo "確認:"
echo "  open http://localhost:9222"
echo "  → JSONが表示されればRemote Debugging有効"
echo ""
echo "終了方法:"
echo "  通常通りChromeを閉じる"
echo ""
echo "============================================================"
