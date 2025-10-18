#!/usr/bin/env python3
"""
変更差分の可視化（HTML出力）
"""
from jinja2 import Template
from pathlib import Path
from typing import List, Dict
from datetime import datetime
import logging
import re

logger = logging.getLogger(__name__)


def highlight_correction_notice(text: str) -> str:
    """
    ※から始まる文（訂正のおことわり）をハイライト

    Args:
        text: 元のテキスト

    Returns:
        ハイライトされたHTML
    """
    if not text:
        return text

    # ※から始まる文を検出
    # パターン1: ※から始まり「失礼しました」を含む場合はその後の。まで
    # パターン2: それ以外は最初の。または改行まで
    pattern = r'(※[^※]*?失礼しました[^\n]*?。|※[^。\n]+[。\n]?)'

    def replace_func(match):
        notice = match.group(1)
        return f'<span class="correction-notice">{notice}</span>'

    return re.sub(pattern, replace_func, text)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NHKニュース変更履歴 - {{ report_date }}</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        h1 {
            color: #1a73e8;
            border-bottom: 3px solid #1a73e8;
            padding-bottom: 10px;
        }
        .summary {
            background-color: #e8f4f8;
            border-left: 4px solid #1a73e8;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }
        .summary h2 {
            margin-top: 0;
            color: #1a73e8;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .stat-card h3 {
            margin: 0 0 10px 0;
            color: #666;
            font-size: 14px;
        }
        .stat-card .number {
            font-size: 32px;
            font-weight: bold;
            color: #1a73e8;
        }
        .change-item {
            background: white;
            margin: 15px 0;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .change-item.new {
            border-left: 4px solid #34a853;
        }
        .change-item.title_changed {
            border-left: 4px solid #fbbc04;
        }
        .change-item.description_changed {
            border-left: 4px solid #ea4335;
        }
        .change-item.description_added {
            border-left: 4px solid #4285f4;
        }
        .change-type {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .change-type.new {
            background-color: #d4edda;
            color: #155724;
        }
        .change-type.title_changed {
            background-color: #fff3cd;
            color: #856404;
        }
        .change-type.description_changed {
            background-color: #f8d7da;
            color: #721c24;
        }
        .change-type.description_added {
            background-color: #d2e3fc;
            color: #174ea6;
        }
        .change-type.correction_removed {
            background-color: #ff6b6b;
            color: white;
        }
        .source-badge {
            display: inline-block;
            padding: 4px 8px;
            background-color: #e8eaed;
            border-radius: 4px;
            font-size: 12px;
            margin-left: 10px;
        }
        .correction-badge {
            display: inline-block;
            padding: 4px 8px;
            background-color: #ff4444;
            color: white;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
            margin-left: 10px;
        }
        .change-item.has-correction {
            border-left: 4px solid #ff4444;
            background-color: #fff5f5;
        }
        .timestamp {
            color: #666;
            font-size: 14px;
            margin-top: 10px;
        }
        .diff-container {
            margin: 15px 0;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 4px;
            white-space: pre-wrap;
            word-wrap: break-word;
            line-height: 1.8;
        }
        .diff-old {
            color: #d32f2f;
            text-decoration: line-through;
            margin-bottom: 12px;
        }
        .diff-new {
            color: #388e3c;
            font-weight: bold;
        }
        .link {
            color: #1a73e8;
            text-decoration: none;
            word-break: break-all;
        }
        .link:hover {
            text-decoration: underline;
        }
        footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #666;
            font-size: 14px;
        }
        .nav-links {
            background-color: white;
            padding: 15px;
            margin: 20px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            display: flex;
            gap: 15px;
            justify-content: center;
            flex-wrap: wrap;
        }
        .nav-link {
            padding: 10px 20px;
            background-color: #1a73e8;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            font-weight: bold;
            transition: background-color 0.2s;
        }
        .nav-link:hover {
            background-color: #1557b0;
        }
        .nav-link.secondary {
            background-color: #34a853;
        }
        .nav-link.secondary:hover {
            background-color: #2d8e47;
        }
        .correction-notice {
            background: #ffeb3b;
            border-left: 4px solid #d32f2f;
            padding: 8px 12px;
            margin: 8px 0;
            display: inline-block;
            border-radius: 4px;
            font-weight: bold;
            color: #d32f2f;
        }
    </style>
</head>
<body>
    <h1>📰 NHKニュース変更履歴</h1>

    <div class="summary">
        <h2>📊 サマリー</h2>
        <p><strong>レポート日時:</strong> {{ report_date }}</p>
        <p><strong>対象期間:</strong> 過去{{ hours }}時間</p>
    </div>

    <div class="nav-links">
        <a href="history.html" class="nav-link">📜 全変更履歴を見る</a>
        <a href="archive.html" class="nav-link secondary">🗂️ 全記事アーカイブを見る</a>
    </div>

    <div class="stats">
        <div class="stat-card">
            <h3>総変更数</h3>
            <div class="number">{{ total_changes }}</div>
        </div>
        <div class="stat-card">
            <h3>新規記事</h3>
            <div class="number">{{ new_count }}</div>
        </div>
        <div class="stat-card">
            <h3>タイトル変更</h3>
            <div class="number">{{ title_changed_count }}</div>
        </div>
        <div class="stat-card">
            <h3>説明文変更</h3>
            <div class="number">{{ desc_changed_count }}</div>
        </div>
        <div class="stat-card" style="background-color: #fff5f5;">
            <h3>🔴 訂正記事</h3>
            <div class="number" style="color: #ff4444;">{{ correction_count }}</div>
        </div>
        <div class="stat-card" style="background-color: #fff0f0;">
            <h3>⚠️ 訂正削除</h3>
            <div class="number" style="color: #ff6b6b;">{{ correction_removed_count }}</div>
        </div>
    </div>

    <h2>📝 変更詳細</h2>

    {% if changes %}
        {% for change in changes %}
        <div class="change-item {{ change.change_type }} {% if change.has_correction %}has-correction{% endif %}">
            <div>
                <span class="change-type {{ change.change_type }}">
                    {% if change.change_type == 'new' %}
                        🆕 新規
                    {% elif change.change_type == 'title_changed' %}
                        ✏️ タイトル変更
                    {% elif change.change_type == 'description_added' or (change.change_type in ['description_changed', 'description_added'] and not change.old_value) %}
                        ➕ 説明文追記
                    {% elif change.change_type == 'description_changed' %}
                        📝 説明文変更
                    {% elif change.change_type == 'correction_removed' %}
                        ⚠️ 訂正削除
                    {% endif %}
                </span>
                <span class="source-badge">{{ change.source }}</span>
                {% if change.has_correction %}
                <span class="correction-badge">🔴 おことわり</span>
                {% endif %}
            </div>

            {% if change.change_type == 'new' %}
                <h3>{{ change.new_value }}</h3>
            {% elif change.change_type == 'description_added' or (change.change_type in ['description_changed', 'description_added'] and not change.old_value) %}
                {% if change.change_summary %}
                <div class="diff-container" style="background-color: #e3f2fd; border-left: 3px solid #1976d2;">
                    <strong>🤖 AI分析:</strong>
                    <div style="margin-top: 8px;">{{ change.change_summary }}</div>
                </div>
                {% endif %}
                <div class="diff-container">
                    <div class="diff-new">追記内容:
{{ highlight_correction_notice(change.new_value)|safe }}</div>
                </div>
            {% else %}
                {% if change.change_summary %}
                <div class="diff-container" style="background-color: #e3f2fd; border-left: 3px solid #1976d2;">
                    <strong>🤖 AI分析:</strong>
                    <div style="margin-top: 8px;">{{ change.change_summary }}</div>
                </div>
                {% endif %}
                <div class="diff-container">
                    <div class="diff-old">旧:
{{ change.old_value }}</div>
                    <div class="diff-new">新:
{{ highlight_correction_notice(change.new_value)|safe }}</div>
                </div>
            {% endif %}

            <div>
                <a href="{{ change.link }}" class="link" target="_blank">{{ change.link }}</a>
            </div>

            <div class="timestamp">🕒 {{ change.detected_at }}</div>
        </div>
        {% endfor %}
    {% else %}
        <div class="change-item">
            <p>過去{{ hours }}時間に変更はありませんでした。</p>
        </div>
    {% endif %}

    <footer>
        <p>NHKニュース差分追跡システム - Python PoC</p>
        <p>Generated at {{ report_date }}</p>
    </footer>
</body>
</html>
'''

class ChangeVisualizer:
    """変更差分のHTML可視化"""

    def __init__(self):
        self.template = Template(HTML_TEMPLATE)
        # カスタムフィルターを追加
        self.template.globals['highlight_correction_notice'] = highlight_correction_notice

    def generate_html_report(self, changes: List[Dict], output_path: str, hours: int = 24):
        """
        HTML変更レポート生成

        Args:
            changes: 変更リスト
            output_path: 出力パス
            hours: 対象期間（時間）
        """
        # 統計計算
        new_count = sum(1 for c in changes if c['change_type'] == 'new')
        title_changed_count = sum(1 for c in changes if c['change_type'] == 'title_changed')
        desc_changed_count = sum(1 for c in changes if c['change_type'] in ('description_changed', 'description_added'))
        correction_count = sum(1 for c in changes if c.get('has_correction'))
        correction_removed_count = sum(1 for c in changes if c['change_type'] == 'correction_removed')

        # HTML生成
        html = self.template.render(
            report_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            hours=hours,
            total_changes=len(changes),
            new_count=new_count,
            title_changed_count=title_changed_count,
            desc_changed_count=desc_changed_count,
            correction_count=correction_count,
            correction_removed_count=correction_removed_count,
            changes=changes,
        )

        # 保存
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        logger.info(f"HTMLレポート生成完了: {output_path}")

        return output_path
