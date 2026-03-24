#!/usr/bin/env python3
"""
Grokipedia APIからイーロン・マスク関連の情報を取得するスクリプト。

使い方:
  python3 fetch_grokipedia.py --query "Elon Musk" --output /tmp/elon_data.json
"""

import argparse
import json
import sys
from datetime import datetime


def fetch_grokipedia(query: str, output_path: str) -> None:
    """
    Grokipedia APIを使って指定クエリの情報を取得し、JSONで保存する。

    処理の流れ:
    1. grokipedia_api をインポート（インストールされていない場合はエラー）
    2. search() で関連ページを検索
    3. 上位ページの get_page() でフルコンテンツを取得
    4. キャリア・哲学・発言に関するセクションを抽出
    5. JSONで保存
    """
    try:
        from grokipedia_api import GrokipediaClient
        from grokipedia_api.exceptions import GrokipediaNotFoundError
    except ImportError:
        error_msg = (
            "grokipedia_api がインストールされていません。\n"
            "インストール: pip install grokipedia-api --break-system-packages"
        )
        print(f"ERROR: {error_msg}", file=sys.stderr)
        # フォールバックデータを出力してスクリプトを正常終了させる
        fallback = {
            "fetched_at": datetime.now().isoformat(),
            "source": "fallback",
            "error": error_msg,
            "data": [],
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(fallback, f, ensure_ascii=False, indent=2)
        return

    client = GrokipediaClient()
    results_data = []

    # Step 1: 検索
    print(f"Searching Grokipedia for: {query}")
    search_results = client.search(query, limit=5)

    if not search_results.get("results"):
        print("No results found.")
    else:
        # Step 2: 上位3件のページを取得
        for result in search_results["results"][:3]:
            slug = result.get("slug", "")
            title = result.get("title", "")
            print(f"Fetching page: {title} ({slug})")

            try:
                page = client.get_page(slug, include_content=True)
                page_info = page.get("page", {})

                results_data.append({
                    "title": page_info.get("title", title),
                    "slug": slug,
                    # コンテンツは最初の3000文字に絞る（コンテキスト節約）
                    "content_preview": (page_info.get("content", ""))[:3000],
                    "citations_count": len(page_info.get("citations", [])),
                })
            except GrokipediaNotFoundError:
                print(f"  Page not found: {slug}")
            except Exception as e:
                print(f"  Error fetching {slug}: {e}")

    # Step 3: 結果を保存
    output = {
        "fetched_at": datetime.now().isoformat(),
        "source": "grokipedia",
        "query": query,
        "total_results": len(results_data),
        "data": results_data,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(results_data)} pages to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Fetch data from Grokipedia API")
    parser.add_argument("--query", required=True, help="Search query (e.g. 'Elon Musk')")
    parser.add_argument("--output", required=True, help="Output JSON file path")
    args = parser.parse_args()

    fetch_grokipedia(args.query, args.output)


if __name__ == "__main__":
    main()
