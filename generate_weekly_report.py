#!/usr/bin/env python3
"""
週次誤情報レポート生成
直近1週間の訂正記事をClaude 4.5 Sonnetで分析
"""
import sqlite3
import os
from datetime import datetime, timedelta
from pathlib import Path
import anthropic

# Claude API設定
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY環境変数が設定されていません")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def get_weekly_corrections(db_path: str, days: int = 7) -> list:
    """直近N日間の訂正記事を取得"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # N日前の日時を計算
    cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

    # 訂正記事を取得（変更履歴と記事情報を結合）
    cursor.execute('''
        SELECT
            c.source,
            COALESCE(a.link, c.link) as link,
            a.title,
            c.change_type,
            c.old_value,
            c.new_value,
            c.detected_at,
            c.correction_keywords,
            a.description
        FROM changes c
        LEFT JOIN articles a ON c.link = a.link AND c.source = a.source
        WHERE (c.has_correction = 1 OR c.correction_keywords IS NOT NULL)
          AND (
            (c.correction_keywords LIKE '%当初%' AND c.correction_keywords LIKE '%掲載%')
            OR
            c.correction_keywords LIKE '%失礼しました%'
          )
          AND c.detected_at >= ?
        ORDER BY c.detected_at DESC
    ''', (cutoff_date,))

    corrections = []
    for row in cursor.fetchall():
        corrections.append({
            'source': row[0],
            'link': row[1],
            'title': row[2],
            'change_type': row[3],
            'old_value': row[4],
            'new_value': row[5],
            'detected_at': row[6],
            'correction_keywords': row[7],
            'description': row[8]
        })

    conn.close()
    return corrections


def convert_to_full_url(source: str, link: str) -> str:
    """相対パスを完全なURLに変換"""
    if link.startswith('http://') or link.startswith('https://'):
        return link

    base_urls = {
        'NHK首都圏ニュース': 'https://www3.nhk.or.jp/shutoken-news/',
        'NHK東海ニュース': 'https://www3.nhk.or.jp/tokai-news/',
        'NHK関西ニュース': 'https://www3.nhk.or.jp/kansai-news/',
        'NHK広島ニュース': 'https://www3.nhk.or.jp/hiroshima-news/',
        'NHK福岡ニュース': 'https://www3.nhk.or.jp/fukuoka-news/',
        'NHK札幌ニュース': 'https://www3.nhk.or.jp/sapporo-news/',
        'NHK東北ニュース': 'https://news.web.nhk/tohoku/',
        'NHKニュース': 'https://www3.nhk.or.jp/news/',
    }

    # NHK東北ニュースの特殊処理
    if source == 'NHK東北ニュース':
        import re
        match = re.search(r'(\d+)\.html$', link)
        if match:
            article_id = match.group(1)
            return f'https://news.web.nhk/newsweb/na/nb-{article_id}'

    if source in base_urls:
        return base_urls[source] + link

    return link


def create_analysis_prompt(corrections: list, start_date: str, end_date: str) -> str:
    """Claude用のプロンプトを生成"""

    # 訂正記事の詳細情報を整形
    corrections_text = ""
    for i, corr in enumerate(corrections, 1):
        full_url = convert_to_full_url(corr['source'], corr['link'])

        corrections_text += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【訂正記事 {i}/{len(corrections)}】

◆ソース: {corr['source']}
◆タイトル: {corr['title']}
◆URL: {full_url}
◆検出日時: {corr['detected_at']}
◆変更種別: {corr['change_type']}

【訂正前の内容】
{corr['old_value'] or '（初回掲載時はこの情報なし）'}

【訂正後の内容（現在の記事本文）】
{corr['new_value'] or corr['description'] or '（取得できず）'}

【訂正キーワード】
{corr['correction_keywords']}

"""

    prompt = f"""あなたは報道倫理を専門とする研究者であり、メディア批評の第一人者です。

【タスク】
NHK地方局ニュースにおける直近1週間（{start_date}〜{end_date}）の訂正記事全{len(corrections)}件を分析し、
学術論文の水準に耐えうる「今週の誤情報レポート」を作成してください。

【分析対象】
以下の{len(corrections)}件の訂正記事について、誤りの内容と深刻度を徹底的に分析してください。

{corrections_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【レポート作成の根本原則】

**基本認識：NHKの報道は正確でなければならない**

公共放送として国民の受信料で運営されるNHKには、報道の正確性を担保する絶対的責任がある。
「些細な誤り」という言い訳は存在しない。全ての誤報は、ジャーナリズムの本質的欠陥の表れである。

1. **深刻度の判定基準**
   ★☆☆☆☆：表記の誤り（固有名詞の誤記）← ただし、これも取材不足の証左
   ★★☆☆☆：事実関係の誤り（日時、数値）← 確認作業の怠慢
   ★★★☆☆：重要事実の誤り（地名、人名、組織名）← 知識の欠如
   ★★★★☆：本質に関わる誤り（容疑内容、被害規模）← ジャーナリストの資質の欠如
   ★★★★★：社会的影響甚大（人権侵害、冤罪）← 報道機関として失格

2. **論評のトーン：本質を鋭く追求する**
   - 短く、密度高く、核心のみを突く
   - 「なぜこの誤りが発生したか」の構造的分析
   - 取材不足、裏取り不足、知識不足、教養不足、疑う力の不足を容赦なく指摘
   - 関係者の当事者意識の欠如、プロ意識の欠如を厳しく批判
   - 「訂正すれば済む」という甘えを許さない

3. **文体：硬質な論文調**
   - 感情的表現を排し、事実と論理で批判
   - 断定的に、簡潔に、的確に
   - 冗長な説明は不要。本質のみを抽出
   - 「本週」という表現は使用せず、「今週」を使用
   - 「示唆」「露呈」などの抽象表現は最小限にし、具体的な問題点を明示

4. **構成要件**
   - **必ず深刻度の高い順に並べる**（★★★★★→★★★★☆→...の順）
   - 全ての訂正記事を分析（漏れなく）
   - 今週の概要：論文の要旨として、硬質な文体で

【出力形式】

以下のHTML形式で、学術論文の水準で出力してください。
**HTMLタグのみを出力し、余計な説明や```htmlなどのマークダウン記法は一切含めないこと。**

<div class="report-content">
<h1>今週の誤情報レポート（{end_date}）</h1>

<h2>📊 今週の概要</h2>
<ul>
<li>訂正記事数: XX件</li>
<li>最多訂正ソース: XXX</li>
<li>深刻度★★★以上: XX件</li>
</ul>

<div class="abstract">
<strong>【要旨】</strong>
<p>今週、NHK地方局ニュースにおいてXX件の訂正が確認された。うちXX件は深刻度★★★以上であり、
報道機関としての基本的資質が問われる事態である。XXXにおける誤りは、取材の初歩的段階での
確認不足であり、具体的には【取材源への確認を怠った / 裏取りを行わなかった / 記憶や憶測で記述した】
などの問題が明白である。公共放送としての責任を自覚せず、安易な訂正で済ませる姿勢は、
ジャーナリズムの根幹を揺るがす。</p>
</div>

<hr>

<h2>🔴 訂正記事の詳細分析（深刻度順）</h2>

<div class="correction-item">
<h3>1. [ソース名] タイトル</h3>
<p><strong>深刻度</strong>: ★★★★☆<br>
<strong>検出日時</strong>: YYYY-MM-DD HH:MM:SS<br>
<strong>URL</strong>: <a href="URL" target="_blank">記事を開く</a></p>

<h4>誤りの内容</h4>
<p>訂正前：XXX → 訂正後：XXX</p>

<h4>論評</h4>
<p>XXXの誤りは、取材時の裏取り不足に起因する。XXXを確認すれば防げた初歩的ミスであり、
記者の知識不足と当事者意識の欠如が露呈している。報道の正確性を軽視する組織文化の問題。</p>
</div>

<hr>

（以下、深刻度の高い順に全ての訂正記事を<div class="correction-item">で囲んで分析）

<hr>

<h2>📝 総評：構造的欠陥としての誤報</h2>
<p>今週の訂正記事は、NHK地方局報道における構造的欠陥を浮き彫りにした。</p>

<div class="problems">
<h3>【問題の本質】</h3>
<ol>
<li><strong>取材体制の脆弱性</strong> - 確認作業の形骸化、裏取りの軽視</li>
<li><strong>人材の質的劣化</strong> - 基礎的知識の欠如、疑う力の不足</li>
<li><strong>組織文化の腐敗</strong> - 「訂正すれば済む」という安易な姿勢、当事者意識の欠如</li>
</ol>
</div>

<div class="recommendations">
<h3>【提言】</h3>
<p>公共放送は、存在意義そのものが問われている。受信料で運営される組織として、
報道の正確性は絶対条件である。構造的改革なくして信頼回復はあり得ない。
人材育成、取材体制の再構築、組織文化の刷新を、今すぐ断行すべきである。</p>
</div>
</div>

【執筆における厳守事項】
1. **全ての訂正記事を深刻度順に分析** - 漏れは許されない
2. **論評は100-150文字** - 冗長な説明は不要、本質のみを抽出
3. **具体的な固有名詞・数値を引用** - 抽象論ではなく事実で批判
4. **硬質な文体を貫く** - 感情的表現は排除、論理と事実で批判
5. **構造的問題を指摘** - 個別の誤りではなく、組織の根本的欠陥を浮き彫りに
6. **HTML形式で直接出力** - ```htmlなどのマークダウン記法は不要、純粋なHTMLのみ

【絶対禁止表現リスト】★★★重要★★★

以下の表現は**絶対に使用してはならない**。違反は許されない。

❌ 禁止：「些細な誤り」「些細な点」「些細ではあるが」
❌ 禁止：「軽微な」「軽微ではあるが」
❌ 禁止：「小さな」「小さなミス」
❌ 禁止：「ちょっとした」「わずかな」
❌ 禁止：「大したことではない」「問題ない」

【代替表現（必ずこちらを使用）】

✅ 使用すべき表現：
- 「この誤りは～」（客観的事実から始める）
- 「～の誤りは、取材の基本的確認を欠いている」
- 「～は、報道機関としての正確性を損なう」
- 「～という誤りは、情報伝達の信頼性を揺るがす」
- 「～は、確認体制の甘さを示す」

【悪い例 vs 良い例】

❌ 悪い例：「些細な誤りではあるが、公共放送としての責任を自覚すべきである。」
✅ 良い例：「この誤りは、情報確認体制の甘さを露呈している。公共放送としての責任を自覚すべきである。」

❌ 悪い例：「すだちとかぼすの誤記は、些細な点ではあるが、正確性を重んじる報道機関としては看過できない。」
✅ 良い例：「すだちとかぼすの誤記は、取材対象への知識不足を示している。正確性を重んじる報道機関としては看過できない。」

それでは、上記の**禁止表現を絶対に使わず**、訂正記事データに基づいて「今週の誤情報レポート」を作成してください。
"""

    return prompt


def validate_forbidden_expressions(text: str) -> tuple[bool, list[str]]:
    """禁止表現の検出"""
    forbidden = [
        '些細な誤り',
        '些細な点',
        '些細ではあるが',
        '些細な',
        '軽微な',
        '小さな',
        'ちょっとした',
        'わずかな',
        '大したことではない',
        '問題ない',
    ]

    found = []
    for expr in forbidden:
        if expr in text:
            found.append(expr)

    return (len(found) == 0, found)


def analyze_with_claude(prompt: str) -> str:
    """Claude 4.5 Sonnetで分析"""

    print("🤖 Claude 4.5 Sonnetで分析中...")
    print(f"📊 プロンプト文字数: {len(prompt):,}文字")

    max_retries = 3
    for attempt in range(max_retries):
        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=8000,
            temperature=0.7,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        response_text = message.content[0].text

        # 禁止表現チェック
        is_valid, forbidden_found = validate_forbidden_expressions(response_text)

        if is_valid:
            print("✅ 禁止表現の検出なし")
            print(f"📊 生成トークン数: {message.usage.output_tokens:,}")
            return response_text
        else:
            print(f"⚠️ 禁止表現を検出（試行{attempt + 1}/{max_retries}）: {', '.join(forbidden_found)}")
            if attempt < max_retries - 1:
                print("🔄 再生成を試みます...")
                # プロンプトに警告を追加して再試行
                prompt += f"\n\n【重要な警告】前回の出力に禁止表現「{', '.join(forbidden_found)}」が含まれていました。これらの表現は絶対に使用しないでください。"
            else:
                print("❌ 最大試行回数に達しました。禁止表現を含むまま出力します（手動で修正してください）")
                return response_text

    return response_text


def main():
    """メイン処理"""
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("週次誤情報レポート生成")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # データベースパス
    db_path = 'data/articles.db'

    # 直近7日間の訂正記事を取得
    print("\n📅 直近7日間の訂正記事を取得中...")
    corrections = get_weekly_corrections(db_path, days=7)

    if not corrections:
        print("❌ 訂正記事が見つかりませんでした")
        return

    print(f"✅ {len(corrections)}件の訂正記事を取得しました")

    # 日付範囲
    end_date = datetime.now().strftime('%Y年%m月%d日')
    start_date = (datetime.now() - timedelta(days=7)).strftime('%Y年%m月%d日')

    # Claudeプロンプト生成
    print("\n📝 Claudeプロンプトを生成中...")
    prompt = create_analysis_prompt(corrections, start_date, end_date)

    # Claude 4.5 Sonnetで分析
    print("\n🔍 Claude 4.5 Sonnetで分析を実行中...")
    report_html = analyze_with_claude(prompt)

    # HTMLから余計なマークダウン記法を削除
    report_html = report_html.replace('```html', '').replace('```', '').strip()

    # 完全なHTMLページを生成
    timestamp = datetime.now().strftime('%Y%m%d')

    full_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>今週の誤情報レポート（{end_date}）</title>
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
        ul, ol {{
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
        .abstract {{
            background: #fff3e0;
            padding: 20px;
            border-left: 5px solid #ff9800;
            margin: 20px 0;
            border-radius: 5px;
        }}
        .correction-item {{
            background: #fafafa;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            border-left: 4px solid #d32f2f;
        }}
        .problems, .recommendations {{
            background: #e3f2fd;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
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
    </style>
</head>
<body>
    <div class="container">
{report_html}
        <p style="text-align: center; margin-top: 50px;">
            <a href="../index.html" class="back-link">← ポータルに戻る</a>
        </p>
    </div>
</body>
</html>
"""

    # レポート保存
    output_dir = Path('reports/weekly')
    output_dir.mkdir(parents=True, exist_ok=True)

    html_output_path = output_dir / f'weekly_report_{timestamp}.html'

    with open(html_output_path, 'w', encoding='utf-8') as f:
        f.write(full_html)

    print(f"\n✅ HTMLレポートを保存しました: {html_output_path}")
    print(f"📂 ファイルサイズ: {html_output_path.stat().st_size:,} bytes")
    print("\n" + "="*70)
    print("📄 生成されたHTML（抜粋）:")
    print("="*70)
    print(report_html[:500] + "...")
    print("="*70)


if __name__ == '__main__':
    main()
