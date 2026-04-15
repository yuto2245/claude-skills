---
name: notebooklm-bridge
description: |
  復習項目を Google Drive 経由で NotebookLM に送り、AI 音声概要（Audio Overview）を自動生成するスキル。
  SAP C_TS462 の学習ノートを通勤中に音声で聴けるように変換することを主目的とする。
  Phase1: Drive へのMarkdown書き込み。Phase2: Chrome MCP による NotebookLM 操作で音声生成。

  以下のトリガー語で起動すること:
  - 「今日の復習を音声化して」「NotebookLMで音声にして」「ポッドキャストにして」
  - 「NotebookLMに〇〇を聞いて」「NotebookLMで調べて」
  - 「学習ログをNotebookLMに蓄積」「NotebookLMのソースに追加」

  Always use this skill when the user wants to:
  - Convert review items to NotebookLM audio
  - Add learning logs to NotebookLM sources
  - Ask NotebookLM a question via chat
---

# notebooklm-bridge

復習項目 → Google Drive → NotebookLM → 音声 のパイプラインを自動化するスキル。

---

## アーキテクチャ

```
[review-scheduler / Notion DB]
        ↓ review_ids
[build_source_md.py]          → YAMLフロントマター付き Markdown
        ↓
[Drive MCP: sources/ に upload]
        ↓ (手動 or Phase3 で自動同期)
[NotebookLM Notebook]
        ↓ Audio Overview 生成
[Chrome MCP: 操作 & DL]
        ↓
[Drive MCP: outputs/audio/ に保存]
        ↓
[ユーザーがスマホで再生]
```

---

## Drive フォルダ構成

```
/NotebookLM-SAP/
├── sources/
│   └── C_TS462/
│       ├── YYYY-MM-DD_<topic>_note.md        # 日次学習ノート
│       └── YYYY-Www_weekly_digest.md          # 週次ダイジェスト
├── outputs/
│   ├── audio/
│   │   └── YYYY-MM-DD_<topic>.mp3             # NotebookLM 生成音声
│   └── summaries/
│       └── YYYY-MM-DD_<topic>_summary.md      # テキストサマリ
└── index.json                                  # ファイル管理インデックス
```

---

## 設定値（初回セットアップ時に書き換える）

```
NOTEBOOK_ID: YOUR_NOTEBOOK_ID
  → NotebookLM の URL から取得:
    https://notebooklm.google.com/notebook/<NOTEBOOK_ID>

DRIVE_ROOT_FOLDER_ID: YOUR_DRIVE_FOLDER_ID
  → Google Drive で /NotebookLM-SAP/ フォルダを作成し、
    共有URLの末尾IDをここに記入

SOURCES_FOLDER: sources/C_TS462/
AUDIO_OUTPUT_FOLDER: outputs/audio/
```

---

## Phase1: Drive への書き込み（実装済み）

### モード A: 今日の復習を音声化

ユーザーが「今日の復習を音声化して」と言ったとき:

1. review-scheduler スキルから今日期限の review_ids リストを取得
2. `scripts/build_source_md.py` を CLI で呼び出し、Markdown を生成
   ```bash
   python scripts/build_source_md.py \
     --review-ids <id1> <id2> ... \
     --topic "C_TS462/YYYY-MM-DD_<topic>" \
     --output /tmp/note.md
   ```
3. 生成された `/tmp/note.md` を Drive MCP で sources/ にアップロード
   - 呼び出し: `drive_io.py` のロジックに従い Drive MCP を呼び出す
   - ファイル名: `YYYY-MM-DD_<topic>_note.md`
4. `audio_requested: true` を index.json に記録

### モード B: NotebookLM のソースに手動追加

ユーザーが「学習ログをNotebookLMに蓄積」と言ったとき:

1. ユーザーからトピックと内容を受け取る
2. テンプレート `templates/source_note_template.md` を元に Markdown を生成
3. Drive MCP で sources/ にアップロード

---

## Phase2: Chrome MCP による音声生成（実装済み）

`scripts/chrome_notebooklm.md` の手順書に従い Claude が Chrome MCP を操作する。

### フロー F1: Audio Overview 生成

1. `scripts/chrome_notebooklm.md` の F1 セクションを読み込む
2. Claude in Chrome MCP で NotebookLM を開き操作
3. 生成した音声ファイルをDL
4. Drive MCP で `outputs/audio/` にアップロード

### フロー F2: チャット質問

1. `scripts/chrome_notebooklm.md` の F2 セクションを読み込む
2. Claude in Chrome MCP でチャット欄に質問を入力
3. 回答テキストを取得してユーザーに返す

---

## 依存関係

- **Google Drive MCP**: sources/ への書き込み・outputs/ からの読み込み
- **Claude in Chrome MCP**: NotebookLM UI 操作
- **review-scheduler スキル**: SM-2 ステージと review_ids の提供
- **Python 3.11+**: `scripts/` 内のスクリプト実行
  - ライブラリ: `python-frontmatter`, `pyyaml`（requirements.txt 参照）

---

## 初回セットアップ手順

1. Google Drive で `/NotebookLM-SAP/` フォルダを作成
2. サブフォルダ `sources/C_TS462/`, `outputs/audio/`, `outputs/summaries/` を作成
3. NotebookLM (https://notebooklm.google.com) で新規 Notebook を作成
4. Notebook の URLから ID を取得し、本 SKILL.md の設定値セクションに記入
5. NotebookLM の Notebook にソースとして Drive の sources/ フォルダを登録（手動）
6. Chrome MCP 接続確認: `mcp__Claude_in_Chrome__navigate` で動作テスト

---

## TODO: Phase3 / Phase4

### Phase3: Notion → Drive 自動同期

- [ ] review-scheduler の Notion DB を定期ポーリング
- [ ] 期限が当日以前の項目を自動で build_source_md.py に渡す
- [ ] 生成された Markdown を Drive に自動アップロード（CronCreate 使用想定）
- [ ] `index.json` の自動更新

### Phase4: 音声ダウンロード & Notion への結果書き戻し

- [ ] `verify_audio_ready.py` による音声生成完了ポーリング
- [ ] 生成音声の Drive への自動保存
- [ ] Notion の復習ページに `audio_path` を書き戻す
- [ ] スマホ向け共有リンク生成

---

## エラーハンドリング方針

- Chrome MCP 操作は各ステップで `screenshot` 検証を挟む
- 3回リトライ後は人間フォールバック（ユーザーに操作を依頼）
- Drive MCP 未接続時は `/tmp/` に保存してパスをユーザーに通知
- Chrome MCP 未接続時は `chrome_notebooklm.md` の手順をユーザーに提示
