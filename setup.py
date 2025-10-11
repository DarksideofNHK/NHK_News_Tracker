#!/usr/bin/env python3
"""
NHK RSS差分追跡システム - セットアップスクリプト
環境に応じてLaunchAgentを設定
"""
import os
import shutil
from pathlib import Path

def setup():
    """セットアップメイン処理"""
    print("="*60)
    print("NHK RSS差分追跡システム - セットアップ")
    print("="*60)
    print()

    # プロジェクトルート
    project_root = Path(__file__).parent.absolute()

    # 1. .envファイルのチェック
    env_file = project_root / '.env'
    env_example = project_root / '.env.example'

    if not env_file.exists():
        print("⚠️  .envファイルが見つかりません。")
        print()

        if env_example.exists():
            print("📋 .env.exampleをコピーして.envを作成しますか？ (y/n): ", end='')
            response = input().lower()

            if response == 'y':
                shutil.copy(env_example, env_file)
                print(f"✅ .envファイルを作成しました: {env_file}")
                print()
                print("⚠️  .envファイルを編集して、GEMINI_API_KEYを設定してください。")
                print(f"   編集: {env_file}")
                print()
            else:
                print("❌ セットアップを中止します。")
                return False
        else:
            print("❌ .env.exampleが見つかりません。")
            return False
    else:
        print(f"✅ .envファイルが存在します: {env_file}")
        print()

    # 2. GEMINI_API_KEYのチェック
    from dotenv import load_dotenv
    load_dotenv(env_file)

    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key or api_key == 'your_gemini_api_key_here':
        print("⚠️  GEMINI_API_KEYが設定されていません。")
        print()
        print("APIキーの取得方法:")
        print("  1. https://aistudio.google.com/app/apikey にアクセス")
        print("  2. 「Create API Key」をクリック")
        print("  3. 生成されたAPIキーをコピー")
        print(f"  4. {env_file} を編集してAPIキーを設定")
        print()
        print("APIキーを入力しますか？ (y/n): ", end='')
        response = input().lower()

        if response == 'y':
            print("GEMINI_API_KEY: ", end='')
            new_key = input().strip()

            if new_key:
                # .envファイルを更新
                with open(env_file, 'r') as f:
                    lines = f.readlines()

                with open(env_file, 'w') as f:
                    for line in lines:
                        if line.startswith('GEMINI_API_KEY='):
                            f.write(f'GEMINI_API_KEY={new_key}\n')
                        else:
                            f.write(line)

                print("✅ APIキーを設定しました。")
                print()
            else:
                print("❌ APIキーが入力されませんでした。")
                return False
    else:
        print("✅ GEMINI_API_KEYが設定されています。")
        print()

    # 3. ディレクトリ作成
    print("📁 必要なディレクトリを作成中...")
    (project_root / 'data').mkdir(exist_ok=True)
    (project_root / 'logs').mkdir(exist_ok=True)
    (project_root / 'reports').mkdir(exist_ok=True)
    print("✅ ディレクトリを作成しました。")
    print()

    # 4. LaunchAgent設定（macOSのみ）
    if os.uname().sysname == 'Darwin':
        print("🍎 macOS LaunchAgent設定")
        print()
        print("自動実行を設定しますか？ (y/n): ", end='')
        response = input().lower()

        if response == 'y':
            setup_launchagent(project_root)
        else:
            print("ℹ️  手動実行のみで使用します。")
            print()
    else:
        print("ℹ️  macOS以外のOSでは、cronまたは他の方法で自動実行を設定してください。")
        print()

    # 5. 依存パッケージのインストール確認
    print("📦 依存パッケージのインストール")
    print()
    print("以下のコマンドで依存パッケージをインストールしてください:")
    print(f"  /usr/bin/python3 -m pip install --user -r {project_root}/requirements.txt")
    print()

    print("="*60)
    print("✅ セットアップ完了")
    print("="*60)
    print()
    print("次のステップ:")
    print(f"  1. 依存パッケージをインストール")
    print(f"  2. テスト実行: /usr/bin/python3 {project_root}/main_hybrid.py")
    print()

    return True

def setup_launchagent(project_root: Path):
    """LaunchAgent plistファイルを生成して配置"""

    home = Path.home()
    launchagents_dir = home / 'Library' / 'LaunchAgents'
    launchagents_dir.mkdir(parents=True, exist_ok=True)

    # 毎時実行用plist
    hourly_plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.nhk.rss-tracker</string>

    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>{project_root}/main_hybrid.py</string>
    </array>

    <key>StartInterval</key>
    <integer>3600</integer>

    <key>StandardOutPath</key>
    <string>{project_root}/logs/launchd.log</string>

    <key>StandardErrorPath</key>
    <string>{project_root}/logs/launchd.error.log</string>

    <key>WorkingDirectory</key>
    <string>{project_root}</string>

    <key>RunAtLoad</key>
    <true/>

    <key>SuccessfulExit</key>
    <false/>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
        <key>HOME</key>
        <string>{home}</string>
    </dict>
</dict>
</plist>
"""

    # 週次レポート用plist
    weekly_plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.nhk.rss-tracker.weekly</string>

    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>{project_root}/generate_weekly_report.py</string>
    </array>

    <key>StartCalendarInterval</key>
    <dict>
        <key>Weekday</key>
        <integer>1</integer>
        <key>Hour</key>
        <integer>0</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>

    <key>StandardOutPath</key>
    <string>{project_root}/logs/weekly.log</string>

    <key>StandardErrorPath</key>
    <string>{project_root}/logs/weekly.error.log</string>

    <key>WorkingDirectory</key>
    <string>{project_root}</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
        <key>HOME</key>
        <string>{home}</string>
    </dict>
</dict>
</plist>
"""

    hourly_file = launchagents_dir / 'com.nhk.rss-tracker.plist'
    weekly_file = launchagents_dir / 'com.nhk.rss-tracker.weekly.plist'

    # 既存のLaunchAgentをアンロード
    os.system(f'launchctl unload {hourly_file} 2>/dev/null')
    os.system(f'launchctl unload {weekly_file} 2>/dev/null')

    # plistファイルを書き込み
    with open(hourly_file, 'w') as f:
        f.write(hourly_plist)

    with open(weekly_file, 'w') as f:
        f.write(weekly_plist)

    print(f"✅ LaunchAgentファイルを作成しました:")
    print(f"   - {hourly_file}")
    print(f"   - {weekly_file}")
    print()

    # LaunchAgentをロード
    os.system(f'launchctl load {hourly_file}')
    os.system(f'launchctl load {weekly_file}')

    print("✅ LaunchAgentを起動しました。")
    print()
    print("確認コマンド:")
    print("  launchctl list | grep nhk")
    print()

if __name__ == '__main__':
    try:
        setup()
    except KeyboardInterrupt:
        print("\n\n❌ セットアップを中止しました。")
    except Exception as e:
        print(f"\n\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
