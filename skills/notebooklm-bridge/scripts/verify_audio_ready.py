#!/usr/bin/env python3
"""
verify_audio_ready.py — 音声ファイル生成完了ポーラー

NotebookLM が Audio Overview を生成し、Drive の outputs/audio/ にアップロードされるまで
ポーリングで待機する。見つかったら exit 0、タイムアウトしたら exit 1。

なぜポーリングが必要か:
  NotebookLM の Audio Overview 生成には数分〜10分程度かかる。
  Claude in Chrome MCP で操作した後、ダウンロードボタンが出現するまで画面を監視する。
  このスクリプトは Drive MCP 経由でファイル一覧をポーリングする「バックグラウンド待機」役。

使い方:
  # Drive の outputs/audio/ に YYYY-MM-DD_TOPIC.mp3 が現れるまで最大10分待つ
  python verify_audio_ready.py --audio-path "outputs/audio/2026-04-16_FIFO.mp3"

  # タイムアウト時間を変える
  python verify_audio_ready.py --audio-path "outputs/audio/2026-04-16_FIFO.mp3" --timeout-sec 300

  # Drive MCP 経由ではなく、ローカルファイルシステムでポーリング（テスト用）
  python verify_audio_ready.py --audio-path "/tmp/audio/2026-04-16_FIFO.mp3" --local

重要:
  このスクリプトは Drive MCP を直接呼び出せない（CLI として動作するため）。
  代わりに「Claude が定期的にこのスクリプトを実行 or drive_io.py の操作を参照する」
  パターンで使う。Drive ポーリングモードでは stdout に次の MCP 呼び出し指示を出力する。
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

# デフォルト設定（環境変数でオーバーライド可能）
DEFAULT_TIMEOUT_SEC = 600   # 10分
DEFAULT_POLL_INTERVAL_SEC = 30  # 30秒ごとにポーリング
DRIVE_ROOT_FOLDER_ID = os.environ.get("DRIVE_ROOT_FOLDER_ID", "YOUR_DRIVE_FOLDER_ID")


def verify_local(audio_path: str, timeout_sec: int, poll_interval: int) -> bool:
    """ローカルファイルシステムで音声ファイルの出現を待つ。

    テスト用・開発用。実際の Drive ファイルは ローカル MCP を通じてダウンロードされる。

    Returns:
        True: ファイルが見つかった
        False: タイムアウト
    """
    path = Path(audio_path)
    deadline = time.monotonic() + timeout_sec
    elapsed = 0

    print(f"[verify] ローカルポーリング開始: {path}", file=sys.stderr)
    print(f"[verify] タイムアウト: {timeout_sec}秒 / ポーリング間隔: {poll_interval}秒", file=sys.stderr)

    while time.monotonic() < deadline:
        if path.exists() and path.stat().st_size > 0:
            print(f"[verify] ✅ 音声ファイルを検出: {path}", file=sys.stderr)
            print(f"[verify] 経過時間: {elapsed}秒", file=sys.stderr)
            # ファイルパスを stdout に出力（呼び出し元が受け取って使う）
            print(str(path))
            return True

        remaining = int(deadline - time.monotonic())
        print(f"[verify] 待機中... 残り {remaining}秒", file=sys.stderr)
        time.sleep(poll_interval)
        elapsed += poll_interval

    print(f"[verify] ❌ タイムアウト ({timeout_sec}秒)", file=sys.stderr)
    return False


def verify_via_drive_mcp(audio_path: str, timeout_sec: int, poll_interval: int) -> bool:
    """Drive MCP 経由で音声ファイルの出現を待つ。

    このモードでは、Claude が実行すべき MCP 操作を JSON で stdout に出力し、
    Claude がその指示を読んで Drive MCP を呼び出す「対話ポーリング」を実現する。

    フロー:
      1. このスクリプトが「次の MCP 呼び出し」を JSON で stdout に出力
      2. Claude が MCP ツールを実行してファイル一覧を取得
      3. Claude がファイル一覧を解析して、このスクリプトを再実行 or 完了を判定

    Returns:
        True: 常に True（Drive MCP モードでは「指示出力」が成功を意味する）
    """
    # ポーリング指示を JSON で出力
    # Claude がこれを読んで MCP ツールを呼び出す
    instruction = {
        "mode": "drive_mcp_poll",
        "target_audio_path": audio_path,
        "timeout_sec": timeout_sec,
        "poll_interval_sec": poll_interval,
        "next_action": {
            "description": (
                f"以下の MCP ツールで Drive の outputs/audio/ 内ファイル一覧を取得し、"
                f"'{Path(audio_path).name}' が存在するか確認してください。"
                f" 存在すれば音声生成完了です。存在しなければ {poll_interval}秒後に再確認してください。"
            ),
            "mcp_tool": "mcp__google_drive__list_files",
            "params": {
                "folder_id": f"{DRIVE_ROOT_FOLDER_ID}/outputs/audio",
            },
            "success_condition": f"ファイル名 '{Path(audio_path).name}' がリストに含まれること",
            "failure_condition": f"{timeout_sec}秒経過してもファイルが見つからない場合",
        },
        "on_success": {
            "action": "download_audio",
            "description": "音声ファイルを /tmp/ にダウンロードし、ユーザーに通知する",
        },
        "on_failure": {
            "action": "human_fallback",
            "description": (
                "タイムアウトしました。NotebookLM の Audio Overview 生成が"
                " 完了しているか手動で確認してください: https://notebooklm.google.com"
            ),
        },
    }

    print(json.dumps(instruction, ensure_ascii=False, indent=2))
    print(
        f"\n[verify] Drive MCP ポーリング指示を出力しました。"
        f" Claude が上記の JSON に従って MCP を呼び出してください。",
        file=sys.stderr,
    )
    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="NotebookLM 音声ファイルの生成完了をポーリングで待つ",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--audio-path",
        required=True,
        metavar="PATH",
        help="待機する音声ファイルのパス（Drive 上のパス、または --local 時はローカルパス）",
    )
    parser.add_argument(
        "--timeout-sec",
        type=int,
        default=DEFAULT_TIMEOUT_SEC,
        metavar="SECONDS",
        help=f"最大待機時間（秒）。デフォルト: {DEFAULT_TIMEOUT_SEC}",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=DEFAULT_POLL_INTERVAL_SEC,
        metavar="SECONDS",
        help=f"ポーリング間隔（秒）。デフォルト: {DEFAULT_POLL_INTERVAL_SEC}",
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="ローカルファイルシステムでポーリング（テスト用）",
    )

    args = parser.parse_args()

    if args.local:
        success = verify_local(args.audio_path, args.timeout_sec, args.poll_interval)
    else:
        # Drive MCP モード: 操作指示を stdout に出力
        success = verify_via_drive_mcp(args.audio_path, args.timeout_sec, args.poll_interval)

    # exit 0: 成功（ファイル検出 or 指示出力完了）
    # exit 1: ローカルモードでタイムアウト
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
