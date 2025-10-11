#!/usr/bin/env python3
"""
Gemini API テスト
"""
from gemini_analyzer import GeminiAnalyzer

def test_gemini():
    """Gemini API の動作確認"""
    print("="*60)
    print("Gemini API テスト")
    print("="*60)

    analyzer = GeminiAnalyzer()

    if not analyzer.enabled:
        print("\n❌ Gemini API が無効です")
        print("環境変数 GEMINI_API_KEY が設定されていません")
        return

    print("\n✅ Gemini API が有効です")

    # テスト1: 記事変更の分析
    print("\n" + "-"*60)
    print("テスト1: 記事変更の分析")
    print("-"*60)

    old_text = "東京都内で交通事故が発生し、1人が軽傷を負いました。"
    new_text = "東京都内で交通事故が発生し、3人が重傷を負いました。"
    title = "東京で交通事故"

    print(f"\n変更前: {old_text}")
    print(f"変更後: {new_text}")

    summary = analyzer.analyze_change(old_text, new_text, title)

    if summary:
        print(f"\n🤖 AI分析: {summary}")
    else:
        print("\n❌ AI分析に失敗しました")

    # テスト2: 訂正内容の分析
    print("\n" + "-"*60)
    print("テスト2: 訂正内容の分析")
    print("-"*60)

    correction_text = """
    東京都内で交通事故が発生しました。
    ※当初、「軽傷」と掲載しましたが、「重傷」の誤りでした。失礼しました。
    """
    keywords = ['当初', '掲載', '失礼しました', '※']

    print(f"\n訂正テキスト: {correction_text.strip()}")
    print(f"検出キーワード: {', '.join(keywords)}")

    correction_summary = analyzer.analyze_correction(correction_text, keywords)

    if correction_summary:
        print(f"\n🤖 訂正分析: {correction_summary}")
    else:
        print("\n❌ 訂正分析に失敗しました")

    print("\n" + "="*60)
    print("テスト完了")
    print("="*60)

if __name__ == '__main__':
    test_gemini()
