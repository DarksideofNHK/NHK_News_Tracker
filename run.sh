#!/bin/bash
# NHK RSS差分追跡システム 実行スクリプト
# 環境変数を自動的に読み込んで実行

# .zshrc から環境変数を読み込む
source ~/.zshrc 2>/dev/null || true

# Gemini APIキーが設定されているか確認
if [ -z "$GEMINI_API_KEY" ]; then
    echo "⚠️  警告: GEMINI_API_KEY が設定されていません"
    echo "AI分析は無効になります。"
    echo ""
    echo "設定方法:"
    echo "  echo 'export GEMINI_API_KEY=\"your_key\"' >> ~/.zshrc"
    echo "  source ~/.zshrc"
    echo ""
fi

# メインスクリプトを実行
cd "$(dirname "$0")"
python3 main_hybrid.py "$@"
