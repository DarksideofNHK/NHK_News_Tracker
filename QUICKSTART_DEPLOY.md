# クイックデプロイガイド

最も簡単にWebサイトとして公開する方法（5分で完了）

## 🚀 最速：Netlify Drop（推奨）

ドラッグ&ドロップするだけで即公開！

### 手順

1. **レポートを生成**
   ```bash
   cd /Users/trudibussi/projects/gemini-cli/rss-diff-analyzer-python
   python3 main_hybrid.py
   ```

2. **Netlifyにアクセス**
   - ブラウザで https://app.netlify.com/drop を開く

3. **reportsフォルダをドラッグ&ドロップ**
   - Finderで `reports` フォルダを開く
   - フォルダ全体をNetlifyのページにドラッグ

4. **完了！**
   - 自動的にURLが発行されます（例: `https://sparkly-sunshine-123456.netlify.app`）
   - このURLにアクセスすれば、ポータルページが表示されます

### 更新方法

同じ手順を繰り返すだけ：
```bash
python3 main_hybrid.py  # 最新データを取得
# reportsフォルダを再度ドラッグ&ドロップ
```

---

## 🔄 自動更新：GitHub Pages

一度設定すれば、あとは自動で更新されます

### 初回セットアップ（10分）

1. **GitHubリポジトリを作成**
   - https://github.com/new
   - リポジトリ名: `nhk-news-tracker`（任意）
   - Public または Private（どちらでも可）
   - Create repository

2. **コードをプッシュ**
   ```bash
   cd /Users/trudibussi/projects/gemini-cli/rss-diff-analyzer-python

   # 初回のみ
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin git@github.com:YOUR_USERNAME/nhk-news-tracker.git
   git push -u origin main
   ```

3. **GitHub Pagesを有効化**
   - リポジトリの Settings → Pages
   - Source: "Deploy from a branch"
   - Branch: `gh-pages` / (root)
   - Save

4. **GitHub Actionsが自動実行される**
   - "Actions" タブで進行状況を確認
   - 数分後に完了

5. **公開URL**
   - `https://YOUR_USERNAME.github.io/nhk-news-tracker/`
   - Settings → Pages で確認できます

### 自動更新

設定済みの GitHub Actions により：
- ✅ **1時間ごとに自動更新**（最新のニュースを取得）
- ✅ コードをpushしたら自動デプロイ
- ✅ 手動実行も可能（Actions → Run workflow）

---

## 📱 どちらを選ぶべき？

### Netlify Drop がおすすめな人
- ✅ とにかく今すぐ公開したい
- ✅ 手動で更新するのが苦にならない
- ✅ GitHubを使いたくない

### GitHub Pages がおすすめな人
- ✅ 自動更新したい（1時間ごと）
- ✅ GitHubを普段から使っている
- ✅ 一度設定したら放置したい

---

## 🎨 カスタマイズ

### サイト名を変更

`generate_portal.py` の以下を編集：
```python
<h1>📰 NHK記事追跡システム</h1>
```

### 更新頻度を変更（GitHub Pages）

`.github/workflows/deploy.yml` の `cron` を編集：
```yaml
schedule:
  # 現在: 1時間ごと
  - cron: '0 * * * *'

  # 変更例: 6時間ごと
  - cron: '0 */6 * * *'
```

---

## ⚠️ 注意事項

### データベースファイル

デフォルトでは `data/articles.db` はデプロイされません（`.gitignore` に含まれる予定）。
これにより、毎回クリーンな状態から記事を収集します。

もし履歴を保持したい場合は、データベースを別途バックアップしてください。

### APIキー

GitHub Actionsを使う場合、Gemini APIキーは不要です（RSSとSeleniumのみで動作）。
もしAI分析機能を使いたい場合は：

1. リポジトリの Settings → Secrets and variables → Actions
2. "New repository secret"
3. Name: `GEMINI_API_KEY`
4. Value: あなたのAPIキー

---

## 🆘 トラブルシューティング

### Netlify: デプロイ後に404エラー

→ `reports` フォルダの中身だけでなく、フォルダごとドラッグしてください

### GitHub Pages: ページが表示されない

→ Settings → Pages で "Your site is live at..." が表示されるまで待ってください（数分かかります）

### GitHub Actions: ビルドが失敗する

→ Actions タブでログを確認してください。多くの場合、依存関係の問題です。

---

## 📞 サポート

詳細なデプロイガイドは `DEPLOYMENT.md` を参照してください。
