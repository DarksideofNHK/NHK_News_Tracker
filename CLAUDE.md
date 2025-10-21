# NHK記事追跡システム - Claude Code 引き継ぎメモ

> **このファイルについて**: プロジェクトディレクトリで作業する際、自動的に読み込まれます。
> 保守管理や更新を行う際は、このドキュメントを参照してください。

## 🚀 よく使う保守管理タスク

### タスク1: 最新記事を収集してデプロイ
```bash
/usr/bin/python3 main_hybrid.py && \
/usr/bin/python3 generate_portal.py && \
/usr/bin/python3 generate_history.py && \
/usr/bin/python3 generate_archive.py && \
netlify deploy --prod --dir=reports
```

### タスク2: ローカルでプレビュー
```bash
cd reports && python3 -m http.server 8000
# http://localhost:8000 で確認
```

### タスク3: GitHubにコミット&プッシュ
```bash
git add .
git commit -m "説明"
git push
```

### タスク4: データベースの確認
```bash
sqlite3 data/articles.db "SELECT COUNT(*) FROM articles;"
sqlite3 data/articles.db "SELECT COUNT(*) FROM changes WHERE has_correction = 1;"
```

---

## プロジェクト概要

**目的**: NHK地方局ニュースの記事を24時間監視し、訂正・変更を自動検出して可視化するシステム

**デプロイ先**: https://nhk-news-tracker.netlify.app
**GitHub**: https://github.com/DarksideofNHK/NHK_News_Tracker （ソースコード公開用）

**問題意識**: NHKは頻繁に誤情報を発信しているが、その実態が知られていない。本システムで報道の透明性と正確性を可視化する。

**デプロイ構成**:
- GitHub: ソースコード公開のみ（GitHub Actionsは無効化済み）
- Netlify: 実運用サイト（手動デプロイ）

---

## システムアーキテクチャ

### データフロー
```
RSS Feed取得 → 記事解析 → 差分検出 → DB保存 → HTML生成 → Netlify公開
```

### 主要コンポーネント
1. **データ収集**: `main_hybrid.py` - RSSフィード取得、記事スクレイピング
2. **差分検出**: SQLiteで前回との差分を検出、訂正キーワード（※、失礼しました、当初、掲載）を自動検出
3. **HTML生成**: `generate_*.py` - ポータル、履歴、アーカイブページを生成
4. **デプロイ**: Netlify CLI経由で自動デプロイ

---

## ファイル構成

```
/Users/trudibussi/projects/gemini-cli/rss-diff-analyzer-python/
├── main_hybrid.py              # メインスクリプト（RSS取得→解析→DB保存）
├── generate_portal.py          # ポータルページ生成（index.html）
├── generate_history.py         # 変更履歴ページ生成（history.html）
├── generate_archive.py         # 記事アーカイブページ生成（archive.html）
├── generate_assets.py          # OGP画像・ファビコン生成
├── data/
│   └── articles.db            # SQLiteデータベース
├── reports/                   # 生成されたHTML（Netlifyへデプロイ）
│   ├── index.html            # ポータル
│   ├── history.html          # 変更履歴
│   ├── archive.html          # 全記事アーカイブ
│   ├── ogp-image.png         # OGP画像（1200x630px）
│   ├── favicon.ico           # ファビコン
│   └── apple-touch-icon.png  # Apple用アイコン
├── netlify.toml              # Netlify設定
└── CLAUDE.md                 # このファイル
```

---

## 実行コマンド

### 1. 記事収集と更新検出
```bash
/usr/bin/python3 main_hybrid.py
```
- RSSフィードから最新記事を取得
- 既存記事との差分を検出
- 訂正記事を自動判定
- データベースに保存

### 2. HTMLページ生成
```bash
# ポータルページ生成（note.com RSS統合）
/usr/bin/python3 generate_portal.py

# 変更履歴ページ生成
/usr/bin/python3 generate_history.py

# 記事アーカイブページ生成
/usr/bin/python3 generate_archive.py
```

### 3. Netlifyデプロイ
```bash
# 本番環境へデプロイ
netlify deploy --prod --dir=reports

# プレビュー（テスト用）
netlify deploy --dir=reports
```

### 4. 全自動実行（推奨）
```bash
# 記事収集 → HTML生成 → デプロイを一括実行
/usr/bin/python3 main_hybrid.py && \
/usr/bin/python3 generate_portal.py && \
/usr/bin/python3 generate_history.py && \
/usr/bin/python3 generate_archive.py && \
netlify deploy --prod --dir=reports
```

---

## データベーススキーマ

### articlesテーブル
```sql
CREATE TABLE articles (
    id INTEGER PRIMARY KEY,
    source TEXT,              -- ソース名（NHK福岡ニュース等）
    title TEXT,               -- 記事タイトル
    link TEXT,                -- 記事URL（相対パス）
    description TEXT,         -- 記事本文
    pub_date TEXT,            -- 公開日時
    first_seen TEXT,          -- 初回検出日時
    last_checked TEXT,        -- 最終確認日時
    has_correction INTEGER,   -- 訂正記事フラグ（0/1）
    correction_keywords TEXT, -- 訂正キーワード
    UNIQUE(source, link)
);
```

### changesテーブル
```sql
CREATE TABLE changes (
    id INTEGER PRIMARY KEY,
    source TEXT,
    link TEXT,
    change_type TEXT,         -- new/title_changed/description_changed/description_added
    old_value TEXT,           -- 変更前の値
    new_value TEXT,           -- 変更後の値
    detected_at TEXT,         -- 検出日時
    has_correction INTEGER,   -- 訂正フラグ
    correction_keywords TEXT
);
```

---

## 訂正記事の検出ロジック

### 検出キーワード
- `※` + `当初` + `掲載` （3つすべて含む）
- `※` + `失礼しました`

### 検出対象
- 記事の`description`フィールド（本文）
- タイトル変更、説明文変更、説明文追記の3パターン

### 表示ロジック
- 訂正キーワードを含む**完全な文**を抽出（。で分割）
- ※マーカーを黄色背景+赤枠でハイライト
- 著作権対応: 最大150-200文字の要約表示

---

## 重要な設定

### URL変換ルール

**特殊ケース: NHK東北ニュース**
```python
# 相対パス: 20251009/6000033450.html
# → 正しいURL: https://news.web.nhk/newsweb/na/nb-6000033450
```
`generate_archive.py`と`generate_history.py`の`get_full_url()`で正規表現で変換。

**その他のソース**
```python
SOURCE_BASE_URLS = {
    'NHK首都圏ニュース': 'https://www3.nhk.or.jp/shutoken-news/',
    'NHK東海ニュース': 'https://www3.nhk.or.jp/tokai-news/',
    'NHK関西ニュース': 'https://www3.nhk.or.jp/kansai-news/',
    'NHK広島ニュース': 'https://www3.nhk.or.jp/hiroshima-news/',
    'NHK福岡ニュース': 'https://www3.nhk.or.jp/fukuoka-news/',
    'NHK札幌ニュース': 'https://www3.nhk.or.jp/sapporo-news/',
    'NHK東北ニュース': 'https://news.web.nhk/tohoku/',
    'NHK ONE検索': '',  # ベースURL無し
}
```

### note.com RSS統合

**RSS URL**: `https://note.com/darkside_of_nhk/rss`

**取得内容**:
- 最新3記事
- OGP画像（BeautifulSoup4でスクレイピング）
- タイトル、要約、リンク

**依存パッケージ**:
```bash
pip install feedparser beautifulsoup4
```

**表示比率**: OGP画像は16:9（`aspect-ratio: 16 / 9;`）

---

## デザイン仕様

### OGP画像
- サイズ: 1200x630px（1.91:1比率）
- グラデーション背景: 紫→青
- タイトル: 2行表示（90pxフォント）
- 3つの特徴を箇条書き表示

### カラースキーム
- プライマリ: `#667eea`（紫）
- セカンダリ: `#764ba2`（濃い紫）
- 訂正マーカー: `#ffeb3b`（黄色）+ `#d32f2f`（赤枠）
- 背景グラデーション: 紫→紫（`#667eea` → `#764ba2`）

### レスポンシブ対応
- 768px以下: グリッドを1カラムに変更
- 統計カードを2カラムに縮小

---

## トラブルシューティング

### 1. Netlifyデプロイが失敗する
**原因**: `netlify.toml`のbuildコマンドが設定されている
**解決**: buildコマンドを空にする
```toml
[build]
  command = ""
  publish = "reports"
```

### 2. note記事が取得できない
**原因**: feedparser/beautifulsoup4がインストールされていない
**解決**:
```bash
/usr/bin/python3 -m pip install feedparser beautifulsoup4
```

### 3. 統計情報が{stats['total_changes']}のまま表示される
**原因**: HTMLテンプレートがf-stringになっていない
**解決**: `html += """` を `html += f"""` に変更

### 4. NHK東北ニュースのリンクが404になる
**原因**: 相対パスの変換ロジックが未実装
**解決**: `get_full_url()`で正規表現を使って記事IDを抽出

### 5. 訂正記事が表示されない
**確認ポイント**:
- `description`に※や「失礼しました」が含まれているか
- `has_correction`フラグが1になっているか
- 検出条件: `(※ + 当初 + 掲載)` OR `(※ + 失礼しました)`

---

## 運用上の注意事項

### 1. 著作権対応
- 記事本文は最大150-200文字の要約のみ表示
- 「→ 元記事を読む（NHK）」リンクを必ず表示
- 全文転載は絶対に行わない

### 2. データベースメンテナンス
- `data/articles.db`は自動的に更新される
- バックアップは定期的に取得推奨
- 肥大化したら古いデータを削除検討

### 3. RSS更新頻度
- NHKのRSSは不定期更新
- 1日1-2回の実行を推奨
- cronやGitHub Actionsで自動化可能

### 4. エラーハンドリング
- `main_hybrid.py`はエラーが発生してもログに記録して継続
- 致命的エラーの場合のみ停止
- ログファイルを定期的に確認

---

## 今後の改善予定

### 1. Netlify Analytics有効化（運用安定後）
**費用**: $9/月
**取得データ**: IPアドレス、リファラー、国、都市、デバイス等

**有効化手順**:
```bash
netlify open
# Site settings → Analytics → Enable Analytics
```

### 2. 自動実行の設定
**選択肢**:
- cron（macOS launchd）
- GitHub Actions
- Netlify Scheduled Functions

### 3. 通知機能
- 訂正記事検出時にメール/Slack通知
- 重要度の高い変更を優先通知

### 4. 検索機能
- 記事タイトル・本文の全文検索
- キーワードでフィルタリング

---

## 依存パッケージ

```bash
# 必須パッケージ
pip install feedparser beautifulsoup4 requests Pillow

# バージョン確認済み
feedparser==6.0.12
beautifulsoup4==4.14.2
requests>=2.31.0
Pillow>=10.0.0
```

---

## よくある質問

**Q: ローカルでプレビューするには？**
```bash
cd reports
python3 -m http.server 8000
# http://localhost:8000 で確認
```

**Q: 特定のソースだけ監視したい場合は？**
`main_hybrid.py`のRSS_FEEDS辞書を編集してコメントアウト。

**Q: OGP画像を再生成するには？**
```bash
/usr/bin/python3 generate_assets.py
```

**Q: データベースをリセットしたい場合は？**
```bash
rm data/articles.db
# 次回実行時に自動作成される
```

---

## 参考リンク

- **本番サイト**: https://nhk-news-tracker.netlify.app
- **Netlifyダッシュボード**: `netlify open`で開く
- **note.com RSS**: https://note.com/darkside_of_nhk/rss

---

## 開発履歴（主要な修正）

### 2025-10-12
1. **NHK東北ニュースのURL生成修正** - 正規表現で記事ID抽出
2. **NHK ONE検索をフィルタに追加** - SOURCE_BASE_URLSに追加
3. **訂正記事の表示改善** - 完全な文を抽出、ハイライト表示
4. **訂正テキストの抽出ロジック修正** - descriptionフィールドから抽出
5. **不適切なおことわり検出を修正** - 厳密な条件チェック追加
6. **OGP画像とファビコン追加** - 1.91:1比率で最適化
7. **サイト目的セクション追加** - 問題意識を明示
8. **note.com RSS統合** - 最新3記事をOGPカード表示
9. **note記事OGP比率を16:9に修正** - aspect-ratioで比率保持

---

## 最終チェックリスト（デプロイ前）

- [ ] `main_hybrid.py`実行でデータベース更新
- [ ] `generate_portal.py`実行でindex.html生成
- [ ] `generate_history.py`実行でhistory.html生成
- [ ] `generate_archive.py`実行でarchive.html生成
- [ ] ローカルでHTMLプレビュー確認
- [ ] 訂正記事が正しくハイライト表示されているか
- [ ] note記事のOGP画像が16:9で表示されているか
- [ ] リンク切れがないか確認
- [ ] `netlify deploy --prod --dir=reports`でデプロイ
- [ ] 本番サイトで最終確認

---

**作成日**: 2025-10-12
**最終更新**: 2025-10-12
**ステータス**: 運用テスト中
