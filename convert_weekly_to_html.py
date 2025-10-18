#!/usr/bin/env python3
"""週次レポートをHTMLに変換"""
import re
from pathlib import Path
from datetime import datetime

def markdown_to_html(md_text: str) -> str:
    """簡易Markdown→HTML変換"""
    # コードブロックを削除
    html = md_text.replace('```markdown', '').replace('```', '')
    
    # 見出しを変換
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)
    
    # リンクを変換
    html = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2" target="_blank">\1</a>', html)
    
    # 太字を変換
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    
    # リストを変換
    html = re.sub(r'^\- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
    html = re.sub(r'^\d+\. (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
    
    # 段落を変換
    paragraphs = html.split('\n\n')
    html_paragraphs = []
    in_list = False
    
    for para in paragraphs:
        if '<li>' in para:
            if not in_list:
                html_paragraphs.append('<ul>')
                in_list = True
            html_paragraphs.append(para)
        else:
            if in_list:
                html_paragraphs.append('</ul>')
                in_list = False
            if para.strip() and not para.startswith('<h') and para.strip() != '---':
                html_paragraphs.append(f'<p>{para}</p>')
            elif para.strip() == '---':
                html_paragraphs.append('<hr>')
            else:
                html_paragraphs.append(para)
    
    if in_list:
        html_paragraphs.append('</ul>')
    
    return '\n'.join(html_paragraphs)

# レポートを読み込み
md_file = Path('reports/weekly/weekly_report_20251012.md')
with open(md_file, 'r', encoding='utf-8') as f:
    md_content = f.read()

# HTMLに変換
html_body = markdown_to_html(md_content)

# 完全なHTMLを生成
html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>今週の誤情報レポート（2025年10月12日）</title>
    <link rel="icon" type="image/x-icon" href="../favicon.ico">
    
    <!-- OGP -->
    <meta property="og:title" content="今週の誤情報レポート | NHK記事追跡システム" />
    <meta property="og:description" content="直近1週間の訂正記事を分析。誤りの内容と深刻度を厳しく論評します。" />
    <meta property="og:image" content="https://nhk-news-tracker.netlify.app/ogp-image.png" />
    
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Hiragino Sans', sans-serif;
            line-height: 1.8;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            color: #333;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        h1 {{
            color: #d32f2f;
            border-bottom: 3px solid #d32f2f;
            padding-bottom: 15px;
            margin-bottom: 30px;
            font-size: 2em;
        }}
        h2 {{
            color: #1976d2;
            margin-top: 40px;
            margin-bottom: 20px;
            font-size: 1.5em;
            border-left: 5px solid #1976d2;
            padding-left: 15px;
        }}
        h3 {{
            color: #424242;
            margin-top: 30px;
            margin-bottom: 15px;
            font-size: 1.3em;
            background: #f5f5f5;
            padding: 10px 15px;
            border-radius: 5px;
        }}
        h4 {{
            color: #616161;
            margin-top: 20px;
            margin-bottom: 10px;
            font-size: 1.1em;
        }}
        p {{
            margin-bottom: 15px;
            color: #424242;
        }}
        ul {{
            margin-left: 25px;
            margin-bottom: 15px;
        }}
        li {{
            margin-bottom: 8px;
        }}
        a {{
            color: #1976d2;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        hr {{
            border: none;
            border-top: 2px solid #e0e0e0;
            margin: 30px 0;
        }}
        strong {{
            color: #d32f2f;
            font-weight: bold;
        }}
        .back-link {{
            display: inline-block;
            margin-top: 40px;
            padding: 12px 30px;
            background: #1976d2;
            color: white !important;
            border-radius: 8px;
            text-decoration: none;
            font-weight: bold;
            transition: background 0.2s;
        }}
        .back-link:hover {{
            background: #1565c0;
            text-decoration: none;
        }}
        .severity-5 {{ color: #c62828; }}
        .severity-4 {{ color: #d32f2f; }}
        .severity-3 {{ color: #e64a19; }}
        .severity-2 {{ color: #f57c00; }}
        .severity-1 {{ color: #fbc02d; }}
    </style>
</head>
<body>
    <div class="container">
{html_body}
        <p style="text-align: center; margin-top: 50px;">
            <a href="../index.html" class="back-link">← ポータルに戻る</a>
        </p>
    </div>
</body>
</html>
"""

# HTMLファイルを保存
output_file = Path('reports/weekly/weekly_report_20251012.html')
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"✅ HTMLレポートを生成しました: {output_file}")
print(f"📂 ファイルサイズ: {output_file.stat().st_size:,} bytes")
