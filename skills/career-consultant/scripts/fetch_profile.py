#!/usr/bin/env python3
"""
Google SpreadsheetからCSV形式でナレッジ・経歴データを取得するスクリプト。

前提: スプレッドシートが「リンクを知っている全員が閲覧可能」に設定されていること。

使い方:
  python3 fetch_profile.py \
    --url "https://docs.google.com/spreadsheets/d/{ID}/export?format=csv" \
    --output /tmp/yuto_profile.json

スプレッドシートのエクスポートURL形式:
  単一シート: https://docs.google.com/spreadsheets/d/{ID}/export?format=csv
  特定シート: https://docs.google.com/spreadsheets/d/{ID}/export?format=csv&gid={SHEET_ID}
"""

import argparse
import csv
import io
import json
import sys
from datetime import datetime

# PROFILE_URL をここに設定しておくと --url 引数を省略できる
DEFAULT_PROFILE_URL = ""  # 例: "https://docs.google.com/spreadsheets/d/xxxx/export?format=csv"


def fetch_csv_from_google(url: str) -> list[dict]:
    """
    指定URLからCSVを取得してdictのリストで返す。

    Googleの公開スプレッドシートは認証なしでCSVエクスポートできる。
    urllib を使うことで外部ライブラリ不要。
    """
    import urllib.request

    print(f"Fetching CSV from: {url}")

    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            content = response.read().decode("utf-8")
    except Exception as e:
        raise RuntimeError(f"Failed to fetch spreadsheet: {e}")

    # CSV → dictリストに変換
    reader = csv.DictReader(io.StringIO(content))
    rows = list(reader)
    print(f"  Fetched {len(rows)} rows")
    return rows


def parse_profile(rows: list[dict]) -> dict:
    """
    CSVの行をキャリアコンサルタントが使いやすい形に整形する。

    CSVの構造は自由だが、以下のキーがあると自動的に分類される:
    - カテゴリ列: "category", "カテゴリ", "種別"
    - 内容列: "content", "内容", "detail"
    - 期間列: "period", "期間", "時期"

    カテゴリ値の例: "career", "skill", "certification", "goal", "note"
    """
    parsed = {
        "career": [],
        "skills": [],
        "certifications": [],
        "goals": [],
        "notes": [],
        "raw": rows,  # 分類できなかった行も保持
    }

    # カテゴリ列のキーを柔軟に検出
    category_keys = ["category", "カテゴリ", "種別", "type"]
    content_keys = ["content", "内容", "detail", "詳細", "value"]

    for row in rows:
        # カテゴリを検出
        category = ""
        for key in category_keys:
            if key in row and row[key]:
                category = str(row[key]).lower().strip()
                break

        # 内容を検出
        content = ""
        for key in content_keys:
            if key in row and row[key]:
                content = str(row[key]).strip()
                break

        if not content:
            # カテゴリ・内容以外の列を結合
            content = " | ".join(
                f"{k}: {v}" for k, v in row.items()
                if v and k not in category_keys
            )

        # カテゴリに応じて振り分け
        if any(x in category for x in ["career", "職歴", "経歴", "work"]):
            parsed["career"].append(row)
        elif any(x in category for x in ["skill", "スキル", "技術"]):
            parsed["skills"].append(content)
        elif any(x in category for x in ["cert", "資格", "qualification"]):
            parsed["certifications"].append(content)
        elif any(x in category for x in ["goal", "目標", "objective"]):
            parsed["goals"].append(content)
        elif any(x in category for x in ["note", "備考", "メモ", "memo"]):
            parsed["notes"].append(content)
        # カテゴリが不明な場合はnotesに入れる
        elif content:
            parsed["notes"].append(content)

    return parsed


def main():
    parser = argparse.ArgumentParser(
        description="Fetch profile data from Google Spreadsheet"
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_PROFILE_URL,
        help="Google Spreadsheet CSV export URL"
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output JSON file path (e.g. /tmp/yuto_profile.json)"
    )
    args = parser.parse_args()

    url = args.url
    if not url:
        print(
            "ERROR: --url が指定されていません。\n"
            "スクリプト内の DEFAULT_PROFILE_URL を設定するか、"
            "--url 引数でURLを渡してください。",
            file=sys.stderr,
        )
        # フォールバックデータで続行
        output = {
            "fetched_at": datetime.now().isoformat(),
            "source": "fallback",
            "error": "No URL provided",
            "parsed": {
                "career": [],
                "skills": [],
                "certifications": [],
                "goals": [],
                "notes": ["URLが未設定のためフォールバックデータを使用"],
            },
        }
    else:
        try:
            rows = fetch_csv_from_google(url)
            parsed = parse_profile(rows)
            output = {
                "fetched_at": datetime.now().isoformat(),
                "source_url": url,
                "row_count": len(rows),
                "parsed": parsed,
            }
        except Exception as e:
            print(f"ERROR: {e}", file=sys.stderr)
            output = {
                "fetched_at": datetime.now().isoformat(),
                "source": "fallback",
                "error": str(e),
                "parsed": {
                    "career": [],
                    "skills": [],
                    "certifications": [],
                    "goals": [],
                    "notes": [f"取得エラー: {e}"],
                },
            }

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Profile data saved to: {args.output}")


if __name__ == "__main__":
    main()
