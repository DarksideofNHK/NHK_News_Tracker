# NHK記事追跡システム - 自動デプロイ設定

## 📋 概要

4時間ごとに自動的に以下の処理を実行します：

1. 最新のRSS記事を収集
2. 変更・訂正記事を検出
3. HTMLページを生成（ポータル、変更履歴、アーカイブ）
4. Netlifyに自動デプロイ

## ⏰ 実行スケジュール

- **実行間隔**: 4時間ごと（14,400秒）
- **初回実行**: システム起動時に即座に実行
- **以降**: 前回実行から4時間後

## 📁 ファイル構成

```
rss-diff-analyzer-python/
├── run_and_deploy.sh                    # 実行スクリプト
├── logs/                                # ログディレクトリ
│   ├── auto_deploy_YYYYMMDD_HHMMSS.log # 各実行のログ
│   ├── launchd_stdout.log              # 標準出力ログ
│   └── launchd_stderr.log              # エラーログ
└── AUTO_DEPLOY_README.md               # このファイル
```

**launchdの設定ファイル:**
```
~/Library/LaunchAgents/com.nhk.tracker.autodeploy.plist
```

## 🔧 管理コマンド

### ステータス確認
```bash
launchctl list | grep com.nhk.tracker.autodeploy
```

### 手動で即座に実行
```bash
/Users/trudibussi/projects/gemini-cli/rss-diff-analyzer-python/run_and_deploy.sh
```

### 自動実行を停止
```bash
launchctl unload ~/Library/LaunchAgents/com.nhk.tracker.autodeploy.plist
```

### 自動実行を再開
```bash
launchctl load ~/Library/LaunchAgents/com.nhk.tracker.autodeploy.plist
```

### 設定をリロード（設定変更後）
```bash
launchctl unload ~/Library/LaunchAgents/com.nhk.tracker.autodeploy.plist
launchctl load ~/Library/LaunchAgents/com.nhk.tracker.autodeploy.plist
```

## 📊 ログの確認

### 最新の実行ログを表示
```bash
ls -t logs/auto_deploy_*.log | head -1 | xargs cat
```

### リアルタイムでログを監視
```bash
tail -f logs/launchd_stdout.log
```

### エラーログを確認
```bash
cat logs/launchd_stderr.log
```

### 最新10件の実行履歴
```bash
ls -lt logs/auto_deploy_*.log | head -10
```

## 🔔 通知

実行結果はログファイルに記録されます：
- ✅ 成功: 各ステップで「✅」マークが表示
- ❌ エラー: 各ステップで「❌」マークが表示
- デプロイURL: https://nhk-news-tracker.netlify.app

## 🧹 メンテナンス

- **古いログの自動削除**: 30日以上前のログファイルは自動削除されます
- **手動削除**: `rm logs/auto_deploy_*.log` で全ログを削除可能

## ⚠️ トラブルシューティング

### 実行されない場合

1. ジョブが登録されているか確認
   ```bash
   launchctl list | grep com.nhk.tracker.autodeploy
   ```

2. plistファイルの構文エラーチェック
   ```bash
   plutil -lint ~/Library/LaunchAgents/com.nhk.tracker.autodeploy.plist
   ```

3. 実行権限の確認
   ```bash
   ls -l run_and_deploy.sh
   # -rwxr-xr-x であることを確認
   ```

4. エラーログを確認
   ```bash
   cat logs/launchd_stderr.log
   ```

### デプロイが失敗する場合

1. Netlify認証状態を確認
   ```bash
   netlify status
   ```

2. 手動でデプロイしてエラーを確認
   ```bash
   netlify deploy --prod --dir=reports
   ```

## 🛠️ カスタマイズ

### 実行間隔を変更する場合

`~/Library/LaunchAgents/com.nhk.tracker.autodeploy.plist`の以下の値を変更：

```xml
<key>StartInterval</key>
<integer>14400</integer>  <!-- 秒数を変更 -->
```

**例:**
- 2時間ごと: 7200
- 6時間ごと: 21600
- 12時間ごと: 43200

変更後は設定をリロード：
```bash
launchctl unload ~/Library/LaunchAgents/com.nhk.tracker.autodeploy.plist
launchctl load ~/Library/LaunchAgents/com.nhk.tracker.autodeploy.plist
```

### 特定の時刻に実行する場合

`StartInterval`を削除し、`StartCalendarInterval`を追加：

```xml
<key>StartCalendarInterval</key>
<array>
    <dict>
        <key>Hour</key>
        <integer>0</integer>  <!-- 0時 -->
        <key>Minute</key>
        <integer>0</integer>  <!-- 0分 -->
    </dict>
    <dict>
        <key>Hour</key>
        <integer>6</integer>  <!-- 6時 -->
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <dict>
        <key>Hour</key>
        <integer>12</integer> <!-- 12時 -->
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <dict>
        <key>Hour</key>
        <integer>18</integer> <!-- 18時 -->
        <key>Minute</key>
        <integer>0</integer>
    </dict>
</array>
```

## 📈 システム情報

- **設定日**: 2025年10月13日
- **実行環境**: macOS launchd
- **Python**: /usr/bin/python3
- **デプロイ先**: https://nhk-news-tracker.netlify.app

## 📝 注意事項

1. **Mac起動中のみ実行**: Macがスリープまたはシャットダウンしている場合は実行されません
2. **ネットワーク必須**: RSS取得とNetlifyデプロイにはインターネット接続が必要です
3. **Python環境**: システムのPython3を使用（仮想環境ではありません）
4. **Netlify認証**: 初回ログイン後、トークンが保存されているため追加認証は不要です

---

**作成日**: 2025年10月13日
**最終更新**: 2025年10月13日
