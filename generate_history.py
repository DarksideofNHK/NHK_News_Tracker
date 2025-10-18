#!/usr/bin/env python3
"""
NHK RSS変更履歴ビューアー
全変更履歴をdiffスタイルで表示
"""

import sqlite3
import difflib
from datetime import datetime
from pathlib import Path
import re

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent


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


# ソース名からベースURLへのマッピング
SOURCE_BASE_URLS = {
    'NHK首都圏ニュース': 'https://www.nhk.or.jp/shutoken-news/',
    'NHK福岡ニュース': 'https://www.nhk.or.jp/fukuoka-news/',
    'NHK札幌ニュース': 'https://www.nhk.or.jp/sapporo-news/',
    'NHK東海ニュース': 'https://www.nhk.or.jp/tokai-news/',
    'NHK広島ニュース': 'https://www.nhk.or.jp/hiroshima-news/',
    'NHK関西ニュース': 'https://www.nhk.or.jp/kansai-news/',
    'NHK東北ニュース': 'https://news.web.nhk/tohoku-news/',
    'NHK ONE検索': '',  # 完全URLで保存されているため、ベースURLは不要
}

def get_full_url(source, relative_path):
    """ソース名と相対パスから完全URLを生成"""
    # 既に完全URLの場合はそのまま返す
    if relative_path.startswith('http://') or relative_path.startswith('https://'):
        return relative_path

    # NHK東北ニュースの特別処理（Selenium経由で取得した記事）
    if source == 'NHK東北ニュース':
        # 20251009/6000033450.html から 6000033450 を抽出
        match = re.search(r'(\d+)\.html$', relative_path)
        if match:
            article_id = match.group(1)
            return f'https://news.web.nhk/newsweb/na/nb-{article_id}'

    # 通常のベースURL結合
    base_url = SOURCE_BASE_URLS.get(source, '')
    if base_url:
        return base_url + relative_path
    return relative_path  # フォールバック

def get_all_changes(db_path, limit=None):
    """全変更履歴を取得（新しい順）"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = """
    WITH change_timeline AS (
        SELECT
            c.*,
            a.title as current_title,
            a.description as current_description,
            a.first_seen,
            LAG(c.detected_at) OVER (PARTITION BY c.link ORDER BY c.detected_at) as previous_check_time
        FROM changes c
        LEFT JOIN articles a ON c.link = a.link
        WHERE c.change_type IN ('title_changed', 'description_changed', 'description_added', 'correction_removed')
    )
    SELECT
        *,
        COALESCE(previous_check_time, first_seen) as before_change_time,
        detected_at as after_change_time
    FROM change_timeline
    ORDER BY detected_at DESC
    """

    if limit:
        query += f" LIMIT {limit}"

    cursor.execute(query)
    changes = cursor.fetchall()
    conn.close()

    return changes

def generate_diff_html(old_text, new_text):
    """テキストの差分をHTML形式で生成"""
    if not old_text:
        old_text = ""
    if not new_text:
        new_text = ""

    # 行ごとに分割
    old_lines = old_text.splitlines()
    new_lines = new_text.splitlines()

    # diffを生成
    differ = difflib.Differ()
    diff = list(differ.compare(old_lines, new_lines))

    html_parts = []
    html_parts.append('<div class="diff-container">')

    for line in diff:
        if line.startswith('- '):
            # 削除された行（赤）
            html_parts.append(f'<div class="diff-line deleted">{line[2:]}</div>')
        elif line.startswith('+ '):
            # 追加された行（緑）
            html_parts.append(f'<div class="diff-line added">{line[2:]}</div>')
        elif line.startswith('  '):
            # 変更なし（グレー）
            html_parts.append(f'<div class="diff-line unchanged">{line[2:]}</div>')

    html_parts.append('</div>')
    return '\n'.join(html_parts)

def extract_correction_summary(text, max_length=200):
    """※や失礼しましたを含む文をすべて抽出（著作権対応）"""
    if not text:
        return ''

    # 文を分割
    sentences = text.replace('。', '。\n').split('\n')

    # ※を含む文と「失礼しました」を含む文を抽出
    correction_sentences = []
    for sentence in sentences:
        if '※' in sentence or '失礼しました' in sentence:
            correction_sentences.append(sentence.strip())

    if correction_sentences:
        # 訂正文を結合
        result = '\n'.join(correction_sentences)

        # 長すぎる場合は各文を短縮
        if len(result) > max_length:
            shortened = []
            for sent in correction_sentences:
                if '失礼しました' in sent:
                    # 訂正のおことわり文は全文表示
                    shortened.append(sent)
                elif '※' in sent:
                    # ※を含む文は前後を含めて表示
                    idx = sent.find('※')
                    start = max(0, idx - 30)
                    end = min(len(sent), idx + 70)
                    excerpt = sent[start:end]
                    if start > 0:
                        excerpt = '...' + excerpt
                    if end < len(sent):
                        excerpt = excerpt + '...'
                    shortened.append(excerpt)
            result = '\n'.join(shortened)

        return result
    else:
        # 訂正マーカーがない場合は先頭から
        if len(text) > max_length:
            return text[:max_length] + '...'
        return text

def extract_diff_context(old_html, new_html, context_chars=200):
    """変更箇所の前後を抽出（著作権対応） - 両方で同じ範囲を表示"""
    import re

    # HTMLタグを含む文字列から変更箇所を検出
    has_old_diff = 'diff-removed' in old_html
    has_new_diff = 'diff-added' in new_html

    if not has_old_diff and not has_new_diff:
        # 変更なしの場合は最初の200文字
        return old_html[:200] + ('...' if len(old_html) > 200 else ''), new_html[:200] + ('...' if len(new_html) > 200 else '')

    # HTMLタグを除去してプレーンテキストの長さを計算
    def strip_tags(html):
        return re.sub(r'<[^>]+>', '', html)

    old_plain = strip_tags(old_html)
    new_plain = strip_tags(new_html)

    # 変更箇所の大まかな位置を特定
    if has_old_diff and has_new_diff:
        # 置換の場合：両方の変更箇所の前後を表示
        old_diff_start = old_html.find('<span class="diff-removed">')
        new_diff_start = new_html.find('<span class="diff-added">')

        # HTMLタグより前の実際の文字数を概算
        old_text_before = strip_tags(old_html[:old_diff_start])
        new_text_before = strip_tags(new_html[:new_diff_start])

        # 開始位置を決定（変更箇所の前context_chars文字）
        start_pos = max(0, min(len(old_text_before), len(new_text_before)) - context_chars)

    elif has_new_diff and not has_old_diff:
        # 追加のみの場合：末尾に追加されたケース
        # 両方で末尾context_chars文字を表示
        start_pos = max(0, len(old_plain) - context_chars)

    elif has_old_diff and not has_new_diff:
        # 削除のみの場合
        old_diff_start = old_html.find('<span class="diff-removed">')
        old_text_before = strip_tags(old_html[:old_diff_start])
        start_pos = max(0, len(old_text_before) - context_chars)
    else:
        start_pos = 0

    # 同じ開始位置からコンテキストを抽出する関数
    def extract_from_position(html, plain_text, start_pos):
        if start_pos == 0:
            # 最初から
            return html, False

        # start_pos文字目から始まるようにHTMLを分割
        char_count = 0
        html_pos = 0
        in_tag = False

        for i, char in enumerate(html):
            if char == '<':
                in_tag = True
            elif char == '>':
                in_tag = False
            elif not in_tag:
                if char_count == start_pos:
                    html_pos = i
                    break
                char_count += 1

        if html_pos > 0:
            return html[html_pos:], True
        return html, False

    old_context, old_truncated = extract_from_position(old_html, old_plain, start_pos)
    new_context, new_truncated = extract_from_position(new_html, new_plain, start_pos)

    # 長さ制限（context_chars * 3程度）
    max_len = context_chars * 3

    def limit_length(html, max_chars):
        plain = strip_tags(html)
        if len(plain) <= max_chars:
            return html, False

        # max_chars文字目でカット
        char_count = 0
        in_tag = False

        for i, char in enumerate(html):
            if char == '<':
                in_tag = True
            elif char == '>':
                in_tag = False
            elif not in_tag:
                if char_count >= max_chars:
                    return html[:i], True
                char_count += 1

        return html, False

    old_context, old_end_truncated = limit_length(old_context, max_len)
    new_context, new_end_truncated = limit_length(new_context, max_len)

    # 省略記号を追加
    if old_truncated:
        old_context = '...' + old_context
    if old_end_truncated:
        old_context = old_context + '...'

    if new_truncated:
        new_context = '...' + new_context
    if new_end_truncated:
        new_context = new_context + '...'

    return old_context, new_context

def remove_duplicate_title(text, title):
    """テキストの末尾に重複しているタイトルを除去"""
    if not text or not title:
        return text

    # タイトルを正規化
    normalized_title = title.strip()
    normalized_text = text.strip()

    # 完全一致チェック
    if normalized_text.endswith(normalized_title):
        text_without_title = normalized_text[:-len(normalized_title)].rstrip('\n').rstrip()
        return text_without_title

    # 部分一致チェック（タイトルの80%以上が末尾に含まれる場合）
    # 空白や助詞の違いを吸収
    title_words = normalized_title.replace(' ', '').replace('　', '')

    # テキストの末尾から100文字を取得して比較
    text_end = normalized_text[-min(len(normalized_text), len(normalized_title) + 50):]
    text_end_normalized = text_end.replace(' ', '').replace('　', '').replace('\n', '')

    # タイトルの主要部分（最初の文字と最後の文字）が含まれているか
    if title_words and len(title_words) > 3:
        # タイトルの70%以上がテキスト末尾に含まれているか確認
        matching_chars = sum(1 for c in title_words if c in text_end_normalized)
        similarity = matching_chars / len(title_words)

        if similarity > 0.7 and text_end_normalized.endswith(title_words[-10:]):
            # 末尾の類似部分を探して除去
            # 最後の改行以降を除去
            parts = normalized_text.rsplit('\n', 1)
            if len(parts) == 2 and len(parts[1].strip()) < len(normalized_title) + 20:
                return parts[0].rstrip()

    return text

def generate_char_level_diff(old_text, new_text, title=None):
    """文字レベルの差分をハイライト表示"""
    if not old_text and not new_text:
        return "", ""

    if not old_text:
        old_text = ""
    if not new_text:
        new_text = ""

    # タイトルの重複を除去
    if title:
        old_text = remove_duplicate_title(old_text, title)
        new_text = remove_duplicate_title(new_text, title)

    # SequenceMatcherで文字レベルの差分を取得
    matcher = difflib.SequenceMatcher(None, old_text, new_text)

    old_html = []
    new_html = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        old_chunk = old_text[i1:i2]
        new_chunk = new_text[j1:j2]

        if tag == 'equal':
            # 変更なし
            old_html.append(old_chunk)
            new_html.append(new_chunk)
        elif tag == 'delete':
            # 削除された部分（赤背景）
            old_html.append(f'<span class="diff-removed">{old_chunk}</span>')
        elif tag == 'insert':
            # 追加された部分（緑背景）
            new_html.append(f'<span class="diff-added">{new_chunk}</span>')
        elif tag == 'replace':
            # 置き換え（赤と緑）
            old_html.append(f'<span class="diff-removed">{old_chunk}</span>')
            new_html.append(f'<span class="diff-added">{new_chunk}</span>')

    return ''.join(old_html), ''.join(new_html)

def generate_inline_diff_html(old_text, new_text, title=None):
    """インライン形式の差分（文字単位ハイライト付き）- 著作権対応で要約表示

    Returns:
        HTMLコンテンツ、または変更がない場合はNone
    """
    if not old_text:
        old_text = ""
    if not new_text:
        new_text = ""

    # 訂正キーワードの有無を確認
    has_correction_keywords = ('※' in old_text or '失礼しました' in old_text or
                               '※' in new_text or '失礼しました' in new_text)

    if has_correction_keywords:
        # 訂正記事の場合は訂正部分を優先的に抽出（著作権対応）
        old_summary = extract_correction_summary(old_text, 200) if old_text else ''
        new_summary = extract_correction_summary(new_text, 200) if new_text else ''
    else:
        # 通常の変更の場合は全文でdiffを取る
        old_summary = old_text
        new_summary = new_text

    # 文字レベルの差分を生成（タイトル重複除去付き）
    old_highlighted, new_highlighted = generate_char_level_diff(old_summary, new_summary, title)

    # タイトル重複除去後に変更がなくなった場合はNoneを返す
    # HTMLタグを除去して比較
    import re
    old_plain = re.sub(r'<[^>]+>', '', old_highlighted).strip()
    new_plain = re.sub(r'<[^>]+>', '', new_highlighted).strip()

    if old_plain == new_plain:
        return None  # 変更なし

    # 著作権対応: 訂正キーワードがない場合は変更箇所周辺のみ表示
    if not has_correction_keywords:
        old_highlighted, new_highlighted = extract_diff_context(old_highlighted, new_highlighted)

    html_parts = []
    html_parts.append('<div class="inline-diff">')

    if has_correction_keywords:
        html_parts.append('<div style="color: #999; font-size: 0.9em; font-style: italic; margin-bottom: 8px;">【引用】以下は記事内容の一部抜粋です（変更箇所は赤/緑でハイライト）</div>')
    else:
        html_parts.append('<div style="color: #999; font-size: 0.9em; font-style: italic; margin-bottom: 8px;">【引用】変更箇所の前後を表示しています（赤/緑でハイライト）</div>')

    # 削除部分
    if old_text:
        html_parts.append('<div class="diff-old">')
        html_parts.append('<span class="label">変更前:</span>\n')
        html_parts.append(f'<span class="text">{old_highlighted}</span>')
        html_parts.append('</div>')

    # 追加部分（おことわりハイライト適用）
    if new_text:
        # おことわりハイライトを適用
        highlighted_new_with_notice = highlight_correction_notice(new_highlighted)
        html_parts.append('<div class="diff-new">')
        html_parts.append('<span class="label">変更後:</span>\n')
        html_parts.append(f'<span class="text">{highlighted_new_with_notice}</span>')
        html_parts.append('</div>')

    html_parts.append('</div>')
    return '\n'.join(html_parts)

def generate_addition_html(new_text):
    """追記専用の表示（変更前を表示せず、要約表示）- 著作権対応"""
    if not new_text:
        new_text = ""

    # 訂正部分を優先的に抽出（著作権対応）
    new_summary = extract_correction_summary(new_text, 200)

    # おことわりハイライト適用
    highlighted_text = highlight_correction_notice(new_summary)

    html_parts = []
    html_parts.append('<div class="inline-diff">')
    html_parts.append('<div style="color: #999; font-size: 0.9em; font-style: italic; margin-bottom: 8px;">【引用】以下は記事内容の一部抜粋です</div>')
    html_parts.append('<div class="diff-new">')
    html_parts.append('<span class="label">追記内容:</span>\n')
    html_parts.append(f'<span class="text">{highlighted_text}</span>')
    html_parts.append('</div>')
    html_parts.append('</div>')
    return '\n'.join(html_parts)

def generate_html(changes, output_path):
    """HTMLファイルを生成"""

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NHK記事変更履歴 - 全履歴</title>

    <!-- Favicon -->
    <link rel="icon" type="image/x-icon" href="favicon.ico">
    <link rel="apple-touch-icon" href="apple-touch-icon.png">

    <!-- OGP (Open Graph Protocol) -->
    <meta property="og:title" content="NHK記事変更履歴 - 全履歴" />
    <meta property="og:description" content="NHK地方局ニュースの変更履歴を時系列で表示。訂正記事の自動検出と差分表示が可能。" />
    <meta property="og:image" content="https://nhk-news-tracker.netlify.app/ogp-image.png" />
    <meta property="og:url" content="https://nhk-news-tracker.netlify.app/history.html" />
    <meta property="og:type" content="website" />

    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:title" content="NHK記事変更履歴 - 全履歴" />
    <meta name="twitter:description" content="NHK地方局ニュースの変更履歴を時系列で表示。訂正記事の自動検出と差分表示が可能。" />
    <meta name="twitter:image" content="https://nhk-news-tracker.netlify.app/ogp-image.png" />

    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Hiragino Sans', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 0;
            margin: 0;
            line-height: 1.4;
            padding-top: 60px; /* グローバルナビの高さ分 */
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 15px;
        }}

        /* グローバルナビゲーション */
        .global-nav {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: rgba(255, 255, 255, 0.98);
            backdrop-filter: blur(10px);
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            z-index: 1000;
            border-bottom: 2px solid #667eea;
        }}

        .global-nav-content {{
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 20px;
        }}

        .global-nav-logo {{
            font-size: 1.3em;
            font-weight: bold;
            color: #2d3748;
            text-decoration: none;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .global-nav-links {{
            display: flex;
            gap: 25px;
            align-items: center;
        }}

        .global-nav-link {{
            color: #4a5568;
            text-decoration: none;
            font-weight: 500;
            font-size: 0.95em;
            transition: color 0.2s;
            padding: 8px 12px;
            border-radius: 6px;
        }}

        .global-nav-link:hover {{
            color: #667eea;
            background: #f7fafc;
        }}

        .global-nav-link.active {{
            color: #667eea;
            background: #edf2f7;
        }}

        header {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
            text-align: center;
        }}

        h1 {{
            color: #2d3748;
            font-size: 2.5em;
            margin-bottom: 10px;
        }}

        .subtitle {{
            color: #718096;
            font-size: 1.1em;
        }}

        .stats {{
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-top: 20px;
        }}

        .stat-item {{
            text-align: center;
        }}

        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}

        .stat-label {{
            color: #718096;
            font-size: 0.9em;
        }}

        .change-card {{
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }}

        .change-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.15);
        }}

        .change-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 15px;
            padding-bottom: 15px;
            border-bottom: 2px solid #e2e8f0;
        }}

        .change-type {{
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.85em;
            text-transform: uppercase;
        }}

        .type-title {{
            background: #fef3c7;
            color: #92400e;
        }}

        .type-description {{
            background: #fed7aa;
            color: #9a3412;
        }}

        .type-correction {{
            background: #fecaca;
            color: #991b1b;
        }}

        .change-time {{
            color: #718096;
            font-size: 0.85em;
            text-align: right;
        }}

        .change-time div {{
            margin: 2px 0;
        }}

        .change-source {{
            color: #4a5568;
            font-weight: bold;
            margin-bottom: 10px;
        }}

        .change-link {{
            color: #667eea;
            text-decoration: none;
            font-size: 0.9em;
            word-break: break-all;
        }}

        .change-link:hover {{
            text-decoration: underline;
        }}

        .inline-diff {{
            margin: 20px 0;
        }}

        .diff-old, .diff-new {{
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
            white-space: pre-wrap;
            word-wrap: break-word;
            line-height: 1.8;
        }}

        .diff-old {{
            background: #fee;
            border-left: 4px solid #f00;
        }}

        .diff-new {{
            background: #efe;
            border-left: 4px solid #0a0;
        }}

        .label {{
            font-weight: bold;
            margin-right: 10px;
        }}

        .diff-old .label {{
            color: #c00;
        }}

        .diff-new .label {{
            color: #0a0;
        }}

        .text {{
            color: #2d3748;
        }}

        .diff-container {{
            background: #1e1e1e;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            font-family: 'Monaco', 'Courier New', monospace;
            font-size: 0.9em;
            overflow-x: auto;
        }}

        .diff-line {{
            padding: 2px 10px;
            white-space: pre-wrap;
            word-break: break-all;
        }}

        .diff-line.deleted {{
            background: #4d1f1f;
            color: #ff9999;
        }}

        .diff-line.added {{
            background: #1f4d1f;
            color: #99ff99;
        }}

        .diff-line.unchanged {{
            color: #999;
        }}

        .no-changes {{
            text-align: center;
            padding: 60px;
            color: #718096;
            font-size: 1.2em;
        }}

        .correction-keywords {{
            background: #fef3c7;
            padding: 10px 15px;
            border-radius: 8px;
            margin: 10px 0;
            color: #92400e;
        }}

        .correction-notice {{
            background: #ffeb3b;
            border-left: 4px solid #d32f2f;
            padding: 8px 12px;
            margin: 8px 0;
            display: inline-block;
            border-radius: 4px;
            font-weight: bold;
            color: #d32f2f;
        }}

        /* 文字レベルの差分ハイライト */
        .diff-removed {{
            background: #ffcdd2;
            color: #c62828;
            padding: 2px 4px;
            border-radius: 3px;
            font-weight: bold;
            text-decoration: line-through;
        }}

        .diff-added {{
            background: #c8e6c9;
            color: #2e7d32;
            padding: 2px 4px;
            border-radius: 3px;
            font-weight: bold;
        }}

        .filter-bar {{
            background: white;
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}

        .filter-buttons {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }}

        .filter-btn {{
            padding: 10px 20px;
            border: 2px solid #e2e8f0;
            background: white;
            border-radius: 20px;
            cursor: pointer;
            transition: all 0.2s;
            font-weight: bold;
        }}

        .filter-btn:hover {{
            background: #f7fafc;
        }}

        .filter-btn.active {{
            background: #667eea;
            color: white;
            border-color: #667eea;
        }}

        /* モバイルファースト対応（スマートフォン最適化） */
        @media (max-width: 768px) {{
            .stats {{
                flex-direction: column;
                gap: 15px;
            }}

            .change-header {{
                flex-direction: column;
                align-items: flex-start;
                gap: 10px;
            }}

            .change-time {{
                text-align: left;
            }}
        }}

        @media (max-width: 480px) {{
            body {{
                padding-top: 55px;
            }}

            .global-nav-content {{
                padding: 10px 15px;
            }}

            .global-nav-logo {{
                font-size: 1.1em;
            }}

            .global-nav-links {{
                gap: 10px;
            }}

            .global-nav-link {{
                font-size: 0.85em;
                padding: 6px 8px;
            }}

            .change-card {{
                padding: 15px;
            }}

            .diff-old, .diff-new {{
                font-size: 0.85em;
                padding: 10px;
            }}
        }}
    </style>
</head>
<body>
    <!-- グローバルナビゲーション -->
    <nav class="global-nav">
        <div class="global-nav-content">
            <a href="index.html" class="global-nav-logo">📰 NHK記事追跡システム</a>
            <div class="global-nav-links">
                <a href="index.html" class="global-nav-link">ポータル</a>
                <a href="history.html" class="global-nav-link active">最近の変更</a>
                <a href="corrections.html" class="global-nav-link">おことわり</a>
                <a href="archive.html" class="global-nav-link">アーカイブ</a>
            </div>
        </div>
    </nav>

    <div class="container">
        <header>
            <h1>📰 NHK最近の変更</h1>
            <p class="subtitle">全ての変更を新しい順に表示（変更箇所は赤/緑でハイライト）</p>
            <div class="stats">
                <div class="stat-item">
                    <div class="stat-number">{len(changes)}</div>
                    <div class="stat-label">総変更数</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">{len([c for c in changes if c['change_type'] == 'title_changed'])}</div>
                    <div class="stat-label">タイトル変更</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">{len([c for c in changes if c['change_type'] in ('description_changed', 'description_added')])}</div>
                    <div class="stat-label">説明文変更</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">{len([c for c in changes if c['has_correction']])}</div>
                    <div class="stat-label">訂正関連</div>
                </div>
            </div>
        </header>

        <div class="filter-bar">
            <div class="filter-buttons">
                <button class="filter-btn active" onclick="filterChanges('all')">すべて</button>
                <button class="filter-btn" onclick="filterChanges('title')">タイトル変更</button>
                <button class="filter-btn" onclick="filterChanges('description')">説明文変更</button>
                <button class="filter-btn" onclick="filterChanges('correction')">訂正関連</button>
            </div>
        </div>
"""

    if not changes:
        html += """
        <div class="change-card">
            <div class="no-changes">
                まだ変更が記録されていません。<br>
                システムが1時間ごとに自動でチェックしています。
            </div>
        </div>
"""
    else:
        for change in changes:
            # old_value が空の場合も追記として扱う（既存データ対応）
            is_addition = (change['change_type'] == 'description_added' or
                          (not change['old_value'] and change['change_type'] in ('description_changed', 'description_added')))

            # 追記でない場合は、先にdiff_htmlを生成して変更があるか確認
            diff_html = None
            if not is_addition:
                # 説明文変更の場合のみタイトル重複を除去
                current_title = ''
                if change['change_type'] in ('description_changed', 'description_added'):
                    try:
                        current_title = change['current_title'] if change['current_title'] else ''
                    except (KeyError, TypeError):
                        current_title = ''

                diff_html = generate_inline_diff_html(change['old_value'], change['new_value'], current_title)

                # 変更がない場合（タイトル重複除去後に差分がなくなった）はスキップ
                if diff_html is None:
                    continue

            # ここから先は実際に変更があるものだけ
            change_type_class = {
                'title_changed': 'type-title',
                'description_changed': 'type-description',
                'description_added': 'type-description',
                'correction_removed': 'type-correction'
            }.get(change['change_type'], 'type-title')

            if is_addition and change['change_type'] in ('description_changed', 'description_added'):
                change_type_label = '説明文追記'
            else:
                change_type_label = {
                    'title_changed': 'タイトル変更',
                    'description_changed': '説明文変更',
                    'description_added': '説明文追記',
                    'correction_removed': '訂正削除'
                }.get(change['change_type'], change['change_type'])

            detected_at = datetime.fromisoformat(change['detected_at'])
            time_str = detected_at.strftime('%Y年%m月%d日 %H:%M:%S')

            # 変更前後の確認日時
            before_time = datetime.fromisoformat(change['before_change_time'])
            after_time = datetime.fromisoformat(change['after_change_time'])
            before_time_str = before_time.strftime('%Y年%m月%d日 %H:%M:%S')
            after_time_str = after_time.strftime('%Y年%m月%d日 %H:%M:%S')

            data_filter = []
            data_filter.append(change['change_type'].split('_')[0])
            if change['has_correction']:
                data_filter.append('correction')

            # 完全URLを生成
            full_url = get_full_url(change['source'], change['link'])

            html += f"""
        <div class="change-card" data-filter="{' '.join(data_filter)}">
            <div class="change-header">
                <div>
                    <span class="change-type {change_type_class}">{change_type_label}</span>
                    {f'<span class="change-type type-correction">訂正あり</span>' if change['has_correction'] else ''}
                </div>
                <div class="change-time">
                    <div>🕐 変更前確認: {before_time_str}</div>
                    <div>🕐 変更後確認: {after_time_str}</div>
                </div>
            </div>

            <div class="change-source">{change['source']}</div>
            <a href="{full_url}" class="change-link" target="_blank">{full_url}</a>

            {f'<div class="correction-keywords">🔴 おことわり</div>' if change['correction_keywords'] else ''}
"""

            # 追記の場合は専用表示、それ以外は既に生成したdiff_htmlを使用
            if is_addition:
                html += f"""            {generate_addition_html(change['new_value'])}
        </div>
"""
            else:
                html += f"""            {diff_html}
        </div>
"""

    html += """
    </div>

    <script>
        function filterChanges(type) {
            // ボタンのアクティブ状態を更新
            document.querySelectorAll('.filter-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            event.target.classList.add('active');

            // カードをフィルタリング
            const cards = document.querySelectorAll('.change-card');
            cards.forEach(card => {
                if (type === 'all') {
                    card.style.display = 'block';
                } else {
                    const filters = card.getAttribute('data-filter');
                    if (filters && filters.includes(type)) {
                        card.style.display = 'block';
                    } else {
                        card.style.display = 'none';
                    }
                }
            });
        }
    </script>

    <!-- NHKアクセストラッキング -->
    <script>
    (function() {
        try {
            var path = window.location.pathname + window.location.search;
            fetch('/.netlify/functions/track-access?path=' + encodeURIComponent(path), {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            }).catch(function(err) {
                console.log('Tracking skipped:', err);
            });
        } catch(e) {
            console.log('Tracking error:', e);
        }
    })();
    </script>
</body>
</html>
"""

    # HTMLファイルを書き込み
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✅ 変更履歴HTMLを生成しました: {output_path}")
    print(f"📊 総変更数: {len(changes)}件")

def main():
    """メイン処理"""
    db_path = PROJECT_ROOT / 'data' / 'articles.db'
    output_path = PROJECT_ROOT / 'reports' / 'history.html'

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("NHK記事変更履歴ビューアー")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()

    # データベースから変更履歴を取得
    print("📖 データベースから変更履歴を取得中...")
    changes = get_all_changes(db_path)

    print(f"✅ {len(changes)}件の変更を取得しました")
    print()

    # HTMLを生成
    print("🎨 HTMLレポートを生成中...")
    generate_html(changes, output_path)

    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"✅ 完了: {output_path}")
    print()
    print("次のコマンドで開きます:")
    print(f"  open {output_path}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

if __name__ == '__main__':
    main()
