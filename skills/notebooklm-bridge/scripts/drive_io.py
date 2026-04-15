#!/usr/bin/env python3
"""
drive_io.py — Google Drive MCP 操作ラッパー

設計方針:
  このファイルは「Claude が読んで実行する宣言的な手順」を Python コードとして表現したものです。
  実際の Drive API 呼び出しは Claude が MCP ツール（mcp__google_drive__* 系）を通じて行います。
  このモジュールは以下の2つの役割を担います:

  1. CLI スクリプト: `python drive_io.py upload --local /tmp/note.md --remote sources/C_TS462/`
     → Claude が実行し、必要な MCP ツール呼び出しの引数を stdout に出力する

  2. ドキュメント: 各関数のdocstringが「Claude へのオペレーション指示書」になっている

なぜこの設計か:
  NotebookLM には公式外部 API が存在しないため、Drive を「バッファ層」として使う。
  Drive MCP の具体的なツール名・引数は MCP 接続状況により変わる可能性があるため、
  このラッパーでツール名を1箇所に集約し変更容量を最小化する。

依存:
  標準ライブラリのみ（Drive MCP は Claude が直接呼び出す）
"""

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


# ── 設定 ──────────────────────────────────────────────────────────────────

# SKILL.md の設定値セクションと対応。環境変数でオーバーライド可能。
DRIVE_ROOT_FOLDER_ID = os.environ.get("DRIVE_ROOT_FOLDER_ID", "YOUR_DRIVE_FOLDER_ID")
SOURCES_FOLDER = os.environ.get("SOURCES_FOLDER", "sources/C_TS462")
AUDIO_OUTPUT_FOLDER = os.environ.get("AUDIO_OUTPUT_FOLDER", "outputs/audio")
SUMMARIES_FOLDER = os.environ.get("SUMMARIES_FOLDER", "outputs/summaries")
INDEX_FILE = "index.json"


# ── データ型 ──────────────────────────────────────────────────────────────

@dataclass
class DriveOperation:
    """Claude が実行すべき Drive MCP 操作を表す。

    このオブジェクトを JSON にシリアライズして stdout に出力することで、
    Claude（またはシェルスクリプト）がどの MCP ツールを呼べばよいかを把握できる。
    """
    action: str           # "upload" | "download" | "list" | "read_index" | "write_index"
    mcp_tool: str         # 呼び出すべき MCP ツール名（例: mcp__google_drive__upload_file）
    params: dict          # MCP ツールに渡す引数
    description: str      # 人間向け説明


# ── MCP ツール定義 ─────────────────────────────────────────────────────────

# Google Drive MCP のツール名はプロバイダにより異なる場合がある。
# ここで一元管理し、変更時はここだけ修正する。
MCP_TOOLS = {
    "upload":   "mcp__google_drive__upload_file",
    "download": "mcp__google_drive__download_file",
    "list":     "mcp__google_drive__list_files",
    "create_folder": "mcp__google_drive__create_folder",
    "search":   "mcp__google_drive__search",
}


# ── 操作生成関数 ──────────────────────────────────────────────────────────

def plan_upload_source(
    local_path: str,
    filename: str,
    topic: Optional[str] = None,
) -> DriveOperation:
    """ソース Markdown を sources/ にアップロードする操作を生成する。

    Claude は返された DriveOperation の mcp_tool と params を使って
    実際の MCP ツールを呼び出す。

    Args:
        local_path: ローカルの一時ファイルパス（例: /tmp/note.md）
        filename: Drive 上のファイル名（例: 2026-04-16_FIFO_note.md）
        topic: サブトピック（例: "在庫管理"）。None の場合デフォルトフォルダに配置
    """
    remote_folder = SOURCES_FOLDER
    if topic:
        # トピック名をサニタイズしてサブフォルダにする（オプション）
        safe_topic = topic.replace("/", "_").replace(" ", "_")
        remote_folder = f"{SOURCES_FOLDER}/{safe_topic}"

    return DriveOperation(
        action="upload",
        mcp_tool=MCP_TOOLS["upload"],
        params={
            "local_path": local_path,
            "remote_folder_id": f"{DRIVE_ROOT_FOLDER_ID}/{remote_folder}",
            "filename": filename,
            "mime_type": "text/markdown",
        },
        description=(
            f"'{filename}' を Drive の {remote_folder}/ にアップロード。"
            " NotebookLM がソースとして参照できるようになる。"
        ),
    )


def plan_upload_audio(
    local_path: str,
    filename: str,
) -> DriveOperation:
    """NotebookLM が生成した音声ファイルを outputs/audio/ に保存する操作を生成する。

    Args:
        local_path: ダウンロードした音声ファイルのローカルパス
        filename: Drive 上のファイル名（例: 2026-04-16_FIFO.mp3）
    """
    return DriveOperation(
        action="upload",
        mcp_tool=MCP_TOOLS["upload"],
        params={
            "local_path": local_path,
            "remote_folder_id": f"{DRIVE_ROOT_FOLDER_ID}/{AUDIO_OUTPUT_FOLDER}",
            "filename": filename,
            "mime_type": "audio/mpeg",
        },
        description=(
            f"NotebookLM 生成音声 '{filename}' を Drive の {AUDIO_OUTPUT_FOLDER}/ に保存。"
            " スマホからストリーミング再生可能になる。"
        ),
    )


def plan_download_audio(
    filename: str,
    local_dir: str = "/tmp",
) -> DriveOperation:
    """outputs/audio/ から音声ファイルをダウンロードする操作を生成する。

    Args:
        filename: ダウンロードしたいファイル名
        local_dir: 保存先ローカルディレクトリ
    """
    return DriveOperation(
        action="download",
        mcp_tool=MCP_TOOLS["download"],
        params={
            "remote_folder_id": f"{DRIVE_ROOT_FOLDER_ID}/{AUDIO_OUTPUT_FOLDER}",
            "filename": filename,
            "local_dir": local_dir,
        },
        description=f"音声ファイル '{filename}' を {local_dir}/ にダウンロード。",
    )


def plan_list_audio() -> DriveOperation:
    """outputs/audio/ 内のファイル一覧を取得する操作を生成する。

    verify_audio_ready.py がポーリングする際に使用する。
    """
    return DriveOperation(
        action="list",
        mcp_tool=MCP_TOOLS["list"],
        params={
            "folder_id": f"{DRIVE_ROOT_FOLDER_ID}/{AUDIO_OUTPUT_FOLDER}",
        },
        description=f"{AUDIO_OUTPUT_FOLDER}/ 内のファイル一覧を取得。音声生成完了を検出するために使用。",
    )


def plan_read_index() -> DriveOperation:
    """index.json を読み込む操作を生成する。"""
    return DriveOperation(
        action="read_index",
        mcp_tool=MCP_TOOLS["download"],
        params={
            "remote_folder_id": DRIVE_ROOT_FOLDER_ID,
            "filename": INDEX_FILE,
            "local_dir": "/tmp",
        },
        description="index.json を /tmp/ にダウンロードして状態を確認する。",
    )


def plan_write_index(local_path: str = f"/tmp/{INDEX_FILE}") -> DriveOperation:
    """更新した index.json を Drive にアップロードする操作を生成する。"""
    return DriveOperation(
        action="write_index",
        mcp_tool=MCP_TOOLS["upload"],
        params={
            "local_path": local_path,
            "remote_folder_id": DRIVE_ROOT_FOLDER_ID,
            "filename": INDEX_FILE,
            "mime_type": "application/json",
        },
        description="更新した index.json を Drive に書き戻す。",
    )


# ── index.json 操作 ───────────────────────────────────────────────────────

def load_index(local_path: str = f"/tmp/{INDEX_FILE}") -> dict:
    """ローカルにダウンロードされた index.json を読み込む。

    存在しない場合は空の初期構造を返す（初回セットアップ時）。
    """
    p = Path(local_path)
    if not p.exists():
        return {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "sources": [],
            "audio_files": [],
        }
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def register_source(
    index: dict,
    filename: str,
    topic: str,
    review_ids: list[str],
    date_str: str,
    audio_requested: bool = True,
) -> dict:
    """index.json にソースファイルのエントリを追加する。

    既に同名のエントリが存在する場合は上書きする（冪等）。
    """
    entry = {
        "filename": filename,
        "topic": topic,
        "date": date_str,
        "review_ids": review_ids,
        "audio_requested": audio_requested,
        "audio_path": None,  # 音声生成後に verify_audio_ready.py が更新
        "registered_at": datetime.now().isoformat(),
    }

    # 既存エントリを上書き（冪等化）
    sources = index.get("sources", [])
    sources = [s for s in sources if s["filename"] != filename]
    sources.append(entry)
    index["sources"] = sources
    return index


def save_index(index: dict, local_path: str = f"/tmp/{INDEX_FILE}") -> None:
    """index.json をローカルに保存する（Drive への書き戻しは plan_write_index() を使う）。"""
    with open(local_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


# ── CLI ──────────────────────────────────────────────────────────────────

def cmd_upload(args) -> None:
    """upload サブコマンド: アップロード操作の JSON を stdout に出力する。

    Claude がこの出力を読み取って MCP ツールを呼び出す。
    """
    if args.type == "source":
        op = plan_upload_source(args.local, args.filename, args.topic)
    elif args.type == "audio":
        op = plan_upload_audio(args.local, args.filename)
    else:
        print(f"ERROR: --type に 'source' または 'audio' を指定してください", file=sys.stderr)
        sys.exit(1)

    # Claude が読み取りやすい JSON + 人間向け説明を出力
    print(json.dumps({
        "operation": op.action,
        "mcp_tool": op.mcp_tool,
        "params": op.params,
        "description": op.description,
        "next_step": (
            f"Claude は上記の mcp_tool を params で呼び出してください。"
            " 完了後、index.json の該当エントリを更新してください。"
        ),
    }, ensure_ascii=False, indent=2))


def cmd_list_audio(args) -> None:
    """list-audio サブコマンド: 音声ファイル一覧操作の JSON を stdout に出力する。"""
    op = plan_list_audio()
    print(json.dumps({
        "operation": op.action,
        "mcp_tool": op.mcp_tool,
        "params": op.params,
        "description": op.description,
    }, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Drive MCP 操作を生成する（Claude が読んで実行する）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # upload サブコマンド
    up = subparsers.add_parser("upload", help="ファイルのアップロード操作を生成")
    up.add_argument("--type", choices=["source", "audio"], required=True,
                    help="アップロードファイルの種別")
    up.add_argument("--local", required=True, help="ローカルファイルパス")
    up.add_argument("--filename", required=True, help="Drive 上のファイル名")
    up.add_argument("--topic", help="トピック（source の場合のみ）")

    # list-audio サブコマンド
    subparsers.add_parser("list-audio", help="音声ファイル一覧操作を生成")

    args = parser.parse_args()

    if args.command == "upload":
        cmd_upload(args)
    elif args.command == "list-audio":
        cmd_list_audio(args)


if __name__ == "__main__":
    main()
