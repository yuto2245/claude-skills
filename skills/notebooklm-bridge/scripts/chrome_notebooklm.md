# chrome_notebooklm.md — NotebookLM UI 操作手順書

**このファイルは Claude が読み取って実行する宣言的な操作手順書です。**
Claude in Chrome MCP（`mcp__Claude_in_Chrome__*`）を使って NotebookLM の画面を操作します。

---

## 前提条件

- Chrome MCP が接続済みであること（`mcp__Claude_in_Chrome__navigate` が呼び出し可能）
- SKILL.md の設定値 `NOTEBOOK_ID` が実際の ID に書き換えられていること
- NotebookLM に Google アカウントでログイン済みであること

---

## セレクタ抽象化の原則（3層防御）

1. **第1層: aria-label / role 属性を優先**
   - DOM 構造は UI アップデートで変わるが、アクセシビリティ属性は比較的安定
   - 例: `button[aria-label="Generate audio overview"]`

2. **第2層: テキストコンテンツによるフォールバック**
   - aria-label が見つからない場合、ボタンテキストで検索
   - `mcp__Claude_in_Chrome__find` で "Generate" "Audio" などのキーワードを探す

3. **第3層: スクリーンショット + 人間フォールバック**
   - 上記2層が失敗した場合、`screenshot` を取得してユーザーに提示
   - 「このボタンを押してください」とユーザーに依頼

---

## F1: Audio Overview 生成フロー

### F1-1: NotebookLM を開く

```
操作:
  mcp__Claude_in_Chrome__navigate
    url: "https://notebooklm.google.com/notebook/{NOTEBOOK_ID}"

検証（screenshot で確認）:
  - "Notebook" または対象ノートブック名がページに表示されていること
  - ログインページにリダイレクトされていないこと

失敗時:
  → ユーザーに「NotebookLM にログインして Notebook を開いてください」と案内
```

### F1-2: Audio Overview パネルを開く

```
操作（順に試す）:
  1. aria-label "Audio Overview" のボタンまたはタブを探す
     mcp__Claude_in_Chrome__find
       selector: '[aria-label*="Audio"], [aria-label*="audio"], button:contains("Audio")'

  2. 見つかったらクリック
     mcp__Claude_in_Chrome__form_input or left_click （座標は snapshot から取得）

  3. 失敗した場合: screenshot を取得してユーザーに提示

検証（screenshot で確認）:
  - Audio Overview パネルが右側または中央に展開されていること
  - "Generate" ボタンが表示されていること

リトライ: 最大3回。3回失敗したら人間フォールバック。
```

### F1-3: Audio Overview を生成する

```
事前確認（screenshot で確認）:
  - ソースが1件以上登録されていること（"No sources" と表示されていないこと）
  - "Generating..." 等の進行中状態でないこと

操作（順に試す）:
  1. aria-label "Generate" のボタンを探す
     mcp__Claude_in_Chrome__find
       selector: 'button[aria-label*="Generate"], button[aria-label*="generate"]'

  2. テキスト "Generate" を持つボタンを探す（フォールバック）
     mcp__Claude_in_Chrome__get_page_text でページテキストを取得
     "Generate audio overview" のようなテキストの周辺要素を snapshot で特定

  3. クリック
     mcp__Claude_in_Chrome__form_input

検証（操作直後の screenshot）:
  - "Generating..." または進捗インジケーターが表示されること
  - エラーダイアログが出ていないこと

エラー "No sources":
  → ユーザーに「NotebookLM のソースにファイルが追加されているか確認してください」と案内
  → sources/ のファイルを NotebookLM に手動で追加する手順を提示

リトライ: 最大3回。
```

### F1-4: 生成完了を待つ

```
ポーリング戦略（最大10分、30秒ごとに確認）:

  ループ:
    1. screenshot を取得
    2. mcp__Claude_in_Chrome__get_page_text でページテキストを取得
    3. 以下のいずれかを検出:
       a. "Download" ボタンが出現 → 完了
       b. "Listen" ボタンが出現 → 完了
       c. 進捗インジケーターが消えた → 完了の可能性あり（screenshot 再確認）
       d. エラーメッセージが出現 → 失敗 → 人間フォールバック
    4. いずれも検出できない場合 → 30秒待ってリトライ

完了検出の優先順位:
  1. aria-label "Download" を持つボタン
     mcp__Claude_in_Chrome__find
       selector: 'button[aria-label*="Download"], a[aria-label*="Download"]'
  2. テキスト "Download" または "Listen" を含む要素
```

### F1-5: 音声をダウンロードする

```
操作:
  1. Download ボタンをクリック
     mcp__Claude_in_Chrome__form_input（セレクタ: 'button[aria-label*="Download"]'）

  2. ダウンロードが完了するまで待つ（通常5〜30秒）
     - ~/Downloads/ に .mp3 ファイルが出現することを確認
     - ファイルサイズが 0 でないことを確認

  3. ダウンロードされたファイルのパスを取得
     （Claude が ~/Downloads/ を確認）

検証:
  - .mp3 ファイルが存在し、サイズ > 0 であること
```

### F1-6: 音声を Drive にアップロードする

```
操作:
  drive_io.py を参照して Drive MCP を呼び出す:

  1. アップロード操作の生成:
     python scripts/drive_io.py upload \
       --type audio \
       --local ~/Downloads/{filename}.mp3 \
       --filename "YYYY-MM-DD_{topic}.mp3"

  2. 出力された JSON の mcp_tool と params を使って Drive MCP を呼び出す

  3. アップロード完了後、index.json の該当エントリを更新:
     - audio_path を記録
     - audio_ready: true を設定

完了報告:
  ユーザーに以下を伝える:
  - 音声ファイルのファイル名
  - Drive の保存パス
  - 再生方法（Google Drive アプリ or 共有リンク）
```

---

## F2: チャット質問フロー

### F2-1: チャット欄を開く

```
事前: F1-1 と同様に NotebookLM を開く

操作（順に試す）:
  1. aria-label "Chat" または "Ask a question" の入力欄を探す
     mcp__Claude_in_Chrome__find
       selector: 'textarea[aria-label*="Chat"], textarea[aria-label*="Ask"], textarea[placeholder*="Ask"]'

  2. 見つかった textarea をクリックしてフォーカス
     mcp__Claude_in_Chrome__form_input
       selector: 上記のセレクタ
       value: "" （クリックのみ）

検証（screenshot）:
  - テキスト入力欄にカーソルが当たっていること
```

### F2-2: 質問を入力する

```
操作:
  mcp__Claude_in_Chrome__form_input
    selector: 'textarea[aria-label*="Chat"], textarea[aria-label*="Ask"]'
    value: "{ユーザーの質問テキスト}"

  送信ボタンをクリック（または Enter キー）:
    mcp__Claude_in_Chrome__find で送信ボタンを探す
      selector: 'button[aria-label*="Send"], button[type="submit"]'
    クリック

検証（screenshot）:
  - 質問テキストがチャット欄に表示されていること
  - 回答生成中のスピナーが表示されること
```

### F2-3: 回答を取得する

```
ポーリング（最大3分、10秒ごと）:
  1. screenshot を取得
  2. mcp__Claude_in_Chrome__get_page_text でページテキストを取得
  3. 回答欄に新しいテキストが出現したことを確認
     （スピナーが消え、質問より後にテキストが存在する）

回答テキストの抽出:
  mcp__Claude_in_Chrome__read_page でページ構造を取得
  または get_page_text で全文取得し、質問より後の部分を抽出

ユーザーへの返答:
  取得した回答テキストをそのまま提示
  引用ソースが表示されている場合は合わせて提示

エラー処理:
  - 3分待っても回答が来ない → screenshot を提示してユーザーに確認依頼
  - 「Sources not found」等のエラー → ソース登録を促す
```

---

## エラーハンドリング総則

### リトライポリシー

| ステップ | 最大リトライ | 間隔 | 失敗時 |
|---------|------------|------|--------|
| navigate | 3回 | 5秒 | human_fallback |
| ボタン探索 | 3回 | 3秒 | 第2層セレクタに切り替え |
| ダウンロード | 3回 | 10秒 | human_fallback |
| 音声生成待ち | - | 30秒 | 10分でタイムアウト → human_fallback |
| チャット回答待ち | - | 10秒 | 3分でタイムアウト → human_fallback |

### 人間フォールバック（human_fallback）メッセージテンプレート

```
❗ 自動操作が失敗しました。以下を手動で行ってください：

[具体的な操作手順]

完了したら「続けて」と入力してください。
```

### ログ記録

各 F1/F2 フローの実行結果を以下の形式で記録（Notion or ローカルファイル）:

```json
{
  "timestamp": "YYYY-MM-DDThh:mm:ss",
  "flow": "F1" | "F2",
  "notebook_id": "...",
  "status": "success" | "failure" | "human_fallback",
  "error": null | "エラーメッセージ",
  "audio_path": "outputs/audio/YYYY-MM-DD_topic.mp3" | null
}
```
