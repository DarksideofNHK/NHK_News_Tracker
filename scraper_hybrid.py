#!/usr/bin/env python3
"""
NHK RSSスクレイピング - ハイブリッド版
requests（6ソース）+ undetected-chromedriver（東北のみ）
JWT認証エラー自動リカバリー対応
"""
import requests
import undetected_chromedriver as uc
from typing import Optional, Dict
import logging
import time
import os
from pathlib import Path
from setup_consent_auto import setup_with_auto_consent
from notifier import MacNotifier

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
                logger.error("JWT認証エラー検出 - 自動リカバリーを開始します...")
                MacNotifier.notify_error("JWT認証エラー", "NHK東北でJWT認証エラー - 自動リカバリー中...")

                # driverを一旦閉じる
                driver.quit()
                driver = None

                # Chromeプロセスが完全に終了するまで待機
                logger.info("Chromeプロセスの終了を待機中...")
                time.sleep(5)

                # 自動再セットアップ
                logger.info("自動再セットアップを実行中...")
                success, profile_dir = setup_with_auto_consent(auto_mode=True)

                if success:
                    logger.info("JWT認証の自動リカバリーが成功 - データ取得を再試行します")
                    MacNotifier.send("JWT認証リカバリー", "再認証成功 - データ取得を再試行中...")

                    # 新しいdriverで再試行
                    chrome_options = uc.ChromeOptions()
                    if self.use_remote_debug:
                        chrome_options.add_experimental_option("debuggerAddress", f"localhost:{self.debug_port}")
                    else:
                        chrome_options.add_argument(f'--user-data-dir={self.selenium_profile_dir}')
                        chrome_options.add_argument(f'--profile-directory={self.profile_name}')
                        chrome_options.add_argument('--headless=new')

                    driver = uc.Chrome(options=chrome_options, use_subprocess=True)
                    driver.get(url)
                    time.sleep(3)
                    content = driver.page_source

                    # 再チェック
                    if '<search' in content and '<record>' in content:
                        record_count = content.count('<record>')
                        logger.info(f"再試行成功: {record_count}件の記事を取得")
                        MacNotifier.send("JWT認証リカバリー成功", f"{record_count}件の記事を取得しました")
                        return content
                    else:
                        logger.error("再試行失敗 - XMLが見つかりません")
                        MacNotifier.notify_error("JWT認証リカバリー失敗", "再試行後もデータ取得に失敗")
                        return None
                else:
                    logger.error("JWT認証の自動リカバリーが失敗しました")
                    MacNotifier.notify_error("JWT認証リカバリー失敗", "自動再認証に失敗しました")
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
                            logger.error(f"JWT認証エラー検出: {name} - 自動リカバリーを開始します...")
                            MacNotifier.notify_error("JWT認証エラー", f"{name}でJWT認証エラー - 自動リカバリー中...")

                            # driverを一旦閉じる
                            driver.quit()
                            driver = None

                            # Chromeプロセスが完全に終了するまで待機
                            logger.info("Chromeプロセスの終了を待機中...")
                            time.sleep(5)

                            # 自動再セットアップ
                            logger.info("自動再セットアップを実行中...")
                            success, profile_dir = setup_with_auto_consent(auto_mode=True)

                            if success:
                                logger.info("JWT認証の自動リカバリーが成功 - データ取得を再試行します")
                                MacNotifier.send("JWT認証リカバリー", "再認証成功 - データ取得を再試行中...")

                                # 新しいdriverで再開
                                chrome_options = uc.ChromeOptions()
                                if self.use_remote_debug:
                                    chrome_options.add_experimental_option("debuggerAddress", f"localhost:{self.debug_port}")
                                else:
                                    chrome_options.add_argument(f'--user-data-dir={self.selenium_profile_dir}')
                                    chrome_options.add_argument(f'--profile-directory={self.profile_name}')
                                    chrome_options.add_argument('--headless=new')

                                driver = uc.Chrome(options=chrome_options, use_subprocess=True)

                                # 再試行
                                driver.get(url)
                                time.sleep(3)
                                content = driver.page_source

                                # 再チェック
                                if '<search' in content and '<record>' in content:
                                    record_count = content.count('<record>')
                                    results[name] = content
                                    logger.info(f"再試行成功: {name} ({record_count}件の記事)")
                                    MacNotifier.send("JWT認証リカバリー成功", f"{name}: {record_count}件の記事を取得")
                                else:
                                    logger.error(f"再試行失敗: {name} - XMLが見つかりません")
                                    MacNotifier.notify_error("JWT認証リカバリー失敗", f"{name}の再試行に失敗")
                                    results[name] = None
                            else:
                                logger.error(f"JWT認証の自動リカバリーが失敗: {name}")
                                MacNotifier.notify_error("JWT認証リカバリー失敗", f"{name}の自動再認証に失敗")
                                results[name] = None
                                # driverが閉じているので、ここで処理を中断
                                break
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

    def search_nhk_one(self, query: str = "失礼しました", driver=None) -> list:
        """
        NHK ONE検索で訂正記事を検索し、記事データを取得

        Args:
            query: 検索キーワード（デフォルト: 失礼しました）
            driver: 既存のSeleniumドライバー（Noneの場合は新規作成）

        Returns:
            記事リスト [{'source': 'NHK ONE検索', 'link': 'url', 'title': '', 'description': '', 'pubDate': ''}, ...]
        """
        from urllib.parse import quote
        import re
        from datetime import datetime

        # URLエンコード
        encoded_query = quote(query)
        search_url = f"https://www.web.nhk/search?query={encoded_query}&modeOfItem=news&period=all&hasVideo=false"

        logger.info(f"NHK ONE検索開始: {query}")
        logger.info(f"検索URL: {search_url}")

        created_driver = False
        if driver is None:
            created_driver = True
            # 新しいdriverを作成
            chrome_options = uc.ChromeOptions()
            if self.use_remote_debug:
                chrome_options.add_experimental_option("debuggerAddress", f"localhost:{self.debug_port}")
            else:
                chrome_options.add_argument(f'--user-data-dir={self.selenium_profile_dir}')
                chrome_options.add_argument(f'--profile-directory={self.profile_name}')
                chrome_options.add_argument('--headless=new')

            driver = uc.Chrome(options=chrome_options, use_subprocess=True)

        articles = []

        try:
            # 検索ページにアクセス
            driver.get(search_url)
            time.sleep(5)  # ページ読み込み待機

            # デバッグ: ページタイトルとURL確認
            logger.info(f"ページタイトル: {driver.title}")
            logger.info(f"現在のURL: {driver.current_url}")

            # デバッグ: ページのHTMLを一部出力
            page_source_preview = driver.page_source[:2000]
            logger.info(f"ページHTML（最初の2000文字）: {page_source_preview}")

            # デバッグ: スクリーンショット保存
            try:
                screenshot_path = f"/tmp/nhk_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                driver.save_screenshot(screenshot_path)
                logger.info(f"スクリーンショット保存: {screenshot_path}")
            except Exception as e:
                logger.warning(f"スクリーンショット保存失敗: {e}")

            # 検索結果から記事URLを抽出
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC

            # 検索結果のリンクを取得
            try:
                # 検索結果の読み込みを待機（JavaScriptで動的に読み込まれるため長めに待機）
                logger.info("検索結果の読み込み待機中...")
                time.sleep(8)  # より長く待機

                # Next.jsのページが完全にレンダリングされるまで待機
                try:
                    # __NEXT_DATA__スクリプトタグの存在を確認
                    WebDriverWait(driver, 10).until(
                        lambda d: d.execute_script("return typeof window.__NEXT_DATA__ !== 'undefined'")
                    )
                    logger.info("Next.js データが読み込まれました")
                except Exception as e:
                    logger.warning(f"Next.js データの待機タイムアウト: {e}")

                # ページをスクロールして遅延読み込みコンテンツをトリガー
                logger.info("ページをスクロールして検索結果を読み込み中...")
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(2)

                # 再度スクリーンショットを保存（スクロール後）
                try:
                    screenshot_path = f"/tmp/nhk_search_scrolled_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    driver.save_screenshot(screenshot_path)
                    logger.info(f"スクロール後のスクリーンショット: {screenshot_path}")
                except:
                    pass

                # HTMLを保存して構造を確認
                try:
                    html_path = f"/tmp/nhk_search_page_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                    with open(html_path, 'w', encoding='utf-8') as f:
                        f.write(driver.page_source)
                    logger.info(f"HTMLページを保存: {html_path}")
                except Exception as e:
                    logger.warning(f"HTML保存失敗: {e}")

                # Next.jsの __NEXT_DATA__ からデータを抽出
                try:
                    next_data = driver.execute_script("return window.__NEXT_DATA__;")
                    if next_data:
                        logger.info("__NEXT_DATA__ からデータを抽出中...")
                        import json
                        logger.debug(f"Next.js Data keys: {list(next_data.keys())}")

                        # JSON構造を探索して記事URLを抽出
                        def extract_urls_from_json(obj, urls=None):
                            if urls is None:
                                urls = []
                            if isinstance(obj, dict):
                                # URLを含むキーを探索
                                for key, value in obj.items():
                                    if key in ['url', 'link', 'href', 'path'] and isinstance(value, str):
                                        if '/news/' in value and 'nhk' in value.lower():
                                            if not value.startswith('http'):
                                                value = 'https://www.nhk.or.jp' + value if value.startswith('/') else value
                                            urls.append(value)
                                    else:
                                        extract_urls_from_json(value, urls)
                            elif isinstance(obj, list):
                                for item in obj:
                                    extract_urls_from_json(item, urls)
                            return urls

                        json_urls = extract_urls_from_json(next_data)
                        if json_urls:
                            logger.info(f"__NEXT_DATA__ から {len(json_urls)}件のURLを抽出")
                            for url in json_urls[:10]:
                                logger.debug(f"  JSON URL: {url}")
                except Exception as e:
                    logger.warning(f"__NEXT_DATA__ の抽出エラー: {e}")

                # 全てのリンクを取得してデバッグ
                all_links = driver.find_elements(By.CSS_SELECTOR, "a")
                logger.info(f"ページ内の全リンク数: {len(all_links)}件")

                # NHK ONE検索結果の記事URLパターン: news.web.nhk/newsweb/na/nb-{article_id}
                news_links = []
                for link in all_links:
                    href = link.get_attribute('href')
                    if href and '/newsweb/na/nb-' in href:
                        news_links.append(href)

                logger.info(f"検索結果記事リンク: {len(news_links)}件")

                # デバッグ: 見つかった記事リンクを全て表示
                if news_links:
                    logger.info(f"記事リンク一覧:")
                    for i, link in enumerate(news_links, 1):
                        logger.info(f"  {i}. {link}")

                # 重複を除外して記事URLリストを作成
                article_urls = list(set(news_links))

                logger.info(f"検索結果: {len(article_urls)}件の記事URLを抽出")

                # デバッグ: 最初の5件のURLを表示
                if article_urls:
                    logger.info(f"記事URL例（最初の5件）:")
                    for i, url in enumerate(article_urls[:5], 1):
                        logger.info(f"  {i}. {url}")

                # 各記事にアクセスして内容を取得
                for i, url in enumerate(article_urls[:20], 1):  # 最大20件まで
                    try:
                        logger.info(f"記事取得中 ({i}/{min(len(article_urls), 20)}): {url}")
                        driver.get(url)
                        time.sleep(3)  # より長く待機

                        # 最初の記事のHTMLを保存してデバッグ
                        if i == 1:
                            try:
                                article_html_path = f"/tmp/nhk_article_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                                with open(article_html_path, 'w', encoding='utf-8') as f:
                                    f.write(driver.page_source)
                                logger.info(f"記事HTMLを保存: {article_html_path}")
                            except:
                                pass

                        # タイトル取得
                        title = ""
                        try:
                            title_elem = driver.find_element(By.CSS_SELECTOR, "h1, .article-title, .news-title")
                            title = title_elem.text.strip()
                            logger.debug(f"タイトル: {title[:100]}")
                        except Exception as e:
                            logger.warning(f"タイトル取得失敗: {url} - {e}")

                        # 本文取得
                        description = ""
                        try:
                            # 複数のセレクタを試行（NHK ONE記事の構造に合わせて）
                            selectors = [
                                "p._1i1d7sh2",  # NHK ONE記事の本文
                                ".article-body",
                                ".news-body",
                                ".content-body",
                                "article p",
                                ".article-content"
                            ]
                            for selector in selectors:
                                try:
                                    body_elems = driver.find_elements(By.CSS_SELECTOR, selector)
                                    if body_elems:
                                        description = "\n".join([elem.text.strip() for elem in body_elems if elem.text.strip()])
                                        if description:
                                            logger.debug(f"本文取得成功 (セレクタ: {selector}): {len(description)}文字")
                                            logger.debug(f"本文プレビュー: {description[:200]}...")
                                            break
                                except:
                                    continue

                            if not description:
                                logger.warning(f"本文取得失敗 (全セレクタで失敗): {url}")
                        except Exception as e:
                            logger.warning(f"本文取得エラー: {url} - {e}")

                        # 公開日時取得
                        pub_date = ""
                        try:
                            date_elem = driver.find_element(By.CSS_SELECTOR, "time, .date, .publish-date")
                            pub_date = date_elem.get_attribute('datetime') or date_elem.text.strip()
                        except:
                            # 日時が取得できない場合は現在時刻
                            pub_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                        # デバッグ情報を出力
                        logger.info(f"  ✓ タイトル: {'あり' if title else 'なし'} ({len(title)}文字)")
                        logger.info(f"  ✓ 本文: {'あり' if description else 'なし'} ({len(description)}文字)")

                        if title and description:
                            # 「失礼しました」または訂正キーワードが含まれているか確認
                            has_query = query in title or query in description
                            has_correction = '※' in description or '※' in title
                            logger.info(f"  ✓ '{query}'含む: {has_query}, '※'含む: {has_correction}")

                            if has_query or has_correction:
                                article = {
                                    'source': 'NHK ONE検索',
                                    'link': url,
                                    'title': title,
                                    'description': description,
                                    'pubDate': pub_date
                                }
                                articles.append(article)
                                logger.info(f"✅ 訂正記事を発見: {title[:50]}...")
                            else:
                                logger.info(f"  ℹ️  訂正キーワードなし: {title[:50]}...")
                        else:
                            logger.warning(f"  ⚠️  記事データ不完全: title={'あり' if title else 'なし'}, desc={'あり' if description else 'なし'}")

                    except Exception as e:
                        logger.error(f"記事取得エラー: {url} - {e}")
                        continue

                logger.info(f"NHK ONE検索完了: {len(articles)}件の訂正記事を取得")

            except Exception as e:
                logger.error(f"検索結果の抽出エラー: {e}")

        except Exception as e:
            logger.error(f"NHK ONE検索エラー: {e}")

        finally:
            if created_driver and driver:
                driver.quit()

        return articles
