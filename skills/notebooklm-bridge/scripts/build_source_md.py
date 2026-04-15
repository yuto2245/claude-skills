#!/usr/bin/env python3
"""
build_source_md.py — NotebookLM ソース用 Markdown ビルダー

復習項目の配列（または JSON ファイル）を受け取り、
YAMLフロントマター付きの Markdown ドキュメントを生成して stdout / ファイルに出力する。

生成された Markdown は Google Drive の sources/C_TS462/ に配置し、
NotebookLM のソースとして登録することで AI 音声概要の原稿になる。

使い方:
  # review-ids を直接指定（通常ユース）
  python build_source_md.py --review-ids abc123 def456 --topic "資産管理/在庫評価" --date 2026-04-16

  # JSON ファイルから読み込む
  python build_source_md.py --input-json reviews.json --topic "資産管理/在庫評価"

  # ファイルに書き出す
  python build_source_md.py --review-ids abc123 --topic "FIFO" --output /tmp/note.md

依存:
  pip install python-frontmatter pyyaml
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Optional

# python-frontmatter が入っていない環境でも部分動作させるため遅延インポート
try:
    import frontmatter  # type: ignore
    HAS_FRONTMATTER = True
except ImportError:
    HAS_FRONTMATTER = False

try:
    import yaml  # type: ignore
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


# ── データ型 ──────────────────────────────────────────────────────────────

class ReviewItem:
    """SM-2 の復習エントリを表す軽量データクラス。

    Notion DB のページから Claude が抽出して渡すことを想定している。
    フィールドは設計書の YAML フロントマター仕様に対応。
    """

    def __init__(
        self,
        notion_page_id: str,
        question: str,
        answer: str,
        sm2_stage: int = 0,
        tags: Optional[list] = None,
    ) -> None:
        self.notion_page_id = notion_page_id
        self.question = question
        self.answer = answer
        self.sm2_stage = sm2_stage
        self.tags = tags or []


# ── フロントマター生成 ─────────────────────────────────────────────────────

def build_frontmatter(
    topic: str,
    review_ids: list[str],
    sm2_stages: list[int],
    today: date,
    audio_requested: bool = True,
) -> dict:
    """YAML フロントマターの辞書を組み立てる。

    設計書仕様:
      title, topic, date, review_ids, sm2_stage, audio_requested, audio_path
    sm2_stage は items 全体の最大値（最も「新しい」段階）を代表値として記録。
    """
    # sm2_stage: 未知の項目（stage=0）が混在する場合でも max を代表値に
    representative_stage = max(sm2_stages) if sm2_stages else 0

    return {
        "title": f"SAP C_TS462 復習ノート — {topic} ({today.isoformat()})",
        "topic": f"C_TS462 / {topic}",
        "date": today.isoformat(),
        "review_ids": review_ids,
        "sm2_stage": representative_stage,
        "audio_requested": audio_requested,
        "audio_path": f"outputs/audio/{today.isoformat()}_{topic.replace('/', '_')}.mp3",
    }


# ── 本文 Markdown 生成 ────────────────────────────────────────────────────

def build_body(items: list[ReviewItem], topic: str, today: date) -> str:
    """NotebookLM が音声化しやすい構造化 Markdown を生成する。

    NotebookLM は見出し・箇条書き・Q&A 形式を得意とするため、
    各復習項目を「問い → 答え」形式で並べる。
    """
    lines: list[str] = []

    # ── ドキュメントヘッダ ─────────────────────────────────
    lines.append(f"# SAP C_TS462 復習ノート: {topic}")
    lines.append("")
    lines.append(f"> 生成日: {today.isoformat()}  ")
    lines.append(f"> 復習項目数: {len(items)} 件  ")
    lines.append(f"> 対象資格: SAP Certified Application Associate – SAP S/4HANA Cloud (C_TS462)")
    lines.append("")

    # ── 導入文（NotebookLM のポッドキャスト生成に乗りやすい形式）──
    lines.append("## このノートについて")
    lines.append("")
    lines.append(
        "このドキュメントは SM-2 アルゴリズムに基づく間隔反復学習の復習セッション記録です。"
        "各セクションは「問い」と「答え」のペアで構成されており、"
        "Audio Overview 機能で音声化して通勤中のリスニング学習に活用することを目的としています。"
    )
    lines.append("")

    # ── 復習項目セクション ────────────────────────────────
    lines.append("## 復習項目")
    lines.append("")

    if not items:
        # JSON が空の場合でも有効な Markdown を返す
        lines.append("_今日の復習項目はありません。_")
        lines.append("")
    else:
        for idx, item in enumerate(items, start=1):
            lines.append(f"### 項目 {idx}: {item.question}")
            lines.append("")
            lines.append(f"**問い**: {item.question}")
            lines.append("")
            lines.append(f"**答え**: {item.answer}")
            lines.append("")
            if item.tags:
                lines.append(f"**タグ**: {', '.join(item.tags)}")
                lines.append("")
            # SM-2 ステージを明記（NotebookLM のコンテキストとして有用）
            lines.append(
                f"_SM-2 ステージ: {item.sm2_stage} "
                f"(Notion ID: {item.notion_page_id})_"
            )
            lines.append("")

    # ── フッタ ─────────────────────────────────────────────
    lines.append("---")
    lines.append("")
    lines.append("*このノートは Claude Code の notebooklm-bridge スキルにより自動生成されました。*")
    lines.append("")

    return "\n".join(lines)


# ── ドキュメント組み立て ──────────────────────────────────────────────────

def build_document(
    items: list[ReviewItem],
    topic: str,
    today: Optional[date] = None,
    audio_requested: bool = True,
) -> str:
    """フロントマター + 本文を結合して完全な Markdown ドキュメントを返す。

    python-frontmatter が利用可能な場合はそのシリアライザを使い、
    ない場合は手書き YAML で先頭に付ける（フォールバック）。
    """
    today = today or date.today()

    review_ids = [item.notion_page_id for item in items]
    sm2_stages = [item.sm2_stage for item in items]

    fm_dict = build_frontmatter(topic, review_ids, sm2_stages, today, audio_requested)
    body = build_body(items, topic, today)

    if HAS_FRONTMATTER and HAS_YAML:
        # python-frontmatter を使って正規の YAML フロントマターを付与
        post = frontmatter.Post(body, **fm_dict)
        return frontmatter.dumps(post)
    elif HAS_YAML:
        # frontmatter なし・yaml あり のフォールバック
        yaml_str = yaml.dump(fm_dict, allow_unicode=True, default_flow_style=False)
        return f"---\n{yaml_str}---\n\n{body}"
    else:
        # 両方なし: 手書き YAML（最小限）
        lines = ["---"]
        for k, v in fm_dict.items():
            if isinstance(v, list):
                lines.append(f"{k}:")
                for item_v in v:
                    lines.append(f"  - {item_v}")
            else:
                lines.append(f"{k}: {v}")
        lines.append("---")
        lines.append("")
        lines.append(body)
        return "\n".join(lines)


# ── JSON 入力パーサ ───────────────────────────────────────────────────────

def parse_items_from_json(path: str) -> list[ReviewItem]:
    """JSON ファイルから ReviewItem リストを構築する。

    期待する JSON 形式（Claude が Notion DB から生成して渡す想定）:
    [
      {
        "notion_page_id": "abc123",
        "question": "FIFOとは何か？",
        "answer": "先入先出法。最初に入庫した品物から先に出庫する...",
        "sm2_stage": 2,
        "tags": ["在庫管理", "FIFO"]
      },
      ...
    ]
    """
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("JSON の最上位要素は配列である必要があります")

    items = []
    for entry in data:
        items.append(
            ReviewItem(
                notion_page_id=entry["notion_page_id"],
                question=entry["question"],
                answer=entry["answer"],
                sm2_stage=int(entry.get("sm2_stage", 0)),
                tags=entry.get("tags", []),
            )
        )
    return items


def parse_items_from_ids(review_ids: list[str]) -> list[ReviewItem]:
    """--review-ids だけ渡された場合のスタブ ReviewItem を生成する。

    実際の question/answer は Claude が Notion から取得して JSON に詰めて渡すのが理想。
    このパスは「とりあえず Drive にアップロードしたい」軽量ユースケース向け。
    """
    items = []
    for rid in review_ids:
        items.append(
            ReviewItem(
                notion_page_id=rid,
                # 実内容は Claude が後から Notion API で補完する
                question=f"[Notion ページ {rid} の問い — Claude が補完する]",
                answer=f"[Notion ページ {rid} の答え — Claude が補完する]",
                sm2_stage=0,
            )
        )
    return items


# ── CLI エントリポイント ──────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="復習項目から NotebookLM ソース用 Markdown を生成する",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # 入力ソース（どちらか一方を指定）
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--review-ids",
        nargs="+",
        metavar="ID",
        help="Notion ページ ID のリスト（スペース区切り）",
    )
    input_group.add_argument(
        "--input-json",
        metavar="PATH",
        help="ReviewItem の JSON ファイルパス",
    )

    parser.add_argument(
        "--topic",
        required=True,
        help="学習トピック（例: '資産管理/在庫評価'、'FIFO'）",
    )
    parser.add_argument(
        "--date",
        metavar="YYYY-MM-DD",
        help="ノートの日付（省略時は今日）",
    )
    parser.add_argument(
        "--output",
        metavar="PATH",
        help="出力ファイルパス（省略時は stdout）",
    )
    parser.add_argument(
        "--no-audio-request",
        action="store_true",
        help="フロントマターの audio_requested を false にする",
    )

    args = parser.parse_args()

    # 日付のパース
    if args.date:
        try:
            today = date.fromisoformat(args.date)
        except ValueError:
            print(f"ERROR: --date の形式が正しくありません: {args.date}", file=sys.stderr)
            sys.exit(1)
    else:
        today = date.today()

    # ReviewItem リストの構築
    if args.input_json:
        try:
            items = parse_items_from_json(args.input_json)
        except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
            print(f"ERROR: JSON 読み込み失敗: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # --review-ids のみ指定 → スタブ生成（Claude が後から補完）
        items = parse_items_from_ids(args.review_ids)

    # Markdown 生成
    document = build_document(
        items=items,
        topic=args.topic,
        today=today,
        audio_requested=not args.no_audio_request,
    )

    # 出力
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(document, encoding="utf-8")
        print(f"書き出し完了: {output_path}", file=sys.stderr)
    else:
        print(document)


if __name__ == "__main__":
    main()
