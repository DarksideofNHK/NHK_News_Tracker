# クイックコマンドリファレンス

よく使うコマンドのチートシート

## 🚀 基本実行

```bash
# プロジェクトディレクトリへ移動
cd /Users/trudibussi/projects/gemini-cli/rss-diff-analyzer-python

# データ取得とレポート生成のみ
/usr/bin/python3 main_hybrid.py

# データ取得 + Netlifyへ自動デプロイ
./deploy_simple.sh

# データ取得 + デプロイ先を選択
./deploy_static.sh
```

---

## 📊 確認・監視

```bash
# データベース統計
sqlite3 data/articles.db "SELECT source, COUNT(*) FROM articles GROUP BY source;"

# 訂正記事の数
sqlite3 data/articles.db "SELECT COUNT(*) FROM articles WHERE is_correction=1;"

# 最新の訂正記事（10件）
sqlite3 data/articles.db "SELECT title, source FROM articles WHERE is_correction=1 ORDER BY fetched_at DESC LIMIT 10;"

# 生成されたHTMLファイル数
find reports -name "*.html" | wc -l

# 最新のレポートを開く
open reports/index.html
```

---

## ⏰ 自動実行の管理（launchd）

```bash
# サービスを開始
launchctl load ~/Library/LaunchAgents/com.nhk.tracker.plist

# サービスを停止
launchctl unload ~/Library/LaunchAgents/com.nhk.tracker.plist

# サービスの状態確認
launchctl list | grep nhk

# ログをリアルタイム表示
tail -f /tmp/nhk-tracker.log

# エラーログを表示
tail -f /tmp/nhk-tracker-error.log
```

---

## ⏰ 自動実行の管理（cron）

```bash
# cron設定を編集
crontab -e

# cron設定を表示
crontab -l

# cronログを表示（macOS）
log show --predicate 'process == "cron"' --last 1h
```

---

## 🌐 Netlify関連

```bash
# Netlifyにログイン
netlify login

# 現在のサイト情報を確認
netlify status

# 手動でデプロイ
netlify deploy --prod --dir=reports

# サイトをブラウザで開く
netlify open

# デプロイ履歴を表示
netlify watch
```

---

## 🔧 トラブルシューティング

```bash
# 依存パッケージを再インストール
/usr/bin/python3 -m pip install -r requirements.txt --upgrade

# ChromeDriverをリセット
/usr/bin/python3 -m pip uninstall -y undetected-chromedriver
/usr/bin/python3 -m pip install undetected-chromedriver

# Chromeのバージョン確認
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version

# NHK ONE検索のテスト
/usr/bin/python3 test_nhk_one_search.py

# 権限を修正
chmod +x deploy_simple.sh deploy_static.sh deploy_netlify.sh deploy_github.sh

# データベースのバックアップ
cp data/articles.db data/articles_backup_$(date +%Y%m%d_%H%M%S).db
```

---

## 📁 ファイル構造の確認

```bash
# プロジェクト構造を表示
tree -L 2 -I '__pycache__|*.pyc'

# reportsフォルダの中身
ls -lh reports/

# データベースのサイズ
du -h data/articles.db

# 総ディスク使用量
du -sh .
```

---

## 🧪 テスト・デバッグ

```bash
# 単一RSS feedのテスト
/usr/bin/python3 -c "from scraper_hybrid import NhkRssScraperHybrid; s = NhkRssScraperHybrid(); print(s.fetch_rss('https://www3.nhk.or.jp/fukuoka-news/news_all_search.xml'))"

# NHK ONE検索のテスト
/usr/bin/python3 test_nhk_one_search.py

# デバッグモードで実行
/usr/bin/python3 main_hybrid.py --verbose

# ログファイルを監視しながら実行
/usr/bin/python3 main_hybrid.py 2>&1 | tee /tmp/nhk-debug.log
```

---

## 📤 デプロイオプション

```bash
# オプション1: Netlify CLI（最も簡単・自動）
netlify deploy --prod --dir=reports

# オプション2: Netlify Drop（手動）
open reports  # Finderを開いて https://app.netlify.com/drop へドラッグ

# オプション3: GitHub Pages（手動プッシュ）
./deploy_github.sh

# オプション4: カスタムサーバー（rsync）
rsync -avz --delete reports/ user@server:/var/www/html/
```

---

## 🔄 定期実行の設定

### 1時間ごと（launchd）

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
</dict>
</plist>
EOF

launchctl load ~/Library/LaunchAgents/com.nhk.tracker.plist
```

### 1時間ごと（cron）

```bash
crontab -e
# 追加:
0 * * * * cd /Users/trudibussi/projects/gemini-cli/rss-diff-analyzer-python && /bin/bash deploy_simple.sh >> /tmp/nhk-deploy.log 2>&1
```

---

## 🎨 レポートのカスタマイズ

```bash
# ポータルページのテンプレートを編集
nano generate_portal.py

# 色やスタイルを変更
# 訂正ハイライトの色: line 98-102 (correction-notice)
# 背景色: #ffeb3b (黄色)
# テキスト色: #d32f2f (赤)

# 変更後、レポートを再生成
/usr/bin/python3 main_hybrid.py
```

---

## 🗑️ クリーンアップ

```bash
# 古いレポートを削除（30日以上前）
find reports -name "*.html" -mtime +30 -delete

# データベースをリセット（注意！全データ削除）
rm data/articles.db
/usr/bin/python3 main_hybrid.py  # 新規作成される

# ログファイルをクリア
> /tmp/nhk-tracker.log
> /tmp/nhk-tracker-error.log
```

---

## 📋 よくある操作フロー

### 初めて実行する

```bash
cd /Users/trudibussi/projects/gemini-cli/rss-diff-analyzer-python
/usr/bin/python3 -m pip install -r requirements.txt
/usr/bin/python3 main_hybrid.py
open reports/index.html
```

### 手動デプロイ

```bash
cd /Users/trudibussi/projects/gemini-cli/rss-diff-analyzer-python
./deploy_simple.sh
```

### 自動デプロイを設定

```bash
# Netlify CLIセットアップ
npm install -g netlify-cli
netlify login
cd /Users/trudibussi/projects/gemini-cli/rss-diff-analyzer-python
netlify init

# launchd設定（上記参照）
launchctl load ~/Library/LaunchAgents/com.nhk.tracker.plist

# 確認
tail -f /tmp/nhk-tracker.log
```

### トラブル時

```bash
# ログを確認
tail -100 /tmp/nhk-tracker.log
cat /tmp/nhk-tracker-error.log

# 手動実行してエラーを特定
/usr/bin/python3 main_hybrid.py

# 依存関係を再インストール
/usr/bin/python3 -m pip install -r requirements.txt --upgrade

# ChromeDriverをリセット
/usr/bin/python3 -m pip uninstall -y undetected-chromedriver
/usr/bin/python3 -m pip install undetected-chromedriver
```

---

## 📚 詳細ガイド

- **自動実行の設定**: `AUTOMATED_DEPLOY.md`
- **簡単なデプロイ**: `DEPLOY_SIMPLE.md`
- **GitHub設定**: `SETUP_NEW_GITHUB.md`
- **完全ガイド**: `DEPLOYMENT.md`

---

## 💡 ヒント

- **ログを監視しながら実行**: `tail -f /tmp/nhk-tracker.log`
- **エラー時は手動実行**: `./deploy_simple.sh` で詳細を確認
- **定期的なバックアップ**: `cp data/articles.db data/backup.db`
- **HTMLを確認してからデプロイ**: `open reports/index.html`
