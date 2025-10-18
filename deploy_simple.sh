#!/bin/bash
# 最も簡単なデプロイスクリプト
# ローカル実行 → Netlify CLI でアップロード

set -e

# プロジェクトディレクトリに移動
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# PATHを明示的に設定（launchdから実行される場合に必要）
# npm global modulesのパスを追加（環境に応じて調整してください）
export PATH="$HOME/.npm-global/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📰 NHK記事追跡システム - 簡単デプロイ"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ステップ1: データ取得とレポート生成
echo "📦 ステップ1: 最新データ取得とレポート生成"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
/usr/bin/python3 main_hybrid.py

if [ $? -ne 0 ]; then
    echo "❌ エラー: レポート生成に失敗しました"
    exit 1
fi

echo ""
echo "✅ レポート生成完了"
echo ""

# ステップ2: デプロイ
echo "📤 ステップ2: HTMLファイルをNetlifyへアップロード"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Netlify CLIの確認
if command -v netlify &> /dev/null; then
    echo "Netlify CLIを使用してデプロイします..."
    netlify deploy --prod --dir=reports

    if [ $? -eq 0 ]; then
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "✅ デプロイ完了！"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    else
        echo "❌ デプロイに失敗しました"
        exit 1
    fi
else
    echo "⚠️  Netlify CLIがインストールされていません"
    echo ""
    echo "次の方法でデプロイできます："
    echo ""
    echo "【方法1: Netlify Drop（最も簡単）】"
    echo "  1. ブラウザで https://app.netlify.com/drop を開く"
    echo "  2. reportsフォルダをドラッグ&ドロップ"
    echo "  3. 完了！URLが自動発行されます"
    echo ""
    echo "【方法2: Netlify CLI をインストール】"
    echo "  npm install -g netlify-cli"
    echo "  netlify login"
    echo "  このスクリプトを再実行"
    echo ""

    # reportsフォルダを開く
    read -p "reportsフォルダをFinderで開きますか？ [y/N]: " open_folder
    if [[ $open_folder == [yY] ]]; then
        open reports
        echo ""
        echo "Finderが開きました。reportsフォルダをNetlifyにドラッグ&ドロップしてください。"
    fi
fi

echo ""
echo "📊 生成されたファイル:"
echo "  HTMLファイル: $(find reports -name "*.html" | wc -l)個"
echo "  生成時刻: $(date '+%Y年%m月%d日 %H:%M:%S')"
echo ""
