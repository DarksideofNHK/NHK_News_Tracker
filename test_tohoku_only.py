#!/usr/bin/env python3
"""
NHK東北ニュース単体テスト
"""
import undetected_chromedriver as uc
import time
import os
from lxml import etree

def test_tohoku():
    """NHK東北ニュースのテスト"""
    print("="*60)
    print("NHK東北ニュース 取得テスト")
    print("="*60)

    profile_dir = os.path.expanduser('~/nhk_scraper_chrome_profile')

    print(f"\n専用プロファイル: {profile_dir}")
    print("Chrome起動中（ヘッドレスモード）...\n")

    try:
        # undetected-chromedriver で起動
        options = uc.ChromeOptions()
        options.add_argument(f'--user-data-dir={profile_dir}')
        options.add_argument('--profile-directory=Default')
        options.add_argument('--headless=new')

        driver = uc.Chrome(options=options, use_subprocess=True)

        # NHK東北にアクセス
        url = 'https://news.web.nhk/tohoku-news/news_all_search.xml'

        print(f"アクセス中: {url}\n")
        driver.get(url)
        time.sleep(5)

        content = driver.page_source

        # JWTエラーチェック
        if 'JWT token' in content or '"error"' in content:
            print("❌ JWT認証エラー")
            print("\n先頭1000文字:")
            print("-" * 60)
            print(content[:1000])
            print("-" * 60)
            print("\n対処:")
            print("1. 通常のChromeで https://news.web.nhk/ にアクセス")
            print("2. 同意ダイアログをOK")
            print("3. python3 copy_cookie_files.py を実行")
            driver.quit()
            return False

        # XMLコンテンツの検出
        if '<search' in content and '<record>' in content:
            record_count = content.count('<record>')

            print(f"✅ 成功！")
            print(f"\nコンテンツサイズ: {len(content):,}文字")
            print(f"記事数: {record_count}件")

            # XMLをパース
            try:
                # HTMLラッパーから<search>タグを抽出
                search_start = content.find('<search')
                if search_start > 0:
                    # </search>の終わりまで取得
                    search_end = content.find('</search>', search_start) + len('</search>')
                    xml_content = content[search_start:search_end]
                else:
                    xml_content = content

                root = etree.fromstring(xml_content.encode('utf-8'))

                print("\n" + "─"*60)
                print("最初の5件の記事:")
                print("─"*60)

                records = root.findall('.//record')[:5]
                for i, record in enumerate(records, 1):
                    title = record.find('title')
                    pub_date = record.find('pubDate')

                    if title is not None:
                        print(f"\n{i}. {title.text}")
                        if pub_date is not None:
                            print(f"   公開日時: {pub_date.text}")

                print("\n" + "─"*60)

            except Exception as e:
                print(f"\nXML解析エラー: {e}")

            driver.quit()
            return True

        else:
            print("⚠️  不明な応答")
            print(f"\nコンテンツサイズ: {len(content):,}文字")
            print("\n先頭1000文字:")
            print("-" * 60)
            print(content[:1000])
            print("-" * 60)
            driver.quit()
            return False

    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("\n" + "#"*60)
    print("# NHK東北ニュース 単体テスト")
    print("#"*60 + "\n")

    success = test_tohoku()

    print("\n" + "="*60)
    if success:
        print("✅ テスト成功！")
        print("\nNHK東北ニュースの自動取得が可能です。")
        print("\n次のステップ:")
        print("1. python3 test_hybrid.py で7ソース全体をテスト")
        print("2. python3 main_hybrid.py で本番実行")
        print("3. cron設定で1時間ごとの自動実行")
    else:
        print("❌ テスト失敗")
        print("\n対処:")
        print("1. 通常のChromeで https://news.web.nhk/ にアクセス")
        print("2. 同意ダイアログをOK")
        print("3. python3 copy_cookie_files.py を実行")
        print("4. 再度このテストを実行")
    print("="*60)
