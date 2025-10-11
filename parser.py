#!/usr/bin/env python3
"""
NHK XML解析機能
"""
from lxml import etree
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class NhkXmlParser:
    """NHK独自形式のXMLパーサー"""

    def parse(self, xml_content: str) -> List[Dict[str, str]]:
        """
        NHK XMLをパース

        Args:
            xml_content: XMLコンテンツ

        Returns:
            記事リスト
        """
        try:
            # BOM除去
            if xml_content.startswith('\ufeff'):
                xml_content = xml_content[1:]

            # XML解析
            root = etree.fromstring(xml_content.encode('utf-8'))

            articles = []

            # <record>タグをすべて取得
            for record in root.findall('.//record'):
                article = {
                    'title': self._get_text(record, 'title'),
                    'link': self._get_text(record, 'link'),
                    'pubDate': self._get_text(record, 'pubDate'),
                    'description': self._get_text(record, 'description'),
                }

                # 必須フィールドチェック
                if article['title'] and article['link']:
                    articles.append(article)

            logger.info(f"解析成功: {len(articles)}件の記事")
            return articles

        except etree.XMLSyntaxError as e:
            logger.error(f"XMLパースエラー: {e}")
            return []
        except Exception as e:
            logger.error(f"エラー: {type(e).__name__}: {e}")
            return []

    def _get_text(self, element, tag: str) -> str:
        """XML要素からテキストを安全に取得"""
        node = element.find(tag)
        if node is not None and node.text:
            return node.text.strip()
        return ''
