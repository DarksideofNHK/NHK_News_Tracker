# 新しいGitHubアカウントでのセットアップ

## 🚀 初回セットアップ

### 1. GitHubアカウントの設定

既に新しいアカウントを作成済みとのことなので、以下を確認してください：

```bash
# 現在のGit設定を確認
git config --global user.name
git config --global user.email

# 新しいアカウントの情報に変更
git config --global user.name "YOUR_NEW_USERNAME"
git config --global user.email "your_new_email@example.com"
```

### 2. SSH鍵の設定（推奨）

新しいアカウント用のSSH鍵を生成：

```bash
# SSH鍵を生成
ssh-keygen -t ed25519 -C "your_new_email@example.com" -f ~/.ssh/id_ed25519_nhk

# SSH鍵をクリップボードにコピー
pbcopy < ~/.ssh/id_ed25519_nhk.pub

# SSH configを設定
cat >> ~/.ssh/config << 'EOF'

# NHK Tracker用の新しいGitHubアカウント
Host github-nhk
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_nhk
EOF
```

GitHubで設定：
1. https://github.com/settings/keys にアクセス
2. "New SSH key" をクリック
3. Title: "NHK Tracker"
4. Key: ペースト（Cmd+V）
5. "Add SSH key"

接続テスト：
```bash
ssh -T git@github-nhk
# "Hi YOUR_NEW_USERNAME! You've successfully authenticated..." と表示されればOK
```

### 3. リポジトリの作成

```bash
# GitHubでリポジトリを作成
# https://github.com/new
# - Repository name: nhk-news-tracker (お好きな名前)
# - Public または Private
# - README は不要（既にファイルがあるため）
```

### 4. コードをプッシュ

```bash
cd /Users/trudibussi/projects/gemini-cli/rss-diff-analyzer-python

# Gitリポジトリを初期化（まだの場合）
git init
git branch -M main

# 新しいリポジトリをリモートに追加
# SSH config使用の場合（推奨）
git remote add origin git@github-nhk:YOUR_NEW_USERNAME/nhk-news-tracker.git

# または標準的な方法
# git remote add origin git@github.com:YOUR_NEW_USERNAME/nhk-news-tracker.git

# 最初のコミット
git add .
git commit -m "Initial commit: NHK News Tracker"

# プッシュ
git push -u origin main
```

### 5. GitHub Pagesの設定

1. リポジトリページで **Settings** → **Pages**
2. Source: **Deploy from a branch**
3. Branch: **gh-pages** / **(root)**
4. **Save**

### 6. GitHub Actionsの動作確認

1. リポジトリの **Actions** タブを開く
2. 自動的にワークフローが実行されます
3. 緑のチェックマークが表示されれば成功

初回は手動で実行することもできます：
- **Actions** → **Deploy to GitHub Pages** → **Run workflow**

### 7. サイトの確認

数分後、以下のURLでアクセス可能になります：

```
https://YOUR_NEW_USERNAME.github.io/nhk-news-tracker/
```

Settings → Pages で正確なURLを確認できます。

---

## 🔐 シークレットの設定（オプション）

Gemini APIを使う場合：

1. リポジトリの **Settings** → **Secrets and variables** → **Actions**
2. **New repository secret**
3. Name: `GEMINI_API_KEY`
4. Value: あなたのAPIキー
5. **Add secret**

---

## 📝 .gitignoreの調整

現在、`reports/*.html` が除外されています。

**オプション1: GitHub Actionsでビルド（推奨）**
- 現在の設定のまま
- GitHub Actionsが自動でレポートを生成

**オプション2: reportsを含める**
```bash
# .gitignore を編集
nano .gitignore

# 以下の行をコメントアウトまたは削除
# reports/*.html
# reports/*.json

# コミット
git add .gitignore
git commit -m "Update .gitignore to include reports"
git push
```

---

## 🔄 自動更新の確認

`.github/workflows/deploy.yml` で設定済み：
- ✅ 1時間ごとに自動実行
- ✅ コードをpushすると自動デプロイ
- ✅ 手動実行も可能

自動実行の様子：
1. **Actions** タブを開く
2. 実行履歴が表示されます
3. 最新の実行をクリックして詳細を確認

---

## 📊 動作確認チェックリスト

- [ ] GitHubアカウントの作成
- [ ] Git設定の更新（name, email）
- [ ] SSH鍵の設定（オプション）
- [ ] GitHubにリポジトリ作成
- [ ] コードをプッシュ
- [ ] GitHub Pagesの有効化
- [ ] Actions の実行確認
- [ ] サイトへのアクセス確認

---

## 🆘 トラブルシューティング

### SSH接続が失敗する

```bash
# SSH鍵の権限を確認
chmod 600 ~/.ssh/id_ed25519_nhk
chmod 644 ~/.ssh/id_ed25519_nhk.pub

# SSH agentに追加
ssh-add ~/.ssh/id_ed25519_nhk

# 再テスト
ssh -T git@github-nhk
```

### Pushが拒否される

```bash
# リモートURLを確認
git remote -v

# 間違っている場合は修正
git remote set-url origin git@github-nhk:YOUR_NEW_USERNAME/nhk-news-tracker.git
```

### GitHub Actionsが失敗する

1. **Actions** タブで失敗したワークフローをクリック
2. エラーログを確認
3. 多くの場合、依存関係の問題
4. `.github/workflows/deploy.yml` を確認

### ページが404エラー

1. Settings → Pages で設定を確認
2. gh-pages ブランチが存在するか確認
3. 数分待ってから再度アクセス

---

## 💡 次のステップ

### カスタムドメインの設定

独自ドメインを持っている場合：

1. Settings → Pages → Custom domain
2. `nhk-tracker.yourdomain.com` を入力
3. DNSプロバイダーでCNAMEレコードを追加：
   ```
   nhk-tracker  CNAME  YOUR_NEW_USERNAME.github.io.
   ```

### 更新頻度の変更

`.github/workflows/deploy.yml` を編集：

```yaml
schedule:
  # 現在: 1時間ごと
  - cron: '0 * * * *'

  # 変更例: 6時間ごと
  - cron: '0 */6 * * *'

  # 変更例: 毎日正午
  - cron: '0 12 * * *'
```

### プライベートリポジトリの公開設定

プライベートリポジトリでもGitHub Pagesは公開されます。
完全にプライベートにしたい場合は、Netlifyのパスワード保護機能を検討してください。

---

## 📞 サポート

その他の質問や問題がある場合は、以下を参照：
- `DEPLOY_SIMPLE.md` - 簡単なデプロイ方法
- `DEPLOYMENT.md` - 詳細なデプロイガイド
