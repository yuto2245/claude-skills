# notebooklm-bridge

> 「スマホ一台でどん底から這い上がる証明を、自分に。」

通勤中のスマホ音声学習で SAP C_TS462 を攻略するための自動化スキル。
SM-2 間隔反復で蓄積した復習項目を NotebookLM の AI 音声に変換し、
耳だけで学べる形にするパイプラインです。

---

## なぜこの設計か

NotebookLM に公式の外部 API はありません。
そのため、このスキルは **ハイブリッドアーキテクチャ** を採用しています。

```
Notion DB（SM-2 データ）
    ↓ review_ids
Claude Code（build_source_md.py）
    ↓ YAMLフロントマター付き Markdown
Google Drive MCP（sources/ にアップロード）
    ↓ ソースとして参照
NotebookLM（Audio Overview 生成）
    ↓ Chrome MCP で操作
Google Drive MCP（outputs/audio/ に保存）
    ↓ スマホでストリーミング
通勤中のリスニング
```

**データ層** は Google Drive で、**操作層** は Chrome MCP で NotebookLM の画面を操作します。
Drive をバッファにすることで、NotebookLM への API 依存を排除し、
将来的に公式 API が提供されても最小限の変更で対応できます。

---

## Phase1 だけで何ができるか

**Phase1（Drive 片方向 — 現在実装済み）** では：

- 今日の SM-2 復習項目を Markdown ノートに変換できる
- Google Drive の `/NotebookLM-SAP/sources/C_TS462/` にアップロードできる
- NotebookLM の Notebook に手動でソースを追加できる（手動ステップあり）
- 週次ダイジェストのテンプレートが使える

つまり **「毎日の復習を素材化して Drive に置く」** ことが自動化されます。
音声生成は NotebookLM の UI で手動でトリガーするか、Phase2 で自動化します。

---

## 初回セットアップ（一度だけ行う）

### Step 1: Google Drive のフォルダ構成を作る

Google Drive で以下のフォルダ構造を手動で作成してください：

```
/NotebookLM-SAP/
├── sources/
│   └── C_TS462/
├── outputs/
│   ├── audio/
│   └── summaries/
```

作成後、`/NotebookLM-SAP/` フォルダの **共有 URL** からフォルダ ID を取得します：
```
https://drive.google.com/drive/folders/XXXXXXXXXXXXXXXXXXXX
                                        ↑ これが DRIVE_ROOT_FOLDER_ID
```

### Step 2: SKILL.md の設定値を書き換える

`SKILL.md` の「設定値」セクションを開き、以下を実際の値に置き換えてください：

```
NOTEBOOK_ID: <NotebookLM の Notebook URL から取得>
DRIVE_ROOT_FOLDER_ID: <Step 1 で取得したフォルダ ID>
```

### Step 3: NotebookLM で Notebook を作成する

1. https://notebooklm.google.com を開く
2. 「New Notebook」をクリック
3. Notebook 名を設定（例: "SAP C_TS462 復習"）
4. URL から Notebook ID を取得して SKILL.md に記入

### Step 4: Google Drive フォルダをソースとして登録（手動）

NotebookLM の Notebook を開き：
1. 「Add source」→「Google Drive」を選択
2. `/NotebookLM-SAP/sources/C_TS462/` フォルダを選択
3. 「Insert」をクリック

以降、このフォルダに Markdown を追加すると NotebookLM が自動で認識します。

### Step 5: Python 依存関係をインストールする

```bash
cd skills/notebooklm-bridge
pip install -r requirements.txt
```

### Step 6: 動作確認

```bash
# テスト用の Markdown を生成して stdout に出力
python scripts/build_source_md.py \
  --review-ids test001 test002 \
  --topic "テスト" \
  --date 2026-04-16
```

---

## 日々の使い方

### 「今日の復習を音声化して」（フルオート — Phase2）

Claude Code に話しかけるだけ：

```
今日の復習を音声化して
```

Claude が以下を自動実行します：
1. review-scheduler から今日の復習 IDs を取得
2. build_source_md.py で Markdown を生成
3. Drive の sources/ にアップロード
4. Chrome MCP で NotebookLM を操作し Audio Overview を生成
5. 完成した .mp3 を Drive の outputs/audio/ に保存

### 「NotebookLMに〇〇を聞いて」（チャット質問）

```
NotebookLMにFIFOと移動平均の違いを聞いて
```

Chrome MCP で NotebookLM のチャット欄に質問して回答を返します。

### ソースを手動追加する場合

```
学習ログをNotebookLMに蓄積して
```

Claude がトピックと内容をヒアリングして Markdown を生成・アップロードします。

---

## ファイル構成

```
skills/notebooklm-bridge/
├── SKILL.md                      ← Claude が読むスキル定義（トリガー語・フロー）
├── README.md                     ← このファイル
├── requirements.txt              ← Python 依存関係
├── .gitignore                    ← .venv, __pycache__ 等を除外
├── scripts/
│   ├── build_source_md.py        ← 復習項目 → Markdown 変換 CLI
│   ├── drive_io.py               ← Drive MCP 操作ラッパー
│   ├── verify_audio_ready.py     ← 音声生成完了ポーラー
│   └── chrome_notebooklm.md     ← NotebookLM UI 操作手順書（Claude が読む）
└── templates/
    ├── source_note_template.md   ← 手動ノート作成用テンプレート
    └── weekly_digest_template.md ← 週次ダイジスト用テンプレート
```

---

## Phase3 / Phase4 について

現在は Phase1 + Phase2 が実装されています。

- **Phase3**: Notion → Drive 自動同期（CronCreate で毎朝実行）
- **Phase4**: 音声完了後に Notion へ結果を書き戻す + スマホ共有リンク生成

詳細は `SKILL.md` の TODO セクションを参照してください。

---

## トラブルシューティング

| 症状 | 原因 | 対処 |
|-----|-----|-----|
| "No sources" が表示される | Drive フォルダが NotebookLM に登録されていない | Step 4 を再実行 |
| Chrome MCP がタイムアウト | NotebookLM の UI 変更 | `chrome_notebooklm.md` のセレクタを更新 |
| Drive MCP が接続されていない | MCP 設定 | Claude Code の設定で Google Drive MCP を接続 |
| build_source_md.py が失敗 | Python 依存関係 | `pip install -r requirements.txt` を実行 |

---

*このスキルは `yuto2245/claude-skills` リポジトリで管理されています。*
