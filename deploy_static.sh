#!/bin/bash
# 静的ファイルデプロイスクリプト
# ローカルで実行→HTMLのみアップロード

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📰 NHK記事追跡システム - 静的デプロイ"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ステップ1: ローカルでレポート生成
echo "📦 ステップ1: ローカルでデータ取得＆レポート生成"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 main_hybrid.py

if [ $? -ne 0 ]; then
    echo "❌ エラー: レポート生成に失敗しました"
    exit 1
fi

echo ""
echo "📤 ステップ2: 生成されたHTMLファイルをデプロイ"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# reportsフォルダの存在確認
if [ ! -d "reports" ]; then
    echo "❌ エラー: reportsフォルダが見つかりません"
    exit 1
fi

# ファイル数を確認
file_count=$(find reports -name "*.html" | wc -l)
echo "📊 アップロード対象: ${file_count}個のHTMLファイル"
echo ""

# デプロイ方法を選択
echo "デプロイ先を選択してください:"
echo "  1) GitHub Pages (gh-pages ブランチ)"
echo "  2) Netlify CLI"
echo "  3) rsync (自前サーバー)"
echo ""
read -p "選択 [1-3]: " choice

case $choice in
    1)
        echo ""
        echo "🐙 GitHub Pagesへデプロイ中..."

        # 一時ディレクトリを作成
        temp_dir=$(mktemp -d)

        # reportsの内容をコピー
        cp -r reports/* "$temp_dir/"

        # 一時ディレクトリでgit操作
        cd "$temp_dir"
        git init
        git add .
        git commit -m "Deploy: $(date '+%Y-%m-%d %H:%M:%S')"

        # リモートリポジトリのURLを確認
        if [ ! -z "$GITHUB_REPO" ]; then
            repo_url="$GITHUB_REPO"
        else
            read -p "GitHubリポジトリURL (例: git@github.com:username/repo.git): " repo_url
        fi

        # gh-pagesブランチにフォースプッシュ
        git push -f "$repo_url" main:gh-pages

        cd - > /dev/null
        rm -rf "$temp_dir"

        echo "✅ GitHub Pagesへのデプロイ完了"
        ;;

    2)
        echo ""
        echo "📡 Netlifyへデプロイ中..."

        if ! command -v netlify &> /dev/null; then
            echo "❌ Netlify CLIがインストールされていません"
            echo ""
            echo "インストール方法:"
            echo "  npm install -g netlify-cli"
            exit 1
        fi

        netlify deploy --prod --dir=reports
        echo "✅ Netlifyへのデプロイ完了"
        ;;

    3)
        echo ""
        echo "🔄 rsyncでデプロイ中..."

        if [ -z "$RSYNC_DEST" ]; then
            read -p "rsync先 (例: user@server:/var/www/html): " rsync_dest
        else
            rsync_dest="$RSYNC_DEST"
        fi

        # rsync実行（ドライラン）
        echo "ドライラン実行中..."
        rsync -avz --dry-run --delete reports/ "$rsync_dest"

        echo ""
        read -p "この内容でアップロードしますか？ [y/N]: " confirm

        if [[ $confirm == [yY] ]]; then
            rsync -avz --delete reports/ "$rsync_dest"
            echo "✅ rsyncでのデプロイ完了"
        else
            echo "キャンセルしました"
            exit 0
        fi
        ;;

    *)
        echo "❌ 無効な選択です"
        exit 1
        ;;
esac

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ デプロイ完了！"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 統計:"
echo "  HTMLファイル: ${file_count}個"
echo "  生成時刻: $(date '+%Y年%m月%d日 %H:%M:%S')"
echo ""
