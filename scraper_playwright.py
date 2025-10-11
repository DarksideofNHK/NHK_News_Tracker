#!/usr/bin/env python3
"""
NHK RSSスクレイピング - Playwright版
"""
from playwright.sync_api import sync_playwright
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class NhkRssScraperPlaywright:
    """Playwrightを使ったNHK RSSフィード取得"""

    def __init__(self, headless: bool = True, timeout: int = 30000):
        """
        Args:
            headless: ヘッドレスモード（True推奨）
            timeout: タイムアウト（ミリ秒）
        """
        self.headless = headless
        self.timeout = timeout

    def fetch(self, url: str) -> Optional[str]:
        """
        NHK RSSフィードを取得

        Args:
            url: RSS URL

        Returns:
            XMLコンテンツ（成功時）、None（失敗時）
        """
        try:
            logger.info(f"取得開始 (Playwright): {url}")

            with sync_playwright() as p:
                # Chromiumブラウザ起動
                browser = p.chromium.launch(headless=self.headless)

                # コンテキスト作成（User-Agent等を設定）
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    viewport={'width': 1920, 'height': 1080},
                    locale='ja-JP',
                )

                # 新しいページ
                page = context.new_page()

                # URLにアクセス
                response = page.goto(url, wait_until='networkidle', timeout=self.timeout)

                if response is None or response.status != 200:
                    logger.error(f"HTTPエラー: {response.status if response else 'None'}")
                    browser.close()
                    return None

                # コンテンツ取得
                content = page.content()

                browser.close()

                logger.info(f"取得成功 (Playwright): {len(content):,}文字")
                return content

        except Exception as e:
            logger.error(f"エラー (Playwright): {type(e).__name__}: {e}")
            return None

    def fetch_batch(self, urls: list) -> dict:
        """
        複数URLを一括取得（ブラウザ再利用で高速化）

        Args:
            urls: URL辞書 {'name': 'url', ...}

        Returns:
            結果辞書 {'name': 'content', ...}
        """
        results = {}

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=self.headless)

                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    viewport={'width': 1920, 'height': 1080},
                    locale='ja-JP',
                )

                for name, url in urls.items():
                    try:
                        logger.info(f"取得中 (Playwright): {name}")

                        page = context.new_page()
                        response = page.goto(url, wait_until='networkidle', timeout=self.timeout)

                        if response and response.status == 200:
                            content = page.content()
                            results[name] = content
                            logger.info(f"成功: {name} ({len(content):,}文字)")
                        else:
                            logger.error(f"失敗: {name} (HTTP {response.status if response else 'None'})")
                            results[name] = None

                        page.close()

                    except Exception as e:
                        logger.error(f"エラー: {name} - {e}")
                        results[name] = None

                browser.close()

        except Exception as e:
            logger.error(f"致命的エラー (Playwright): {e}")

        return results
