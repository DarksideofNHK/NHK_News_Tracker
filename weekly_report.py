#!/usr/bin/env python3
"""
週次レポート生成 - NHK誤情報モニタリング

特に以下を重点的に追跡:
- 訂正が数時間で削除されたケース
- 固有名詞、数字、事実関係の誤り
- 深刻な変更
"""
import sqlite3
from pathlib import Path
from typing import List, Dict
from datetime import datetime, timedelta
from jinja2 import Template
import logging

logger = logging.getLogger(__name__)

class WeeklyReportGenerator:
    """週次レポート生成"""

    def __init__(self, db_path: str = 'data/articles.db'):
        self.db_path = db_path

    def get_corrections(self, days: int = 7) -> List[Dict]:
        """訂正記事を取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        # 訂正ありの記事
        cursor.execute('''
            SELECT DISTINCT a.source, a.link, a.title, a.description,
                   a.correction_keywords, a.first_seen, a.last_seen
            FROM articles a
            WHERE a.has_correction = 1 AND a.first_seen >= ?
            ORDER BY a.first_seen DESC
        ''', (cutoff,))

        corrections = []
        for row in cursor.fetchall():
            corrections.append({
                'source': row[0],
                'link': row[1],
                'title': row[2],
                'description': row[3],
                'correction_keywords': row[4],
                'first_seen': row[5],
                'last_seen': row[6]
            })

        conn.close()
        return corrections

    def get_correction_removals(self, days: int = 7) -> List[Dict]:
        """訂正削除を取得（最も重要！）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        cursor.execute('''
            SELECT c.source, c.link, c.old_value, c.new_value,
                   c.detected_at, c.correction_keywords, c.change_summary
            FROM changes c
            WHERE c.change_type = 'correction_removed' AND c.detected_at >= ?
            ORDER BY c.detected_at DESC
        ''', (cutoff,))

        removals = []
        for row in cursor.fetchall():
            # 記事タイトルも取得
            cursor2 = conn.cursor()
            cursor2.execute('SELECT title FROM articles WHERE source = ? AND link = ?',
                          (row[0], row[1]))
            title_row = cursor2.fetchone()
            title = title_row[0] if title_row else "（タイトル不明）"

            removals.append({
                'source': row[0],
                'link': row[1],
                'title': title,
                'old_value': row[2],
                'new_value': row[3],
                'detected_at': row[4],
                'correction_keywords': row[5],
                'change_summary': row[6]
            })

        conn.close()
        return removals

    def get_serious_changes(self, days: int = 7) -> List[Dict]:
        """深刻な変更を取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        # 説明文変更で訂正キーワードを含むもの
        cursor.execute('''
            SELECT c.source, c.link, c.old_value, c.new_value,
                   c.detected_at, c.change_summary, c.has_correction, c.correction_keywords
            FROM changes c
            WHERE c.change_type = 'description_changed'
                  AND c.detected_at >= ?
                  AND (c.has_correction = 1 OR c.change_summary IS NOT NULL)
            ORDER BY c.has_correction DESC, c.detected_at DESC
        ''', (cutoff,))

        changes = []
        for row in cursor.fetchall():
            # 記事タイトルも取得
            cursor2 = conn.cursor()
            cursor2.execute('SELECT title FROM articles WHERE source = ? AND link = ?',
                          (row[0], row[1]))
            title_row = cursor2.fetchone()
            title = title_row[0] if title_row else "（タイトル不明）"

            changes.append({
                'source': row[0],
                'link': row[1],
                'title': title,
                'old_value': row[2],
                'new_value': row[3],
                'detected_at': row[4],
                'change_summary': row[5],
                'has_correction': row[6],
                'correction_keywords': row[7]
            })

        conn.close()
        return changes

    def generate_report(self, days: int = 7, output_path: str = None) -> str:
        """
        週次レポート生成

        Args:
            days: 対象期間（日数）
            output_path: 出力先パス
        """
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d')
            output_path = f"reports/weekly_report_{timestamp}.html"

        # データ取得
        corrections = self.get_corrections(days)
        removals = self.get_correction_removals(days)
        serious_changes = self.get_serious_changes(days)

        # レポート生成
        template = Template(WEEKLY_REPORT_TEMPLATE)
        html = template.render(
            report_date=datetime.now().strftime('%Y年%m月%d日'),
            days=days,
            corrections=corrections,
            removals=removals,
            serious_changes=serious_changes,
            correction_count=len(corrections),
            removal_count=len(removals),
            serious_count=len(serious_changes)
        )

        # ファイル出力
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(html, encoding='utf-8')

        logger.info(f"週次レポート生成完了: {output_path}")
        return output_path


WEEKLY_REPORT_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NHK誤情報モニタリング週次レポート - {{ report_date }}</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        h1 {
            color: #c62828;
            border-bottom: 4px solid #c62828;
            padding-bottom: 10px;
        }
        h2 {
            color: #d32f2f;
            margin-top: 30px;
            padding-left: 10px;
            border-left: 5px solid #d32f2f;
        }
        .alert-box {
            background-color: #ffebee;
            border-left: 5px solid #c62828;
            padding: 20px;
            margin: 20px 0;
            border-radius: 4px;
        }
        .summary {
            background-color: #fff3cd;
            border-left: 4px solid #ff9800;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-top: 4px solid #ff4444;
        }
        .stat-card h3 {
            margin: 0 0 10px 0;
            color: #666;
            font-size: 14px;
        }
        .stat-card .number {
            font-size: 36px;
            font-weight: bold;
            color: #c62828;
        }
        .item {
            background: white;
            margin: 15px 0;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .item.critical {
            border-left: 5px solid #c62828;
            background-color: #ffebee;
        }
        .item.warning {
            border-left: 5px solid #ff9800;
            background-color: #fff3e0;
        }
        .item.info {
            border-left: 5px solid #2196F3;
        }
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            margin: 5px 5px 5px 0;
        }
        .badge.critical {
            background-color: #c62828;
            color: white;
        }
        .badge.warning {
            background-color: #ff9800;
            color: white;
        }
        .badge.correction {
            background-color: #ff4444;
            color: white;
        }
        .source-badge {
            background-color: #e8eaed;
            color: #333;
        }
        .content {
            margin: 15px 0;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 4px;
        }
        .old-content {
            color: #d32f2f;
            margin-bottom: 10px;
            padding: 10px;
            background-color: #ffebee;
            border-radius: 4px;
        }
        .new-content {
            color: #2e7d32;
            padding: 10px;
            background-color: #e8f5e9;
            border-radius: 4px;
        }
        .timestamp {
            color: #666;
            font-size: 14px;
            margin-top: 10px;
        }
        .link {
            color: #1976d2;
            text-decoration: none;
            word-break: break-all;
        }
        .link:hover {
            text-decoration: underline;
        }
        footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #ddd;
            text-align: center;
            color: #666;
        }
    </style>
</head>
<body>
    <h1>🚨 NHK誤情報モニタリング週次レポート</h1>

    <div class="alert-box">
        <h3>⚠️ 重要な警告</h3>
        <p>このレポートは、NHKニュースにおける記事の修正・訂正・削除を自動追跡したものです。</p>
        <p><strong>特に注視すべき点:</strong></p>
        <ul>
            <li>訂正が数時間で削除されているケース</li>
            <li>固有名詞、数字、事実関係の誤り</li>
            <li>深刻な内容変更が行われたケース</li>
        </ul>
    </div>

    <div class="summary">
        <h2>📊 サマリー</h2>
        <p><strong>レポート作成日:</strong> {{ report_date }}</p>
        <p><strong>対象期間:</strong> 過去{{ days }}日間</p>
    </div>

    <div class="stats">
        <div class="stat-card">
            <h3>🔴 訂正記事</h3>
            <div class="number">{{ correction_count }}</div>
        </div>
        <div class="stat-card">
            <h3>⚠️ 訂正削除</h3>
            <div class="number">{{ removal_count }}</div>
        </div>
        <div class="stat-card">
            <h3>📝 深刻な変更</h3>
            <div class="number">{{ serious_count }}</div>
        </div>
    </div>

    <h2>🚨 最重要: 訂正が削除されたケース ({{ removal_count }}件)</h2>
    <p style="color: #c62828; font-weight: bold;">※ これらは訂正後、数時間で削除された可能性があります</p>

    {% if removals %}
        {% for item in removals %}
        <div class="item critical">
            <div>
                <span class="badge critical">訂正削除</span>
                <span class="badge source-badge">{{ item.source }}</span>
                {% if item.correction_keywords %}
                <span class="badge correction">キーワード: {{ item.correction_keywords }}</span>
                {% endif %}
            </div>

            <h3>{{ item.title }}</h3>

            {% if item.change_summary %}
            <div class="content" style="background-color: #e3f2fd; border-left: 3px solid #1976d2;">
                <strong>🤖 AI分析:</strong> {{ item.change_summary }}
            </div>
            {% endif %}

            <div class="content">
                <div class="old-content">
                    <strong>削除前（訂正あり）:</strong><br>
                    {{ item.old_value[:300] }}{% if item.old_value|length > 300 %}...{% endif %}
                </div>
                <div class="new-content">
                    <strong>削除後（訂正なし）:</strong><br>
                    {{ item.new_value[:300] }}{% if item.new_value|length > 300 %}...{% endif %}
                </div>
            </div>

            <div>
                <a href="{{ item.link }}" class="link" target="_blank">{{ item.link }}</a>
            </div>
            <div class="timestamp">検出時刻: {{ item.detected_at }}</div>
        </div>
        {% endfor %}
    {% else %}
        <div class="item info">
            <p>訂正削除は検出されませんでした。</p>
        </div>
    {% endif %}

    <h2>🔴 訂正記事一覧 ({{ correction_count }}件)</h2>

    {% if corrections %}
        {% for item in corrections %}
        <div class="item warning">
            <div>
                <span class="badge warning">訂正あり</span>
                <span class="badge source-badge">{{ item.source }}</span>
                {% if item.correction_keywords %}
                <span class="badge correction">{{ item.correction_keywords }}</span>
                {% endif %}
            </div>

            <h3>{{ item.title }}</h3>

            <div class="content">
                {{ item.description[:400] }}{% if item.description|length > 400 %}...{% endif %}
            </div>

            <div>
                <a href="{{ item.link }}" class="link" target="_blank">{{ item.link }}</a>
            </div>
            <div class="timestamp">
                初回検出: {{ item.first_seen }}<br>
                最終確認: {{ item.last_seen }}
            </div>
        </div>
        {% endfor %}
    {% else %}
        <div class="item info">
            <p>訂正記事は検出されませんでした。</p>
        </div>
    {% endif %}

    <h2>📝 深刻な変更一覧 ({{ serious_count }}件)</h2>

    {% if serious_changes %}
        {% for item in serious_changes %}
        <div class="item {% if item.has_correction %}critical{% else %}warning{% endif %}">
            <div>
                <span class="badge {% if item.has_correction %}critical{% else %}warning{% endif %}">
                    {% if item.has_correction %}深刻な変更{% else %}変更あり{% endif %}
                </span>
                <span class="badge source-badge">{{ item.source }}</span>
                {% if item.correction_keywords %}
                <span class="badge correction">{{ item.correction_keywords }}</span>
                {% endif %}
            </div>

            <h3>{{ item.title }}</h3>

            {% if item.change_summary %}
            <div class="content" style="background-color: #e3f2fd; border-left: 3px solid #1976d2;">
                <strong>🤖 AI分析:</strong> {{ item.change_summary }}
            </div>
            {% endif %}

            <div class="content">
                <div class="old-content">
                    <strong>変更前:</strong><br>
                    {{ item.old_value[:300] }}{% if item.old_value|length > 300 %}...{% endif %}
                </div>
                <div class="new-content">
                    <strong>変更後:</strong><br>
                    {{ item.new_value[:300] }}{% if item.new_value|length > 300 %}...{% endif %}
                </div>
            </div>

            <div>
                <a href="{{ item.link }}" class="link" target="_blank">{{ item.link }}</a>
            </div>
            <div class="timestamp">検出時刻: {{ item.detected_at }}</div>
        </div>
        {% endfor %}
    {% else %}
        <div class="item info">
            <p>深刻な変更は検出されませんでした。</p>
        </div>
    {% endif %}

    <footer>
        <p><strong>NHK誤情報モニタリングシステム</strong></p>
        <p>Generated at {{ report_date }}</p>
        <p style="color: #c62828; font-weight: bold;">
            ⚠️ このレポートの目的は、報道機関の正確性と透明性を監視することです。
        </p>
    </footer>
</body>
</html>
'''
