# デプロイ関連ファイル一覧

このプロジェクトのデプロイに関する全ファイルのガイド

## 📋 目的別ガイド

### 初めてデプロイする

1. **`DEPLOY_SIMPLE.md`** - 最も簡単な方法から始める
2. **`QUICK_COMMANDS.md`** - よく使うコマンドを手元に置く

### 完全自動化したい

1. **`AUTOMATED_DEPLOY.md`** - 自動実行の詳細設定
2. **`deploy_simple.sh`** - 実行するスクリプト

### 新しいGitHubアカウントを使う

1. **`SETUP_NEW_GITHUB.md`** - ステップバイステップ設定

---

## 📄 全ファイル一覧

### ドキュメント（マークダウン）

| ファイル | 内容 | 対象者 |
|---------|------|--------|
| `README.md` | プロジェクト全体の説明 | 全員 |
| `QUICK_COMMANDS.md` | よく使うコマンド集 | 全員（手元に置く） |
| `DEPLOY_SIMPLE.md` | 最も簡単なデプロイ方法 | 初心者 |
| `AUTOMATED_DEPLOY.md` | 自動実行の詳細ガイド | 自動化したい人 |
| `SETUP_NEW_GITHUB.md` | GitHub新規アカウント設定 | GitHub使う人 |
| `DEPLOYMENT.md` | 完全なデプロイガイド | 詳細を知りたい人 |
| `QUICKSTART_DEPLOY.md` | 5分クイックスタート | すぐ始めたい人 |
| `DEPLOYMENT_FILES.md` | このファイル | 全体像を知りたい人 |

### スクリプト（実行ファイル）

| ファイル | 用途 | 使用場面 |
|---------|------|---------|
| `deploy_simple.sh` | **簡単デプロイ（推奨）** | 日常的な運用 |
| `deploy_static.sh` | デプロイ先選択式 | 初回設定や切替時 |
| `deploy_netlify.sh` | Netlify専用 | Netlifyのみ使う場合 |
| `deploy_github.sh` | GitHub Pages専用 | GitHub Pagesのみ使う場合 |

### 設定ファイル

| ファイル | 内容 | 必要性 |
|---------|------|--------|
| `netlify.toml` | Netlify設定 | Netlify使用時 |
| `.github/workflows/deploy.yml` | GitHub Actions設定 | GitHub Pages使用時 |
| `~/Library/LaunchAgents/com.nhk.tracker.plist` | macOS自動実行設定 | 自動化する場合 |

---

## 🚀 使い方フロー

### フロー1: 最速で試す（3分）

```
1. DEPLOY_SIMPLE.md を読む
2. ローカルでデータ取得
   → python3 main_hybrid.py
3. Netlify Dropへドラッグ&ドロップ
   → https://app.netlify.com/drop
```

### フロー2: 自動化する（15分）

```
1. AUTOMATED_DEPLOY.md を読む
2. Netlify CLIをセットアップ
   → npm install -g netlify-cli
   → netlify login
   → netlify init
3. launchdを設定
   → plistファイル作成
   → launchctl load
4. 完了！毎時自動実行
```

### フロー3: GitHubで完全自動化（30分）

```
1. SETUP_NEW_GITHUB.md を読む
2. GitHubアカウント作成
3. SSH鍵設定
4. リポジトリ作成＆プッシュ
5. GitHub Pagesを有効化
6. 完了！1時間ごと自動更新
```

---

## 📊 デプロイ方法の比較

| 方法 | 難易度 | 自動化 | コスト | おすすめ度 |
|------|--------|--------|--------|-----------|
| Netlify Drop | ⭐ | 手動 | 無料 | ⭐⭐⭐⭐ |
| Netlify CLI | ⭐⭐ | 可能 | 無料 | ⭐⭐⭐⭐⭐ |
| GitHub Pages | ⭐⭐⭐ | 完全自動 | 無料 | ⭐⭐⭐⭐ |
| rsync | ⭐⭐⭐⭐ | 可能 | サーバー費用 | ⭐⭐ |

---

## 🎯 シナリオ別おすすめ

### 「今すぐ公開したい！」

→ **Netlify Drop** (`DEPLOY_SIMPLE.md`)
- ドキュメント: `DEPLOY_SIMPLE.md`
- 所要時間: 3分
- スキル: 不要

### 「手間をかけずに自動運用したい」

→ **Netlify CLI + launchd** (`AUTOMATED_DEPLOY.md`)
- スクリプト: `deploy_simple.sh`
- ドキュメント: `AUTOMATED_DEPLOY.md`
- 所要時間: 15分（初回のみ）
- スキル: ターミナル基本操作

### 「GitHubで管理したい」

→ **GitHub Pages + Actions** (`SETUP_NEW_GITHUB.md`)
- ドキュメント: `SETUP_NEW_GITHUB.md`
- 所要時間: 30分（初回のみ）
- スキル: Git基本操作

### 「自前サーバーに置きたい」

→ **rsync** (`deploy_static.sh`)
- スクリプト: `deploy_static.sh`（オプション3を選択）
- ドキュメント: `DEPLOYMENT.md`
- 所要時間: 環境による
- スキル: サーバー管理

---

## 🔧 各スクリプトの詳細

### `deploy_simple.sh`（推奨）

**用途**: 最もシンプルなデプロイスクリプト

**実行内容**:
1. `python3 main_hybrid.py` でデータ取得とレポート生成
2. Netlify CLIがあれば自動デプロイ
3. なければFinderを開いてドラッグ&ドロップを案内

**使い方**:
```bash
cd /Users/trudibussi/projects/gemini-cli/rss-diff-analyzer-python
./deploy_simple.sh
```

**対象者**: 全員

---

### `deploy_static.sh`

**用途**: デプロイ先を選択できる汎用スクリプト

**実行内容**:
1. `python3 main_hybrid.py` でデータ取得とレポート生成
2. デプロイ先を選択:
   - GitHub Pages (gh-pages ブランチ)
   - Netlify CLI
   - rsync (自前サーバー)

**使い方**:
```bash
./deploy_static.sh
# 1-3を選択
```

**対象者**: 複数のデプロイ先を試したい人

---

### `deploy_netlify.sh`

**用途**: Netlify専用の簡潔なスクリプト

**実行内容**:
1. `python3 main_hybrid.py` でデータ取得
2. `netlify deploy --prod --dir=reports`

**使い方**:
```bash
./deploy_netlify.sh
```

**対象者**: Netlifyのみを使う人

---

### `deploy_github.sh`

**用途**: GitHub Pages専用の手動プッシュスクリプト

**実行内容**:
1. `python3 main_hybrid.py` でデータ取得
2. reportsをgh-pagesブランチへプッシュ

**使い方**:
```bash
./deploy_github.sh
```

**対象者**: GitHub Pagesを手動でプッシュしたい人

---

## 📚 ドキュメントの詳細

### `README.md`

**内容**: プロジェクト全体の説明
- システム概要
- インストール方法
- 基本的な使い方
- デプロイ方法の概要（新規追加）

**読むべきタイミング**: 最初に

---

### `QUICK_COMMANDS.md`

**内容**: よく使うコマンドのチートシート
- 基本実行コマンド
- 確認・監視コマンド
- launchd/cron管理
- Netlify操作
- トラブルシューティング

**読むべきタイミング**: 日常的に参照

---

### `DEPLOY_SIMPLE.md`

**内容**: 最も簡単なデプロイ方法
- Netlify Drop（ドラッグ&ドロップ）
- GitHub Pages（自動更新）
- 各方法の比較

**読むべきタイミング**: 初めてデプロイする時

---

### `AUTOMATED_DEPLOY.md`

**内容**: 自動実行の詳細ガイド
- macOS launchd設定
- cron設定
- 実行頻度のカスタマイズ
- ログ監視
- トラブルシューティング

**読むべきタイミング**: 自動化したい時

---

### `SETUP_NEW_GITHUB.md`

**内容**: GitHub新規アカウントでのセットアップ
- アカウント設定
- SSH鍵作成
- リポジトリ作成
- GitHub Pages設定
- GitHub Actions設定

**読むべきタイミング**: GitHubを使う時

---

### `DEPLOYMENT.md`

**内容**: 完全なデプロイガイド
- 全デプロイ方法の詳細
- Netlify設定
- GitHub Actions設定
- Cloudflare Pages設定
- カスタムドメイン設定

**読むべきタイミング**: 詳細を知りたい時

---

### `QUICKSTART_DEPLOY.md`

**内容**: 5分で始めるクイックスタート
- Netlify Drop（3分）
- GitHub Pages（10分）
- 最小限の手順のみ

**読むべきタイミング**: すぐに始めたい時

---

## 💡 実践的な使い方

### ケース1: 初めて使う

```bash
# 1. プロジェクトを理解
README.md を読む

# 2. ローカルで実行してみる
python3 main_hybrid.py
open reports/index.html

# 3. 簡単にデプロイ
DEPLOY_SIMPLE.md を読む
→ Netlify Dropへドラッグ&ドロップ
```

### ケース2: 本格運用を開始

```bash
# 1. 自動化ガイドを読む
AUTOMATED_DEPLOY.md を読む

# 2. Netlify CLIセットアップ
npm install -g netlify-cli
netlify login
netlify init

# 3. launchdを設定
plistファイル作成
launchctl load

# 4. QUICK_COMMANDS.mdをブックマーク
```

### ケース3: 困った時

```bash
# 1. クイックコマンドでトラブルシューティング
QUICK_COMMANDS.md の「🔧 トラブルシューティング」セクション

# 2. ログを確認
tail -f /tmp/nhk-tracker.log

# 3. 手動実行でエラー特定
python3 main_hybrid.py
```

---

## 🎉 まとめ

### ファイル数

- **ドキュメント**: 8ファイル
- **スクリプト**: 4ファイル
- **設定ファイル**: 2-3ファイル（環境による）

### 推奨ワークフロー

```
1. README.md で全体を理解
2. DEPLOY_SIMPLE.md でまず試す
3. AUTOMATED_DEPLOY.md で自動化
4. QUICK_COMMANDS.md を日常的に参照
```

### サポート

困った時は以下を確認:
1. `QUICK_COMMANDS.md` のトラブルシューティング
2. 各ガイドのトラブルシューティングセクション
3. ログファイル (`/tmp/nhk-tracker.log`)

---

**最終更新**: 2025-10-12
**対応バージョン**: v4.0.0
