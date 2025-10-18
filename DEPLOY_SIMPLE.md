# 最も簡単なデプロイ方法

## 🚀 方法1: Netlify Drop（最速・推奨）

**所要時間: 3分**

### 手順

1. **レポートを生成**
   ```bash
   cd /Users/trudibussi/projects/gemini-cli/rss-diff-analyzer-python
   python3 main_hybrid.py
   ```

2. **Netlify Dropにアクセス**
   - ブラウザで https://app.netlify.com/drop を開く
   - ログイン（GitHubアカウントでOK）

3. **reportsフォルダをドラッグ&ドロップ**
   - Finderで `reports` フォルダを開く
   - フォルダごとNetlifyのページにドロップ

4. **完了！**
   - URLが自動発行されます（例: `https://cosmic-star-123456.netlify.app`）
   - すぐにアクセス可能

### 更新方法

```bash
# 最新データを取得
python3 main_hybrid.py

# reportsフォルダを再度ドラッグ&ドロップ
```

**メリット:**
- ✅ 設定不要
- ✅ すぐに公開できる
- ✅ 無料
- ✅ 自動HTTPS

---

## 🔄 方法2: GitHub Pages（自動更新）

**所要時間: 15分（初回のみ）**

### ステップ1: リポジトリ作成

```bash
cd /Users/trudibussi/projects/gemini-cli/rss-diff-analyzer-python

# Gitリポジトリを初期化（まだの場合）
git init
git branch -M main

# GitHubでリポジトリを作成後
git remote add origin git@github.com:YOUR_USERNAME/nhk-tracker.git

# 最初のコミット
git add .
git commit -m "Initial commit"
git push -u origin main
```

### ステップ2: GitHub Actionsの設定

すでに `.github/workflows/deploy.yml` が用意されています。

ただし、現在のデプロイ設定は reports を生成するため、
`.gitignore` でreportsを除外しないようにする必要があります。

**オプションA: reportsを含める（簡単）**

`.gitignore` から以下の行を削除またはコメントアウト：
```
# reports/*.html
# reports/*.json
```

**オプションB: GitHub Actionsでビルド（推奨）**

このまま変更なし。GitHub Actionsが自動でレポートを生成します。

### ステップ3: GitHub Pagesを有効化

1. GitHubリポジトリの **Settings** → **Pages**
2. Source: **Deploy from a branch**
3. Branch: **gh-pages** → **(root)**
4. **Save**

### ステップ4: 初回デプロイ

GitHub Actionsが自動実行されます：
- **Actions** タブで進行状況を確認
- 完了後、`https://YOUR_USERNAME.github.io/nhk-tracker/` で公開

### 自動更新

設定済み！以降は：
- ✅ 1時間ごとに自動更新
- ✅ コードをpushすると自動デプロイ
- ✅ 手動実行も可能（Actions → Run workflow）

---

## 📊 比較

| 機能 | Netlify Drop | GitHub Pages |
|------|--------------|--------------|
| 設定の簡単さ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 自動更新 | ❌ 手動 | ✅ 1時間ごと |
| コスト | 無料 | 無料 |
| カスタムドメイン | ✅ | ✅ |
| HTTPS | ✅ 自動 | ✅ 自動 |

## 🎯 どちらを選ぶ？

### Netlify Dropがおすすめ：
- 今すぐ公開したい
- 手動更新でOK
- 設定不要がいい

### GitHub Pagesがおすすめ：
- 自動更新したい
- Gitを使っている
- 一度設定したら放置したい

---

## 🔧 デプロイ用スクリプト

### Netlify CLIを使う場合

```bash
# 初回のみ: Netlify CLIをインストール
npm install -g netlify-cli

# ログイン
netlify login

# デプロイ
python3 main_hybrid.py  # レポート生成
netlify deploy --prod --dir=reports

# 以降は毎回
python3 main_hybrid.py && netlify deploy --prod --dir=reports
```

### 自動化スクリプト

`deploy.sh` を作成：
```bash
#!/bin/bash
set -e

echo "📦 データ取得＆レポート生成中..."
python3 main_hybrid.py

echo "📤 デプロイ中..."
netlify deploy --prod --dir=reports

echo "✅ 完了！"
```

実行：
```bash
chmod +x deploy.sh
./deploy.sh
```

### cron で定期実行

```bash
# crontabを編集
crontab -e

# 1時間ごとに自動更新
0 * * * * cd /Users/trudibussi/projects/gemini-cli/rss-diff-analyzer-python && ./deploy.sh >> /tmp/nhk-deploy.log 2>&1
```

---

## 💡 ヒント

### カスタムドメイン設定

**Netlify:**
1. Site settings → Domain management
2. Add custom domain
3. DNSレコードを設定

**GitHub Pages:**
1. Settings → Pages → Custom domain
2. `nhk-tracker.your-domain.com` を入力
3. DNSに CNAME レコードを追加

### パスワード保護（Netlify）

Netlifyの有料プラン（$19/月）でパスワード保護が可能です。
無料で保護したい場合は、Cloudflare Access（無料）を検討してください。

---

## ⚠️ 重要な注意

### Seleniumについて

GitHub ActionsやNetlifyのビルド環境でSeleniumを使う場合、
Chromeのインストールが必要です。

現在の設定では、ローカルで生成したHTMLをアップロードする方式（Netlify Drop）
が最も確実です。

自動ビルドする場合は、追加の設定が必要になる場合があります。

---

## 次のステップ

詳細な設定は以下を参照：
- `DEPLOYMENT.md` - 完全なデプロイガイド
- `QUICKSTART_DEPLOY.md` - クイックスタートガイド
