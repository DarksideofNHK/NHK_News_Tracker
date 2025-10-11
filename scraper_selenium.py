#!/usr/bin/env python3
"""
NHK RSSスクレイピング - Selenium版（Chromeプロファイル使用）
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from typing import Optional
import logging
import time
import os

logger = logging.getLogger(__name__)

class NhkRssScraperSelenium:
    """Seleniumを使ったNHK RSSフィード取得（プロファイル使用）"""

    def __init__(self, headless: bool = True, profile_dir: str = None):
        """
        Args:
            headless: ヘッドレスモード（True推奨）
            profile_dir: Chromeプロファイルディレクトリ
        """
        self.headless = headless

        if profile_dir is None:
            # デフォルト: 専用プロファイル
            self.profile_dir = os.path.expanduser('~/Library/Application Support/Google/Chrome_NHK_Scraper')
        else:
            self.profile_dir = profile_dir

        self.driver = None

    def _create_driver(self):
        """ドライバー作成"""
        chrome_options = Options()

        # プロファイル設定
        chrome_options.add_argument(f'user-data-dir={self.profile_dir}')
        chrome_options.add_argument('profile-directory=Default')

        # その他のオプション
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')

        if self.headless:
            chrome_options.add_argument('--headless')

        # ログ抑制
        chrome_options.add_argument('--log-level=3')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

        return webdriver.Chrome(options=chrome_options)

    def fetch(self, url: str) -> Optional[str]:
        """
        NHK RSSフィードを取得

        Args:
            url: RSS URL

        Returns:
            XMLコンテンツ（成功時）、None（失敗時）
        """
        try:
            logger.info(f"取得開始 (Selenium): {url}")

            # ドライバー作成（毎回新規）
            driver = self._create_driver()

            try:
                driver.get(url)
                time.sleep(2)  # ページ読み込み待機

                content = driver.page_source

                # JWT認証エラーチェック
                if 'JWT token' in content or ('"error"' in content and 'status": 401' in content):
                    logger.error("JWT認証エラー - プロファイルの再設定が必要")
                    return None

                # XMLチェック
                if '<?xml' in content or '<search' in content:
                    logger.info(f"取得成功 (Selenium): {len(content):,}文字")
                    return content
                else:
                    logger.error("XMLが見つかりません")
                    return None

            finally:
                driver.quit()

        except Exception as e:
            logger.error(f"エラー (Selenium): {type(e).__name__}: {e}")
            return None

    def fetch_batch(self, urls: dict) -> dict:
        """
        複数URLを一括取得（ブラウザ再利用で高速化）

        Args:
            urls: URL辞書 {'name': 'url', ...}

        Returns:
            結果辞書 {'name': 'content', ...}
        """
        results = {}

        # ドライバー作成（再利用）
        driver = self._create_driver()

        try:
            for name, url in urls.items():
                try:
                    logger.info(f"取得中 (Selenium): {name}")

                    driver.get(url)
                    time.sleep(2)

                    content = driver.page_source

                    # JWT認証エラーチェック
                    if 'JWT token' in content or ('"error"' in content and 'status": 401' in content):
                        logger.error(f"JWT認証エラー: {name}")
                        results[name] = None
                        continue

                    # XMLチェック
                    if '<?xml' in content or '<search' in content:
                        results[name] = content
                        logger.info(f"成功: {name} ({len(content):,}文字)")
                    else:
                        logger.error(f"XMLが見つかりません: {name}")
                        results[name] = None

                except Exception as e:
                    logger.error(f"エラー: {name} - {e}")
                    results[name] = None

        finally:
            driver.quit()

        return results
