# デプロイメントガイド

NHK記事追跡システムをWebサイトとして公開する方法

## 方法1: GitHub Pages（おすすめ）

### 準備

1. GitHubにリポジトリを作成（プライベートでもOK）

2. リポジトリにコードをプッシュ：
```bash
cd /Users/trudibussi/projects/gemini-cli/rss-diff-analyzer-python
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin git@github.com:YOUR_USERNAME/nhk-tracker.git
git push -u origin main
```

3. GitHubリポジトリのSettings → Secrets and variables → Actions で以下を設定：
   - `GEMINI_API_KEY`: あなたのGemini APIキー（オプション、AI分析を使う場合）

4. Settings → Pages で以下を設定：
   - Source: "Deploy from a branch"
   - Branch: "gh-pages" / (root)
   - Save

### 自動デプロイ（GitHub Actions）

`.github/workflows/deploy.yml` が既に設定されています。

- **自動更新**: 1時間ごとに最新データを取得してデプロイ
- **手動実行**: Actions タブから "Run workflow" で手動実行可能

### 手動デプロイ

```bash
# 実行権限を付与
chmod +x deploy_github.sh

# デプロイスクリプトを編集
nano deploy_github.sh
# YOUR_USERNAME と YOUR_REPO を実際の値に変更

# デプロイ実行
./deploy_github.sh
```

### 公開URL

`https://YOUR_USERNAME.github.io/YOUR_REPO/`

---

## 方法2: Netlify（最も簡単）

### 手動デプロイ（ドラッグ&ドロップ）

1. https://app.netlify.com/drop にアクセス

2. `reports` フォルダをドラッグ&ドロップ

3. 完了！URLが発行されます（例: `https://random-name-123.netlify.app`）

### GitHub連携で自動デプロイ

1. https://app.netlify.com にログイン

2. "New site from Git" → GitHubを選択

3. リポジトリを選択

4. Build settings:
   - Build command: `python3 main_hybrid.py`
   - Publish directory: `reports`

5. Environment variables に追加:
   - `GEMINI_API_KEY`: あなたのAPIキー（オプション）

6. Deploy site

### Netlify CLI（ローカルから）

```bash
# Netlify CLIをインストール
npm install -g netlify-cli

# ログイン
netlify login

# 初回デプロイ
cd /Users/trudibussi/projects/gemini-cli/rss-diff-analyzer-python
python3 main_hybrid.py  # レポート生成
netlify deploy --prod --dir=reports

# 以降は簡単に
python3 main_hybrid.py && netlify deploy --prod --dir=reports
```

---

## 方法3: Cloudflare Pages（高速・無料）

1. https://pages.cloudflare.com にログイン

2. "Create a project" → GitHubリポジトリを接続

3. Build settings:
   - Build command: `python3 main_hybrid.py`
   - Build output directory: `reports`

4. Environment variables:
   - `PYTHON_VERSION`: `3.9`
   - `GEMINI_API_KEY`: あなたのAPIキー（オプション）

5. Save and Deploy

---

## 自動更新の設定

### cron + デプロイスクリプト（ローカルサーバー）

```bash
# crontabを編集
crontab -e

# 1時間ごとに実行
0 * * * * cd /Users/trudibussi/projects/gemini-cli/rss-diff-analyzer-python && ./deploy_github.sh >> /tmp/nhk-deploy.log 2>&1
```

### GitHub Actions（推奨）

すでに設定済み（`.github/workflows/deploy.yml`）
- 1時間ごとに自動実行
- 手動実行も可能

---

## カスタムドメインの設定

### GitHub Pages

1. リポジトリの Settings → Pages → Custom domain
2. 独自ドメイン（例: `nhk-tracker.example.com`）を入力
3. DNSに以下のCNAMEレコードを追加：
   ```
   nhk-tracker  CNAME  YOUR_USERNAME.github.io.
   ```

### Netlify

1. Site settings → Domain management → Add custom domain
2. ドメインを入力
3. DNSレコードの設定指示に従う

### Cloudflare Pages

1. プロジェクト → Custom domains → Set up a custom domain
2. Cloudflareで管理しているドメインなら自動設定

---

## セキュリティ注意事項

### プライベート情報の保護

データベース（`data/articles.db`）をデプロイに含めたくない場合：

```bash
# .gitignore に追加
echo "data/articles.db" >> .gitignore
echo "data/*.db" >> .gitignore
```

### 環境変数の管理

APIキーは絶対にコードに含めないこと：
- ✅ GitHub Secrets に保存
- ✅ Netlify/Cloudflare の Environment variables に保存
- ❌ コードにハードコード

---

## おすすめの構成

### 個人利用・テスト
→ **Netlify Drop**（ドラッグ&ドロップ）

### 継続的な運用
→ **GitHub Pages + GitHub Actions**（完全自動化）

### 高速配信・グローバル
→ **Cloudflare Pages**

---

## トラブルシューティング

### GitHub Actions が失敗する

1. リポジトリの Actions タブでエラーログを確認
2. Secrets が正しく設定されているか確認
3. `requirements.txt` が最新か確認

### Netlify でビルドが失敗する

1. Build log を確認
2. Python バージョンが正しいか確認（`runtime.txt` を追加）
3. 依存関係が正しいか確認

### リンクが切れている

- `convert_to_full_url()` 関数でベースURLが正しいか確認
- データベースの link フィールドを確認

---

## 更新頻度の調整

### GitHub Actions

`.github/workflows/deploy.yml` の `cron` を変更：

```yaml
schedule:
  # 毎時実行
  - cron: '0 * * * *'

  # 6時間ごと
  - cron: '0 */6 * * *'

  # 毎日正午
  - cron: '0 12 * * *'
```

### Netlify（Build Hooks）

1. Site settings → Build & deploy → Build hooks
2. "Add build hook" で webhook URL を取得
3. cron で定期的に curl でトリガー：
```bash
0 * * * * curl -X POST -d {} https://api.netlify.com/build_hooks/YOUR_HOOK_ID
```

---

## コスト

すべての方法で**完全無料**で運用可能です：

- **GitHub Pages**: 無料（パブリック/プライベートリポジトリ両方）
- **Netlify**: 100GB/月まで無料
- **Cloudflare Pages**: 無制限（フリープラン）
