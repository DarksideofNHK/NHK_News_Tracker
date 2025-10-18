#!/bin/bash
# GitHub Pagesへ手動デプロイ

set -e

echo "📦 レポート生成中..."
python3 main_hybrid.py

echo "📤 GitHub Pagesへデプロイ中..."

# reportsディレクトリをgh-pagesブランチにプッシュ
cd reports

# 一時的にgitリポジトリを初期化
git init
git add .
git commit -m "Update: $(date '+%Y-%m-%d %H:%M:%S')"

# GitHub Pagesブランチにフォースプッシュ
git push -f git@github.com:YOUR_USERNAME/YOUR_REPO.git main:gh-pages

cd ..

echo "✅ デプロイ完了！"
echo "🌐 https://YOUR_USERNAME.github.io/YOUR_REPO/"
