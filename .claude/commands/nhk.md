---
description: NHK News Tracker プロジェクトの保守管理コマンド
---

# NHK News Tracker - プロジェクトコンテキスト

あなたは **NHK記事追跡システム** の保守管理を行います。

## プロジェクト概要

**プロジェクト名**: NHK News Tracker
**場所**: `/Users/trudibussi/projects/gemini-cli/rss-diff-analyzer-python/`
**目的**: NHK地方局ニュースを24時間監視し、記事の訂正・変更を自動検出
**デプロイ先**: https://nhk-news-tracker.netlify.app
**GitHub**: https://github.com/DarksideofNHK/NHK_News_Tracker (ソースコード公開用)

## アーキテクチャ

- **データ収集**: `main_hybrid.py` - RSSフィード7ソース + Selenium 2ソース
- **差分検出**: SQLiteで前回との差分を検出、訂正キーワード自動検出
- **HTML生成**: `generate_portal.py`, `generate_history.py`, `generate_archive.py`
- **デプロイ**: Netlify CLI経由（`netlify deploy --prod --dir=reports`）

## 重要ファイル

- `CLAUDE.md` - 詳細な技術仕様と運用ガイド
- `README.md` - オープンソースプロジェクトとしての公開用ドキュメント
- `data/articles.db` - SQLiteデータベース
- `reports/` - 生成されたHTML（Netlifyデプロイ対象）
- `netlify.toml` - Netlify設定
- `.env` - API Key（GEMINI_API_KEY必須）

## よく使うコマンド

```bash
# 記事収集と更新検出
/usr/bin/python3 main_hybrid.py

# HTMLページ生成
/usr/bin/python3 generate_portal.py
/usr/bin/python3 generate_history.py
/usr/bin/python3 generate_archive.py

# Netlifyデプロイ
netlify deploy --prod --dir=reports

# 全自動実行（推奨）
/usr/bin/python3 main_hybrid.py && \
/usr/bin/python3 generate_portal.py && \
/usr/bin/python3 generate_history.py && \
/usr/bin/python3 generate_archive.py && \
netlify deploy --prod --dir=reports
```

## デプロイ構成

- **GitHub**: ソースコード公開のみ（GitHub Actionsは無効化済み）
- **Netlify**: 実運用サイト（手動デプロイ）
- **ワークフロー**: ローカル実行 → HTML生成 → Netlifyアップロード

## トラブルシューティング

### よくある問題

1. **Selenium/ChromeDriverエラー**
   - `setup_consent_auto.py`を再実行
   - NHK東北の同意ダイアログを確認

2. **訂正記事が表示されない**
   - 検出条件: `(※ + 当初 + 掲載)` OR `(※ + 失礼しました)`
   - `description`フィールドを確認

3. **note.com記事が取得できない**
   - `feedparser`, `beautifulsoup4`がインストールされているか確認

4. **NHK東北ニュースのリンクが404**
   - `get_full_url()`の正規表現を確認（`generate_archive.py`, `generate_history.py`）

## 保守作業時の注意

- CLAUDE.mdを必ず参照してから作業を開始
- データベース変更時はバックアップを取得
- HTML生成スクリプト変更時はローカルで確認してからデプロイ
- 著作権対応：記事本文は最大150-200文字の要約のみ表示

## 現在のタスク

ユーザーの要望を確認し、以下のいずれかの作業を実施してください：

- **機能追加**: 新しいRSSソース追加、検出ロジック改善等
- **バグ修正**: エラー対応、表示不具合修正等
- **デプロイ**: 最新版の公開
- **ドキュメント更新**: README、CLAUDE.md等の更新
- **その他**: ユーザーの要望に応じて対応

ユーザーに何をしたいか質問してください。
