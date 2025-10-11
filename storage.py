#!/usr/bin/env python3
"""
データ蓄積機能（JSON/SQLite）
"""
import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ArticleStorage:
    """記事データベース"""

    def __init__(self, db_path: str = 'data/articles.db', gemini_analyzer=None):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.gemini_analyzer = gemini_analyzer
        self._init_db()

    def _init_db(self):
        """データベース初期化"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # articlesテーブル作成
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                link TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                pub_date TEXT,
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL,
                has_correction INTEGER DEFAULT 0,
                correction_keywords TEXT,
                UNIQUE(source, link)
            )
        ''')

        # changesテーブル作成（変更履歴）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                link TEXT NOT NULL,
                change_type TEXT NOT NULL,
                old_value TEXT,
                new_value TEXT,
                detected_at TEXT NOT NULL,
                change_summary TEXT,
                has_correction INTEGER DEFAULT 0,
                correction_keywords TEXT
            )
        ''')

        # インデックス作成
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_link ON articles(link)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_changes_source ON changes(source)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_changes_detected_at ON changes(detected_at)')

        # マイグレーション: 既存DBに訂正カラムを追加（articles）
        try:
            cursor.execute("ALTER TABLE articles ADD COLUMN has_correction INTEGER DEFAULT 0")
            logger.info("マイグレーション: articlesにhas_correctionカラムを追加")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE articles ADD COLUMN correction_keywords TEXT")
            logger.info("マイグレーション: articlesにcorrection_keywordsカラムを追加")
        except sqlite3.OperationalError:
            pass

        # マイグレーション: 既存DBにカラムを追加（changes）
        try:
            cursor.execute("ALTER TABLE changes ADD COLUMN change_summary TEXT")
            logger.info("マイグレーション: changesにchange_summaryカラムを追加")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE changes ADD COLUMN has_correction INTEGER DEFAULT 0")
            logger.info("マイグレーション: changesにhas_correctionカラムを追加")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE changes ADD COLUMN correction_keywords TEXT")
            logger.info("マイグレーション: changesにcorrection_keywordsカラムを追加")
        except sqlite3.OperationalError:
            pass

        conn.commit()
        conn.close()

        logger.info(f"データベース初期化完了: {self.db_path}")

    def detect_correction(self, text: str) -> tuple[bool, list[str]]:
        """
        訂正キーワードを検出

        Args:
            text: 記事の説明文

        Returns:
            (has_correction, found_keywords): 訂正が含まれるか、検出されたキーワードリスト
        """
        if not text:
            return False, []

        # 訂正キーワード
        keywords = ['当初', '掲載', '失礼しました', '※']  # 全角※

        found = []
        for keyword in keywords:
            if keyword in text:
                found.append(keyword)

        return len(found) > 0, found

    def save_articles(self, source: str, articles: List[Dict[str, str]]) -> Dict[str, int]:
        """
        記事を保存し、変更を検出

        Returns:
            {'new': 新規件数, 'updated': 更新件数, 'unchanged': 変更なし件数}
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        stats = {'new': 0, 'updated': 0, 'unchanged': 0}

        for article in articles:
            # 訂正検出
            has_correction, correction_keywords = self.detect_correction(article.get('description', ''))
            keywords_str = ','.join(correction_keywords) if correction_keywords else None

            # 既存記事チェック
            cursor.execute('''
                SELECT title, description, has_correction FROM articles
                WHERE source = ? AND link = ?
            ''', (source, article['link']))

            existing = cursor.fetchone()

            if existing is None:
                # 新規記事
                cursor.execute('''
                    INSERT INTO articles (source, link, title, description, pub_date, first_seen, last_seen, has_correction, correction_keywords)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (source, article['link'], article['title'], article['description'],
                      article['pubDate'], now, now, 1 if has_correction else 0, keywords_str))

                # 変更履歴記録
                cursor.execute('''
                    INSERT INTO changes (source, link, change_type, new_value, detected_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (source, article['link'], 'new', article['title'], now))

                stats['new'] += 1
                if has_correction:
                    logger.info(f"🔴 新規記事（訂正あり）: {article['title']} [キーワード: {keywords_str}]")
                else:
                    logger.info(f"新規記事: {article['title']}")

            else:
                old_title, old_desc, old_has_correction = existing

                # タイトル変更チェック
                if old_title != article['title']:
                    # AI分析
                    change_summary = None
                    if self.gemini_analyzer:
                        change_summary = self.gemini_analyzer.analyze_change(
                            old_title, article['title'], article['title']
                        )

                    cursor.execute('''
                        UPDATE articles SET title = ?, last_seen = ?, has_correction = ?, correction_keywords = ?
                        WHERE source = ? AND link = ?
                    ''', (article['title'], now, 1 if has_correction else 0, keywords_str, source, article['link']))

                    cursor.execute('''
                        INSERT INTO changes (source, link, change_type, old_value, new_value, detected_at, change_summary, has_correction, correction_keywords)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (source, article['link'], 'title_changed', old_title, article['title'], now, change_summary, 1 if has_correction else 0, keywords_str))

                    stats['updated'] += 1
                    logger.info(f"タイトル変更: {old_title} → {article['title']}")

                # 説明文変更チェック
                elif old_desc != article['description']:
                    # AI分析
                    change_summary = None
                    if self.gemini_analyzer:
                        change_summary = self.gemini_analyzer.analyze_change(
                            old_desc or "", article['description'] or "", article['title']
                        )

                    cursor.execute('''
                        UPDATE articles SET description = ?, last_seen = ?, has_correction = ?, correction_keywords = ?
                        WHERE source = ? AND link = ?
                    ''', (article['description'], now, 1 if has_correction else 0, keywords_str, source, article['link']))

                    cursor.execute('''
                        INSERT INTO changes (source, link, change_type, old_value, new_value, detected_at, change_summary, has_correction, correction_keywords)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (source, article['link'], 'description_changed', old_desc, article['description'], now, change_summary, 1 if has_correction else 0, keywords_str))

                    # 訂正の追加・削除を検出
                    if not old_has_correction and has_correction:
                        logger.info(f"🔴 訂正追加: {article['title']} [キーワード: {keywords_str}]")
                    elif old_has_correction and not has_correction:
                        logger.info(f"⚠️  訂正削除: {article['title']} (以前のキーワード: {keywords_str})")
                        # 訂正削除を記録
                        cursor.execute('''
                            INSERT INTO changes (source, link, change_type, old_value, new_value, detected_at, change_summary, has_correction, correction_keywords)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (source, article['link'], 'correction_removed', old_desc, article['description'], now, "訂正が削除されました", 0, keywords_str))

                    stats['updated'] += 1
                    logger.info(f"説明文変更: {article['title']}")

                else:
                    # 変更なし - last_seenのみ更新
                    cursor.execute('''
                        UPDATE articles SET last_seen = ?
                        WHERE source = ? AND link = ?
                    ''', (now, source, article['link']))

                    stats['unchanged'] += 1

        conn.commit()
        conn.close()

        logger.info(f"保存完了: 新規{stats['new']}件, 更新{stats['updated']}件, 変更なし{stats['unchanged']}件")
        return stats

    def get_recent_changes(self, hours: int = 24, source: Optional[str] = None) -> List[Dict]:
        """最近の変更を取得"""
        from datetime import timedelta

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()

        if source:
            cursor.execute('''
                SELECT source, link, change_type, old_value, new_value, detected_at
                FROM changes
                WHERE detected_at >= ? AND source = ?
                ORDER BY detected_at DESC
            ''', (cutoff, source))
        else:
            cursor.execute('''
                SELECT source, link, change_type, old_value, new_value, detected_at
                FROM changes
                WHERE detected_at >= ?
                ORDER BY detected_at DESC
            ''', (cutoff,))

        changes = []
        for row in cursor.fetchall():
            changes.append({
                'source': row[0],
                'link': row[1],
                'change_type': row[2],
                'old_value': row[3],
                'new_value': row[4],
                'detected_at': row[5],
            })

        conn.close()
        return changes

    def export_to_json(self, output_path: str):
        """全データをJSONエクスポート"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 記事取得
        cursor.execute('SELECT * FROM articles ORDER BY first_seen DESC')
        articles = [dict(zip([col[0] for col in cursor.description], row))
                   for row in cursor.fetchall()]

        # 変更履歴取得
        cursor.execute('SELECT * FROM changes ORDER BY detected_at DESC LIMIT 1000')
        changes = [dict(zip([col[0] for col in cursor.description], row))
                  for row in cursor.fetchall()]

        conn.close()

        data = {
            'articles': articles,
            'changes': changes,
            'exported_at': datetime.now().isoformat(),
        }

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"JSONエクスポート完了: {output_path}")
