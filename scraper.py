#!/usr/bin/env python3
"""
NHK RSSスクレイピング機能
"""
import requests
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class NhkRssScraper:
    """NHK RSSフィード取得クラス"""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }

    def fetch(self, url: str) -> Optional[str]:
        """
        NHK RSSフィードを取得

        Args:
            url: RSS URL

        Returns:
            XMLコンテンツ（成功時）、None（失敗時）
        """
        try:
            logger.info(f"取得開始: {url}")

            response = requests.get(
                url,
                headers=self.headers,
                timeout=self.timeout
            )

            response.raise_for_status()

            content = response.text
            logger.info(f"取得成功: {len(content):,}文字")

            return content

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTPエラー: {e.response.status_code} - {url}")
            return None
        except requests.exceptions.Timeout:
            logger.error(f"タイムアウト: {url}")
            return None
        except Exception as e:
            logger.error(f"エラー: {type(e).__name__}: {e}")
            return None
