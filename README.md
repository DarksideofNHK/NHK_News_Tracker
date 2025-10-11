# NHK RSS差分追跡システム

NHKニュースのRSSフィードを監視し、記事の変更（タイトル・説明文の修正、訂正など）を自動追跡するシステムです。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

## ✨ 主な機能

- **自動監視**: 7つのNHK地域ニュースを毎時チェック
- **変更検出**: タイトル・説明文の変更を自動検出
- **訂正追跡**: 訂正記事を自動識別
- **AI分析**: Gemini APIによる変更内容の分析（オプション）
- **履歴管理**: 全ての変更履歴をデータベースに保存
- **HTMLレポート**: 見やすいWebインターフェースで確認

### 監視対象（7ソース）

1. NHK首都圏ニュース
2. NHK福岡ニュース
3. NHK札幌ニュース
4. NHK東海ニュース
5. NHK広島ニュース
6. NHK関西ニュース
7. NHK東北ニュース（Selenium使用・認証対応）

## 📋 必要要件

- Python 3.9以上
- Chrome/Chromium（NHK東北ニュース用）
- Gemini API Key（AI分析機能を使う場合）

## 🚀 クイックスタート

### 1. リポジトリのクローン

```bash
git clone https://github.com/Trudibussi/NHK_News_Tracker.git
cd NHK_News_Tracker
```

### 2. セットアップスクリプトの実行

```bash
python3 setup.py
```

セットアップスクリプトが以下を対話的に行います：
- `.env`ファイルの作成とAPI キーの設定
- 必要なディレクトリの作成
- LaunchAgent の設定（macOS）

### 3. 依存パッケージのインストール

```bash
python3 -m pip install --user -r requirements.txt
```

### 4. NHK東北用の認証設定（重要）

NHK東北ニュースにアクセスするには、初回に同意ダイアログをOKする必要があります：

```bash
python3 setup_consent_auto.py
```

ブラウザが開いたら、同意ダイアログを確認してください。

### 5. テスト実行

```bash
python3 main_hybrid.py
```

成功すると、`reports/`ディレクトリにHTMLレポートが生成されます。

## 📁 生成されるファイル

### HTMLレポート（`reports/`ディレクトリ）

- `changes_YYYYMMDD_HHMMSS.html` - 過去24時間の変更レポート
- `history.html` - 全変更履歴（diff表示付き）
- `archive.html` - 全記事アーカイブ（検索・フィルター機能付き）

### データベース

- `data/articles.db` - SQLiteデータベース（記事と変更履歴）

### ログ

- `logs/launchd.log` - 自動実行ログ（macOS）
- `logs/nhk_tracker.log` - 詳細ログ

## ⚙️ 設定

### 環境変数（`.env`ファイル）

```bash
# Gemini API Key（AI分析機能用・オプション）
GEMINI_API_KEY=your_api_key_here
```

Gemini API Keyの取得方法：
1. https://aistudio.google.com/app/apikey にアクセス
2. 「Create API Key」をクリック
3. 生成されたAPIキーをコピー
4. `.env`ファイルに貼り付け

### 監視設定（`config.yaml`）

監視対象のソースや取得間隔を変更できます：

```yaml
sources:
  - name: "NHK首都圏ニュース"
    url: "https://www.nhk.or.jp/shutoken-news/news_all_search.xml"
    enabled: true

report:
  output_dir: "reports"
  hours: 24  # レポート対象期間
```

## 🔧 自動実行の設定

### macOS（LaunchAgent）

セットアップスクリプトで自動設定されます。

```bash
# LaunchAgentの状態確認
launchctl list | grep nhk

# 手動実行（テスト）
launchctl start com.nhk.rss-tracker

# 停止
launchctl unload ~/Library/LaunchAgents/com.nhk.rss-tracker.plist

# 再開
launchctl load ~/Library/LaunchAgents/com.nhk.rss-tracker.plist
```

### Linux/その他のOS

cronを使用：

```bash
# crontab -e
# 毎時0分に実行
0 * * * * cd /path/to/NHK_News_Tracker && /usr/bin/python3 main_hybrid.py
```

## 📊 使用方法

### Webインターフェースで確認

```bash
# 最新レポートを開く
open reports/changes_*.html

# 全変更履歴を開く
open reports/history.html

# 全記事アーカイブを開く
open reports/archive.html
```

### 手動実行

```bash
# メインスクリプト実行
python3 main_hybrid.py

# 履歴ビューアー生成
python3 generate_history.py

# アーカイブビューアー生成
python3 generate_archive.py

# 週次レポート生成
python3 generate_weekly_report.py 7  # 過去7日間
```

## 🏗️ プロジェクト構造

```
NHK_News_Tracker/
├── main_hybrid.py          # メインスクリプト
├── setup.py                # セットアップスクリプト
├── config.yaml             # 設定ファイル
├── .env                    # 環境変数（gitignore対象）
├── .env.example            # 環境変数サンプル
├── requirements.txt        # Python依存パッケージ
│
├── scraper_hybrid.py       # RSSスクレイパー
├── parser.py               # XMLパーサー
├── storage.py              # データベース管理
├── visualizer.py           # HTMLレポート生成
├── gemini_analyzer.py      # AI分析（Gemini API）
│
├── generate_history.py     # 全変更履歴ビューアー
├── generate_archive.py     # 全記事アーカイブビューアー
├── generate_weekly_report.py # 週次レポート
│
├── data/                   # データベース
│   └── articles.db
├── logs/                   # ログファイル
├── reports/                # HTMLレポート
└── README.md
```

## 🔒 セキュリティとプライバシー

- **APIキー管理**: `.env`ファイルで管理（gitignore済み）
- **ローカル実行**: 全てのデータはローカルに保存
- **外部送信なし**: 記事データは外部サーバーに送信されません（Gemini API使用時を除く）

## 🐛 トラブルシューティング

### APIキーが読み込まれない

```bash
# .envファイルの存在確認
cat .env

# 環境変数の確認
python3 -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('GEMINI_API_KEY'))"
```

### LaunchAgentが起動しない（macOS）

```bash
# ログ確認
tail -f logs/launchd.error.log

# LaunchAgentの再起動
launchctl unload ~/Library/LaunchAgents/com.nhk.rss-tracker.plist
launchctl load ~/Library/LaunchAgents/com.nhk.rss-tracker.plist
```

### NHK東北のみエラーが発生

```bash
# 認証プロファイルを再作成
python3 setup_consent_auto.py
```

### データベースエラー

```bash
# データベースの整合性チェック
sqlite3 data/articles.db "PRAGMA integrity_check;"
```

## 🧪 テスト

```bash
# NHK東北単体テスト
python3 test_saved_profile.py

# 全ソーステスト
python3 test_hybrid.py

# 完全パイプラインテスト
./run.sh
```

## 📝 ライセンス

MIT License - 詳細は[LICENSE](LICENSE)ファイルを参照してください。

## 🤝 貢献

Issue・Pull Requestは歓迎です。

1. このリポジトリをフォーク
2. フィーチャーブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add some amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. Pull Requestを作成

## 📮 お問い合わせ

Issue tracker: https://github.com/Trudibussi/NHK_News_Tracker/issues

## 🙏 謝辞

- NHKニュースのRSSフィード
- Google Gemini API
- [undetected-chromedriver](https://github.com/ultrafunkamsterdam/undetected-chromedriver)

## 📈 実績

- 全7ソース: 100%成功率
- 約800記事/回を自動取得
- タイトル・説明文の変更検出
- 訂正記事の自動追跡
- AI分析による変更内容の要約

---

**バージョン**: 3.2.0
**最終更新**: 2025-10-11
