#!/usr/bin/env python3
"""
既存のChromeプロファイルを検出
"""
import os
from pathlib import Path
import json

def find_chrome_profiles():
    """Chromeプロファイルを検出"""
    home = Path.home()

    # Mac Chrome profile directory
    chrome_base = home / "Library/Application Support/Google/Chrome"

    if not chrome_base.exists():
        print("❌ Chromeプロファイルが見つかりません")
        return None

    print(f"✅ Chromeベースディレクトリ: {chrome_base}\n")

    # プロファイル一覧
    profiles = []

    # Default プロファイル
    default_profile = chrome_base / "Default"
    if default_profile.exists():
        profiles.append(("Default", default_profile))

    # Profile 1, Profile 2, ... を検索
    for i in range(1, 20):
        profile_dir = chrome_base / f"Profile {i}"
        if profile_dir.exists():
            profiles.append((f"Profile {i}", profile_dir))

    if not profiles:
        print("❌ プロファイルが見つかりません")
        return None

    print(f"検出されたプロファイル数: {len(profiles)}\n")

    # 各プロファイルの情報を表示
    for name, path in profiles:
        print(f"{'='*60}")
        print(f"プロファイル名: {name}")
        print(f"パス: {path}")

        # Preferences ファイルから情報を取得
        prefs_file = path / "Preferences"
        if prefs_file.exists():
            try:
                with open(prefs_file, 'r', encoding='utf-8') as f:
                    prefs = json.load(f)

                # アカウント名
                account_info = prefs.get('account_info', [{}])[0]
                email = account_info.get('email', 'N/A')

                # プロファイル名
                profile_info = prefs.get('profile', {})
                profile_name = profile_info.get('name', 'N/A')

                print(f"アカウント: {email}")
                print(f"表示名: {profile_name}")
            except Exception as e:
                print(f"⚠️  設定ファイルの読み込みエラー: {e}")

        # Cookies ファイルの存在確認
        cookies_file = path / "Cookies"
        if cookies_file.exists():
            size = cookies_file.stat().st_size
            print(f"Cookies: あり ({size:,}バイト)")
        else:
            print(f"Cookies: なし")

        print()

    # 推奨プロファイル
    print("="*60)
    print("推奨設定:")
    print("="*60)

    # Defaultプロファイルを推奨
    if any(name == "Default" for name, _ in profiles):
        print("プロファイル名: Default")
        print(f"パス: {chrome_base}")
        print("\nこれがメインのChromeプロファイルです。")
        print("NHK東北ニュースにアクセスできているのは、このプロファイルだと思われます。")
    else:
        print(f"プロファイル名: {profiles[0][0]}")
        print(f"パス: {chrome_base}")

    return chrome_base

if __name__ == '__main__':
    print("="*60)
    print("Chromeプロファイル検出")
    print("="*60)
    print()

    chrome_base = find_chrome_profiles()

    if chrome_base:
        print("\n" + "="*60)
        print("次のステップ:")
        print("="*60)
        print("\n1. 以下のコマンドでテスト:")
        print(f"   python test_existing_profile.py")
        print("\n2. 注意: Chromeを完全に閉じてから実行してください")
        print("   （Chromeが起動中だとプロファイルがロックされます）")
