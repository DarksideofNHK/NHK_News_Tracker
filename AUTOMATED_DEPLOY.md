# 自動デプロイ設定ガイド

ローカルで定期的にスクリプトを実行し、生成されたHTMLファイルを自動でアップロードする方法

## 🎯 基本方針

- ✅ **ローカルで実行**: サーバーでプログラムを動かさない
- ✅ **HTMLのみアップロード**: 必要なファイルだけをデプロイ
- ✅ **定期実行**: cronまたはlaunchd（macOS）で自動化

---

## 🚀 クイックスタート

### 手動実行（まずはこれから）

```bash
cd /Users/trudibussi/projects/gemini-cli/rss-diff-analyzer-python
./deploy_simple.sh
```

これだけで：
1. 最新データ取得
2. レポート生成
3. Netlifyへデプロイ（またはFinderを開いてドラッグ&ドロップ）

---

## ⏰ 自動実行の設定

### 方法1: macOS launchd（推奨）

cronよりも信頼性が高く、macOSに最適化されています。

#### ステップ1: plist ファイルを作成

```bash
cat > ~/Library/LaunchAgents/com.nhk.tracker.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.nhk.tracker</string>

    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/Users/trudibussi/projects/gemini-cli/rss-diff-analyzer-python/deploy_simple.sh</string>
    </array>

    <key>StartCalendarInterval</key>
    <dict>
        <key>Minute</key>
        <integer>0</integer>
    </dict>

    <key>StandardOutPath</key>
    <string>/tmp/nhk-tracker.log</string>

    <key>StandardErrorPath</key>
    <string>/tmp/nhk-tracker-error.log</string>

    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
EOF
```

**設定内容**:
- 毎時0分に実行（1時間ごと）
- ログは `/tmp/nhk-tracker.log` に保存
- エラーは `/tmp/nhk-tracker-error.log` に保存

#### ステップ2: 実行頻度のカスタマイズ（オプション）

**6時間ごとに実行:**
```xml
<key>StartCalendarInterval</key>
<array>
    <dict>
        <key>Hour</key>
        <integer>0</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <dict>
        <key>Hour</key>
        <integer>6</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <dict>
        <key>Hour</key>
        <integer>12</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <dict>
        <key>Hour</key>
        <integer>18</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
</array>
```

**毎日正午に実行:**
```xml
<key>StartCalendarInterval</key>
<dict>
    <key>Hour</key>
    <integer>12</integer>
    <key>Minute</key>
    <integer>0</integer>
</dict>
```

#### ステップ3: サービスを有効化

```bash
# 読み込み
launchctl load ~/Library/LaunchAgents/com.nhk.tracker.plist

# 状態確認
launchctl list | grep nhk

# ログを確認
tail -f /tmp/nhk-tracker.log
```

#### ステップ4: 停止・再起動

```bash
# 停止
launchctl unload ~/Library/LaunchAgents/com.nhk.tracker.plist

# 再起動（設定変更後など）
launchctl unload ~/Library/LaunchAgents/com.nhk.tracker.plist
launchctl load ~/Library/LaunchAgents/com.nhk.tracker.plist
```

---

### 方法2: cron（シンプル）

```bash
# crontabを編集
crontab -e

# 以下を追加
# 1時間ごとに実行
0 * * * * cd /Users/trudibussi/projects/gemini-cli/rss-diff-analyzer-python && /bin/bash deploy_simple.sh >> /tmp/nhk-deploy.log 2>&1

# または、6時間ごとに実行
0 */6 * * * cd /Users/trudibussi/projects/gemini-cli/rss-diff-analyzer-python && /bin/bash deploy_simple.sh >> /tmp/nhk-deploy.log 2>&1
```

**cron書式の説明:**
```
* * * * *
│ │ │ │ │
│ │ │ │ └─── 曜日 (0-6, 日曜=0)
│ │ │ └───── 月 (1-12)
│ │ └─────── 日 (1-31)
│ └───────── 時 (0-23)
└─────────── 分 (0-59)
```

**例:**
- `0 * * * *` - 毎時0分
- `0 */6 * * *` - 6時間ごと
- `0 9,18 * * *` - 毎日9時と18時
- `0 12 * * *` - 毎日正午

**ログ確認:**
```bash
tail -f /tmp/nhk-deploy.log
```

---

## 📋 デプロイ方法の選択

### オプションA: Netlify CLI（完全自動）

**初回セットアップ:**
```bash
# Netlify CLIをインストール
npm install -g netlify-cli

# ログイン
netlify login

# プロジェクトをリンク
cd /Users/trudibussi/projects/gemini-cli/rss-diff-analyzer-python
netlify init
```

**以降は自動:**
`deploy_simple.sh` を実行すると自動でNetlifyへデプロイされます。

---

### オプションB: Netlify Drop（手動）

**手順:**
1. cron/launchdで `python3 main_hybrid.py` のみを実行
2. 好きなタイミングで `reports` フォルダを https://app.netlify.com/drop へドラッグ&ドロップ

**設定例（レポート生成のみ自動化）:**
```bash
# launchdの場合
<key>ProgramArguments</key>
<array>
    <string>/usr/bin/python3</string>
    <string>/Users/trudibussi/projects/gemini-cli/rss-diff-analyzer-python/main_hybrid.py</string>
</array>

# cronの場合
0 * * * * cd /Users/trudibussi/projects/gemini-cli/rss-diff-analyzer-python && /usr/bin/python3 main_hybrid.py >> /tmp/nhk-scrape.log 2>&1
```

---

### オプションC: GitHub Pages（完全自動・サーバー実行）

GitHub Actionsでサーバー側で実行したい場合は、`SETUP_NEW_GITHUB.md` を参照してください。

ただし、今回の方針（ローカル実行優先）とは異なります。

---

## 🔧 トラブルシューティング

### launchdが実行されない

```bash
# ログを確認
cat /tmp/nhk-tracker.log
cat /tmp/nhk-tracker-error.log

# 権限を確認
ls -la ~/Library/LaunchAgents/com.nhk.tracker.plist

# plistの構文チェック
plutil -lint ~/Library/LaunchAgents/com.nhk.tracker.plist
```

### cronが実行されない

```bash
# cronログを確認（macOS）
log show --predicate 'process == "cron"' --last 1h

# スクリプトが実行可能か確認
ls -la deploy_simple.sh

# 手動で実行してエラーを確認
bash -x deploy_simple.sh
```

### Netlify CLIの認証エラー

```bash
# 再ログイン
netlify logout
netlify login

# トークンを確認
netlify status
```

### ChromeDriverのエラー

```bash
# undetected-chromedriverを再インストール
/usr/bin/python3 -m pip uninstall -y undetected-chromedriver
/usr/bin/python3 -m pip install undetected-chromedriver

# Chromeのバージョンを確認
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version
```

---

## 📊 実行状況の確認

### ログの監視

**リアルタイム表示:**
```bash
# launchdの場合
tail -f /tmp/nhk-tracker.log

# cronの場合
tail -f /tmp/nhk-deploy.log
```

**過去のログ検索:**
```bash
# エラーのみ表示
grep "エラー\|失敗\|ERROR" /tmp/nhk-tracker.log

# 成功した実行のみ
grep "✅\|完了" /tmp/nhk-tracker.log

# 最新10回の実行結果
grep "━━━" /tmp/nhk-tracker.log | tail -20
```

### データベースの確認

```bash
# SQLiteでデータベースを直接確認
sqlite3 data/articles.db "SELECT COUNT(*) as total_articles FROM articles;"
sqlite3 data/articles.db "SELECT source, COUNT(*) FROM articles GROUP BY source;"

# 最新の訂正記事
sqlite3 data/articles.db "SELECT title, source, fetched_at FROM articles WHERE is_correction=1 ORDER BY fetched_at DESC LIMIT 10;"
```

### Webサイトの確認

**Netlify:**
- ダッシュボード: https://app.netlify.com
- デプロイ履歴と自動更新の状態を確認

**GitHub Pages:**
- Actions: https://github.com/YOUR_USERNAME/nhk-news-tracker/actions
- ワークフローの実行履歴を確認

---

## 💡 おすすめの運用方法

### パターン1: 完全自動（推奨）

```
launchd（1時間ごと）
  ↓
ローカルでmain_hybrid.py実行
  ↓
Netlify CLI で自動デプロイ
```

**メリット:**
- 完全に手放しで運用可能
- ローカルで実行するのでSelenium問題なし
- サーバーコスト0円

---

### パターン2: 半自動

```
launchd（1時間ごと）
  ↓
ローカルでmain_hybrid.py実行
  ↓
手動でNetlify Dropへドラッグ&ドロップ
```

**メリット:**
- デプロイのタイミングを手動で制御
- 内容を確認してから公開可能

---

### パターン3: 完全手動

```
好きなタイミングで deploy_simple.sh を実行
```

**メリット:**
- 最もシンプル
- 自分のペースで運用

---

## 🎉 まとめ

**最小構成（完全自動）:**

1. Netlify CLIをセットアップ
   ```bash
   npm install -g netlify-cli
   netlify login
   cd /Users/trudibussi/projects/gemini-cli/rss-diff-analyzer-python
   netlify init
   ```

2. launchdを設定
   ```bash
   # plistファイルを作成（上記の内容）
   launchctl load ~/Library/LaunchAgents/com.nhk.tracker.plist
   ```

3. 完了！

これで毎時0分に自動で：
- ✅ 最新ニュースを取得
- ✅ 訂正記事を検出
- ✅ HTMLレポートを生成
- ✅ Netlifyへ自動デプロイ

すべてローカルで実行されるため、サーバー側でのプログラム実行は不要です。

---

## 📞 参考資料

- **デプロイ方法の詳細**: `DEPLOY_SIMPLE.md`
- **GitHub Pages設定**: `SETUP_NEW_GITHUB.md`
- **完全なデプロイガイド**: `DEPLOYMENT.md`
- **Netlify設定**: `deploy_netlify.sh`
