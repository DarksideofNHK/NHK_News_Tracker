#!/usr/bin/env python3
"""
NHK RSSスクレイピング - ハイブリッド版
requests（6ソース）+ undetected-chromedriver（東北のみ）
"""
import requests
import undetected_chromedriver as uc
from typing import Optional, Dict
import logging
import time
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class NhkRssScraperHybrid:
    """ハイブリッドスクレイパー（requests + Selenium）"""

    def __init__(self, selenium_profile_dir: str = None, use_remote_debug: bool = False, debug_port: int = 9222):
        """
        Args:
            selenium_profile_dir: Seleniumで使用するChromeプロファイル
            use_remote_debug: Remote Debugging使用（デフォルト: False - 専用プロファイル使用）
            debug_port: Remote Debuggingポート（デフォルト: 9222）
        """
        self.use_remote_debug = use_remote_debug
        self.debug_port = debug_port

        if not use_remote_debug:
            # 専用プロファイルを使用（デフォルト）
            if selenium_profile_dir is None:
                self.selenium_profile_dir = os.path.expanduser('~/nhk_scraper_chrome_profile')
            else:
                self.selenium_profile_dir = selenium_profile_dir
            self.profile_name = 'Default'

        # requests用ヘッダー
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
        }

    def _should_use_selenium(self, url: str) -> bool:
        """Seleniumとrequestsのどちらを使うか判定"""
        return 'news.web.nhk' in url

    def _fetch_with_requests(self, url: str) -> Optional[str]:
        """requestsで取得（www.nhk.or.jp用）"""
        try:
            logger.info(f"取得開始 (requests): {url}")
            response = requests.get(url, headers=self.headers, timeout=30)

            if response.status_code == 200:
                logger.info(f"取得成功 (requests): {len(response.text):,}文字")
                return response.text
            else:
                logger.error(f"HTTPエラー (requests): {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"エラー (requests): {type(e).__name__}: {e}")
            return None

    def _fetch_with_selenium(self, url: str) -> Optional[str]:
        """undetected-chromedriverで取得（news.web.nhk用）"""
        driver = None
        try:
            logger.info(f"取得開始 (undetected-chromedriver): {url}")

            # Chromeオプション
            chrome_options = uc.ChromeOptions()

            if self.use_remote_debug:
                # Remote Debugging使用（Chromeを起動したまま接続）
                chrome_options.add_experimental_option("debuggerAddress", f"localhost:{self.debug_port}")
                logger.info(f"Remote Debugging使用: localhost:{self.debug_port}")
            else:
                # プロファイル直接使用（Cookieコピー済み）
                chrome_options.add_argument(f'--user-data-dir={self.selenium_profile_dir}')
                chrome_options.add_argument('--profile-directory={self.profile_name}')
                chrome_options.add_argument('--headless=new')

            driver = uc.Chrome(options=chrome_options, use_subprocess=True)
            driver.get(url)
            time.sleep(3)  # ページ読み込み待機

            content = driver.page_source

            # JWT認証エラーチェック
            if 'JWT token' in content or ('"error"' in content and 'status": 401' in content):
                logger.error("JWT認証エラー - プロファイルの再セットアップが必要")
                logger.error("以下のコマンドを実行してください:")
                logger.error("  python setup_consent_auto.py")
                return None

            # XMLチェック（修正版：ChromeのXMLビューアーがHTMLでラップするため、<search>と<record>をチェック）
            if '<search' in content and '<record>' in content:
                record_count = content.count('<record>')
                logger.info(f"取得成功 (Selenium): {record_count}件の記事, {len(content):,}文字")
                return content
            else:
                logger.error("XMLが見つかりません（<search>または<record>タグが見つかりません）")
                return None

        except Exception as e:
            logger.error(f"エラー (Selenium): {type(e).__name__}: {e}")
            return None
        finally:
            if driver:
                driver.quit()

    def fetch(self, url: str) -> Optional[str]:
        """
        URL取得（自動判定: requests or Selenium）

        Args:
            url: RSS URL

        Returns:
            XMLコンテンツ（成功時）、None（失敗時）
        """
        if self._should_use_selenium(url):
            return self._fetch_with_selenium(url)
        else:
            return self._fetch_with_requests(url)

    def fetch_batch(self, urls: Dict[str, str]) -> Dict[str, Optional[str]]:
        """
        複数URL一括取得（最適化版）

        Args:
            urls: {'name': 'url', ...}

        Returns:
            {'name': 'content', ...}
        """
        results = {}

        # requestsで取得可能なURLをまず処理（高速）
        requests_urls = {name: url for name, url in urls.items()
                        if not self._should_use_selenium(url)}

        for name, url in requests_urls.items():
            logger.info(f"取得中 (requests): {name}")
            content = self._fetch_with_requests(url)
            results[name] = content
            time.sleep(0.5)  # 控えめな待機

        # Seleniumが必要なURLを処理（低速）
        selenium_urls = {name: url for name, url in urls.items()
                        if self._should_use_selenium(url)}

        if selenium_urls:
            # undetected-chromedriverを再利用（高速化）
            driver = None
            try:
                chrome_options = uc.ChromeOptions()

                if self.use_remote_debug:
                    # Remote Debugging使用
                    chrome_options.add_experimental_option("debuggerAddress", f"localhost:{self.debug_port}")
                else:
                    # プロファイル直接使用（Cookieコピー済み）
                    chrome_options.add_argument(f'--user-data-dir={self.selenium_profile_dir}')
                    chrome_options.add_argument(f'--profile-directory={self.profile_name}')
                    chrome_options.add_argument('--headless=new')

                driver = uc.Chrome(options=chrome_options, use_subprocess=True)

                for name, url in selenium_urls.items():
                    try:
                        logger.info(f"取得中 (Selenium): {name}")
                        driver.get(url)
                        time.sleep(3)

                        content = driver.page_source

                        # JWT認証エラーチェック
                        if 'JWT token' in content or ('"error"' in content and 'status": 401' in content):
                            logger.error(f"JWT認証エラー: {name}")
                            logger.error("プロファイルの再セットアップが必要です:")
                            logger.error("  python setup_consent_auto.py")
                            results[name] = None
                        elif '<search' in content and '<record>' in content:
                            record_count = content.count('<record>')
                            results[name] = content
                            logger.info(f"成功: {name} ({record_count}件の記事, {len(content):,}文字)")
                        else:
                            logger.error(f"XMLが見つかりません: {name}")
                            results[name] = None

                    except Exception as e:
                        logger.error(f"エラー: {name} - {e}")
                        results[name] = None

            finally:
                if driver:
                    driver.quit()

        return results
