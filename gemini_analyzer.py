#!/usr/bin/env python3
"""
Gemini API統合 - 記事変更の分析
"""
import os
import logging
from typing import Optional
import requests

logger = logging.getLogger(__name__)

class GeminiAnalyzer:
    """Gemini API を使用した記事変更の分析"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: Gemini API キー（環境変数 GEMINI_API_KEY から取得）
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            logger.warning("GEMINI_API_KEY が設定されていません。AI分析は無効です。")
            self.enabled = False
        else:
            self.enabled = True
            logger.info("Gemini API 統合が有効になりました")

    def analyze_change(self, old_text: str, new_text: str, title: str = "") -> Optional[str]:
        """
        記事の変更内容を分析

        Args:
            old_text: 変更前のテキスト
            new_text: 変更後のテキスト
            title: 記事タイトル（オプション）

        Returns:
            AI分析サマリー（簡潔な変更説明）
        """
        if not self.enabled:
            return None

        if not old_text or not new_text:
            return None

        try:
            # Gemini 2.0 Flash を使用
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={self.api_key}"

            prompt = f"""以下は、NHKニュース記事の変更内容です。変更点を簡潔に分析し、重要な変更を50文字以内で要約してください。

記事タイトル: {title}

【変更前】
{old_text[:500]}

【変更後】
{new_text[:500]}

要約（50文字以内）:"""

            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "temperature": 0.3,
                    "maxOutputTokens": 100
                }
            }

            headers = {
                "Content-Type": "application/json"
            }

            response = requests.post(url, json=payload, headers=headers, timeout=30)

            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    summary = result['candidates'][0]['content']['parts'][0]['text'].strip()
                    logger.info(f"AI分析完了: {title[:30]}...")
                    return summary
                else:
                    logger.warning("AIレスポンスが空です")
                    return None
            else:
                logger.error(f"Gemini APIエラー: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"AI分析エラー: {e}")
            return None

    def analyze_correction(self, text: str, keywords: list[str]) -> Optional[str]:
        """
        訂正内容を分析

        Args:
            text: 訂正を含むテキスト
            keywords: 検出されたキーワード

        Returns:
            訂正内容のサマリー
        """
        if not self.enabled:
            return None

        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={self.api_key}"

            prompt = f"""以下のNHKニュース記事に訂正が含まれています。訂正内容を30文字以内で簡潔に要約してください。

検出キーワード: {', '.join(keywords)}

記事内容:
{text[:300]}

訂正内容（30文字以内）:"""

            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "temperature": 0.3,
                    "maxOutputTokens": 50
                }
            }

            headers = {
                "Content-Type": "application/json"
            }

            response = requests.post(url, json=payload, headers=headers, timeout=30)

            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    summary = result['candidates'][0]['content']['parts'][0]['text'].strip()
                    return summary

            return None

        except Exception as e:
            logger.error(f"訂正分析エラー: {e}")
            return None
