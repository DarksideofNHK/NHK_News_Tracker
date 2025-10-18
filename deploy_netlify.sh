#!/bin/bash
# Netlify へのデプロイスクリプト

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📰 NHK記事追跡システム - Netlifyデプロイ"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Netlify CLIの確認
if ! command -v netlify &> /dev/null; then
    echo "⚠️  Netlify CLIがインストールされていません"
    echo ""
    echo "インストール方法:"
    echo "  npm install -g netlify-cli"
    echo ""
    echo "または、手動デプロイ:"
    echo "  1. https://app.netlify.com/drop を開く"
    echo "  2. reports フォルダをドラッグ&ドロップ"
    echo ""
    exit 1
fi

echo "📦 ステップ1: 最新データを取得＆レポート生成"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 main_hybrid.py

if [ $? -ne 0 ]; then
    echo "❌ エラー: レポート生成に失敗しました"
    exit 1
fi

echo ""
echo "📤 ステップ2: Netlifyへデプロイ"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 初回デプロイか確認
if [ ! -f ".netlify/state.json" ]; then
    echo "🆕 初回デプロイです"
    echo "ログインとサイトの設定を行います..."
    echo ""
    netlify init
fi

# デプロイ実行
netlify deploy --prod --dir=reports

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ デプロイ完了！"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🌐 サイトURL:"
netlify status | grep "Live Draft URL" || echo "Netlify のダッシュボードでURLを確認してください"
echo ""
