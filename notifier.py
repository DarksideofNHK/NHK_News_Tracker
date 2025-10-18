#!/usr/bin/env python3
"""
macOS通知センター連携
"""
import subprocess
import logging

logger = logging.getLogger(__name__)


class MacNotifier:
    """macOS通知センター"""

    @staticmethod
    def send(title: str, message: str, sound: str = None):
        """
        macOS通知センターに通知を送信

        Args:
            title: 通知のタイトル
            message: 通知のメッセージ
            sound: サウンド名（'Basso', 'Blow', 'Bottle', 'Frog', 'Funk', 'Glass', 'Hero', 'Morse', 'Ping', 'Pop', 'Purr', 'Sosumi', 'Submarine', 'Tink'）
        """
        try:
            # AppleScriptで通知を送信
            if sound:
                script = f'display notification "{message}" with title "{title}" sound name "{sound}"'
            else:
                script = f'display notification "{message}" with title "{title}"'

            subprocess.run(
                ['osascript', '-e', script],
                check=True,
                capture_output=True,
                text=True
            )
            logger.info(f"通知送信成功: {title} - {message}")

        except subprocess.CalledProcessError as e:
            logger.error(f"通知送信失敗: {e.stderr}")
        except Exception as e:
            logger.error(f"通知エラー: {e}")

    @classmethod
    def notify_completion(cls, new_count: int, updated_count: int, total_count: int, failed_sources: list = None):
        """
        実行完了通知

        Args:
            new_count: 新規記事数
            updated_count: 更新記事数
            total_count: 総記事数
            failed_sources: 失敗したソースのリスト
        """
        # 変更がある場合のみ通知
        if new_count > 0 or updated_count > 0:
            parts = []
            if new_count > 0:
                parts.append(f"新規{new_count}件")
            if updated_count > 0:
                parts.append(f"更新{updated_count}件")

            message = f"{', '.join(parts)}を検出（総{total_count}件）"
            cls.send("NHK追跡システム", message)

        # エラーがある場合は別途通知
        if failed_sources:
            source_names = ', '.join(failed_sources)
            cls.send(
                "NHK追跡システム - エラー",
                f"取得失敗: {source_names}",
                sound="Basso"
            )

    @classmethod
    def notify_error(cls, error_type: str, details: str):
        """
        エラー通知

        Args:
            error_type: エラーの種類
            details: エラーの詳細
        """
        cls.send(
            f"NHK追跡システム - {error_type}",
            details,
            sound="Basso"
        )

    @classmethod
    def notify_correction_detected(cls, count: int, sources: list):
        """
        訂正記事検出通知

        Args:
            count: 訂正記事数
            sources: 訂正記事が見つかったソース
        """
        source_names = ', '.join(sources)
        cls.send(
            "NHK追跡システム - 訂正記事",
            f"{count}件の訂正記事を検出: {source_names}",
            sound="Ping"
        )

    @classmethod
    def notify_jwt_error(cls, source_name: str):
        """
        JWT認証エラー通知

        Args:
            source_name: エラーが発生したソース名
        """
        cls.send(
            "NHK追跡システム - 認証エラー",
            f"{source_name}でJWT認証エラーが発生しました",
            sound="Basso"
        )

    @classmethod
    def notify_correction_added(cls, source: str, title: str, keywords: str):
        """
        訂正追加通知

        Args:
            source: ソース名
            title: 記事タイトル
            keywords: 検出されたキーワード
        """
        cls.send(
            "NHK追跡システム - 訂正記事追加",
            f"{source}: {title}\nキーワード: {keywords}",
            sound="Ping"
        )

    @classmethod
    def notify_correction_removed(cls, source: str, title: str, keywords: str):
        """
        訂正削除通知（重要）

        Args:
            source: ソース名
            title: 記事タイトル
            keywords: 削除された訂正のキーワード
        """
        cls.send(
            "⚠️ NHK追跡 - 訂正が削除されました",
            f"{source}: {title}\n以前のキーワード: {keywords}",
            sound="Sosumi"
        )


def test_notifications():
    """通知機能のテスト"""
    print("macOS通知機能のテスト")
    print("="*60)

    # テスト1: 基本通知
    print("\n[テスト1] 基本通知")
    MacNotifier.send("テスト通知", "これはテスト通知です")

    # テスト2: サウンド付き通知
    print("\n[テスト2] サウンド付き通知")
    MacNotifier.send("テスト通知", "サウンド付きのテスト", sound="Glass")

    # テスト3: 実行完了通知（変更あり）
    print("\n[テスト3] 実行完了通知（変更あり）")
    MacNotifier.notify_completion(new_count=3, updated_count=1, total_count=800)

    # テスト4: 実行完了通知（変更なし）
    print("\n[テスト4] 実行完了通知（変更なし）")
    MacNotifier.notify_completion(new_count=0, updated_count=0, total_count=800)

    # テスト5: エラー通知
    print("\n[テスト5] エラー通知")
    MacNotifier.notify_error("取得エラー", "NHK東北の取得に失敗しました")

    # テスト6: 訂正記事検出通知
    print("\n[テスト6] 訂正記事検出通知")
    MacNotifier.notify_correction_detected(count=2, sources=["NHK首都圏", "NHK福岡"])

    # テスト7: JWT認証エラー通知
    print("\n[テスト7] JWT認証エラー通知")
    MacNotifier.notify_jwt_error("NHK東北ニュース")

    # テスト8: 失敗ソースありの完了通知
    print("\n[テスト8] 失敗ソースありの完了通知")
    MacNotifier.notify_completion(
        new_count=2,
        updated_count=1,
        total_count=750,
        failed_sources=["NHK東北ニュース"]
    )

    print("\n" + "="*60)
    print("通知テスト完了")


if __name__ == '__main__':
    test_notifications()
