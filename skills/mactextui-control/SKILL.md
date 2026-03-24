---
name: mactextui-control
description: |
  macOSアプリをスクリーンショット不要・低トークンで操作するスキル。
  mactextui-control MCPが接続されているときに使う。

  以下の言葉が出たら積極的に使うこと:
  - 「〇〇アプリを開いて」「〇〇を操作して」「〇〇を再生/停止して」
  - 「音楽を再生して」「次の曲」「音量を上げて/下げて」「一時停止」「今の曲は？」
  - 「Safariで〇〇を開いて」「新しいタブ」「URLを開いて」
  - 「メモに書いて」「メモを作って」「カレンダーの予定」
  - 「Finderで開いて」「フォルダを開いて」
  - 「LINEを開いて」「Obsidianを開いて」
  - 「アプリのボタンをクリックして」「テキストを入力して」
  - 「Macの〇〇アプリで〇〇して」「ウィンドウの〇〇を押して」
  - computer-useがポリシーでブロックされたアプリの操作
  - computer-useよりトークンを節約したい操作全般

  computer-useのスクリーンショット（約6,000 tokens/枚）を使わず、
  テキストベースのAX APIとAppleScriptで操作するため大幅にトークンを節約できる。
---

# mactextui-control 操作ガイド

## 原理：なぜこのツールが存在するか

macOSアプリを操作するには通常2つの方法がある：

1. **computer-use（スクリーンショット方式）**: 画面を撮影→画像解析→座標クリック。毎回約6,000トークン消費。ポリシーでブロックされるアプリもある（例: ミュージック）。
2. **mactextui-control（テキストAPI方式）**: macOS Accessibility APIとAppleScript辞書を使い、テキストベースでUI構造を取得・操作する。50〜800トークン/回。ポリシー制限なし。

つまり「目で見て操作する」のではなく「アプリに直接話しかける」方式。

## ツール一覧と使い分け

| ツール | 用途 | トークン消費 |
|---|---|---|
| `perform_action (applescript)` | アプリへの直接命令（再生・停止・保存・情報取得など） | ◎ 最軽量 |
| `find_element` | ボタン名で座標を検索してクリック | ○ 軽量 |
| `focus_app` | アプリを前面に出す | ○ 軽量 |
| `get_app_list` | 起動中アプリ一覧の確認 | ○ 軽量 |
| `get_ui_tree` | アプリのUI要素全体を取得 | △ アプリ次第で重い |

## 操作の原則：applescriptを最優先にする

**フォーカス不要・サンドボックス対応・最軽量**のため、まず `applescript` アクションで試みること。

```
# 例: Musicを再生
perform_action(action="applescript", app_name="Music", text="play")

# 例: Musicを一時停止
perform_action(action="applescript", app_name="Music", text="pause")

# 例: Safariで新しいタブを開く
perform_action(action="applescript", app_name="Safari", text="make new document")
```

### なぜapplescriptが優先なのか

macOSのアプリには2種類の操作経路がある：

1. **System Events経由（AX API）** — ボタンのクリックやキー送信。フォーカスが必要で、Musicのようなサンドボックスアプリでは使えない場合がある
2. **AppleScript辞書コマンド** — アプリに直接話しかける方式。フォーカス不要で、サンドボックスアプリにも届く

`tell application "Music" to play` は、Musicが画面に出ていなくても、他のアプリがフォーカスを持っていても動作する。

## computer-useとの使い分け判断フロー

```
ユーザーがアプリ操作を要求
  │
  ├─ AppleScriptコマンドで実現できる？
  │    YES → perform_action(applescript) を使う【最優先】
  │
  ├─ ボタン名/ラベルが分かっている？
  │    YES → find_element → perform_action(click) を使う
  │
  ├─ UIの構造把握が必要？
  │    YES → get_ui_tree → 対象特定 → click
  │
  ├─ 上記すべて失敗 or 視覚的な位置確認が必要？
  │    → computer-use のスクリーンショット+クリックにフォールバック
  │
  └─ computer-useもポリシーでブロック？
       → ユーザーに手動操作を案内
```

**computer-useを使うべきケース:**
- 画像・動画の視覚的な確認が必要なとき
- ドラッグ&ドロップ操作
- アプリのUI構造が複雑でfind_elementでは特定できないとき
- Webブラウザ内のDOM操作（→ Chrome MCPが適切）

**mactextui-controlを使うべきケース:**
- アプリへの命令（再生、保存、開く、閉じるなど）
- 情報取得（今の曲名、ウィンドウタイトルなど）
- computer-useがポリシーでブロックされたアプリ
- 繰り返し操作でトークンを節約したいとき

## 情報取得パターン（read系）

applescriptは操作だけでなく、アプリから情報を取得することもできる。
返り値は `detail` フィールドに入る。

```python
# 今再生中の曲名
perform_action(action="applescript", app_name="Music", text="get name of current track")
# → {"status": "ok", "detail": "Aperture"}

# 今再生中の曲のアーティスト
perform_action(action="applescript", app_name="Music", text="get artist of current track")

# Musicの再生状態
perform_action(action="applescript", app_name="Music", text="get player state")
# → "playing" or "paused" or "stopped"

# Safariの現在のURL
perform_action(action="applescript", app_name="Safari", text="get URL of current tab of front window")

# Safariの現在のページタイトル
perform_action(action="applescript", app_name="Safari", text="get name of front window")

# Finderの最前面フォルダのパス
perform_action(action="applescript", app_name="Finder", text="get POSIX path of (target of front Finder window as alias)")
```

## UIクリックが必要な場合（find_element → click）

ボタンのクリックなどAppleScriptコマンドがない操作には `find_element` で座標を取得してクリックする。

```python
# 1. ボタンの座標を探す
find_element(label="送信", app_name="Mail")
# → {"found": 1, "elements": [{"label": "送信", "coords": {"x": 450, "y": 300}}]}

# 2. 座標をクリック
perform_action(action="click", x=450, y=300)
```

## キー操作（app_name指定で確実に届ける）

`app_name` を指定すると、フォーカスの問題を回避して特定アプリにキーを送れる。

```python
# 例: FinderでCmd+Sを送る
perform_action(action="key", key="command+s", app_name="Finder")
```

**注意**: `app_name` なしの `key` アクションは、実行時点でフォーカスしているアプリに届く。
ClaudeのチャットUIとMCPが交互に動作するため、意図しないアプリに届くことがある。
→ **常に app_name を指定すること。**

## サンドボックスアプリの制限

Music・App Store・写真など、Appleのサンドボックスアプリは `get_ui_tree` / `find_element` が動作しない場合がある。
`System Events` のプロセス一覧に現れないためで、`get_app_list` では見えるのに `get_ui_tree` が "Process not found" になる。

→ **解決策**: `applescript` アクションでアプリの辞書コマンドを直接呼ぶ。

## エラーが出たときの対応

| エラーメッセージ | 原因 | 対応 |
|---|---|---|
| `osascript にはキー操作の送信は許可されません (1002)` | オートメーション権限が未付与 | システム設定 → プライバシーとセキュリティ → オートメーション → osascript の System Events を ON |
| `Process not found` | サンドボックスアプリでAX APIが使えない | `applescript` アクションに切り替える |
| `App not found: ○○` | アプリ名が間違っている or 未起動 | `get_app_list` で正確な名前を確認。日本語名（ミュージック）と英語名（Music）両方試す |
| `Connection refused` / タイムアウト | MCPサーバーが停止 | Claude Desktopを再起動 |
| `command not found` (applescript) | そのアプリにそのコマンドがない | WebSearchでAppleScript辞書を調べるか、`find_element + click` に切り替え |

## 権限の前提条件

このMCPが動作するには以下の権限が必要：

- **システム設定 → プライバシーとセキュリティ → アクセシビリティ**
  - `osascript`: ON
  - `Claude`: ON
- **システム設定 → プライバシーとセキュリティ → オートメーション**
  - `osascript` → `System Events`: ON

## トークン節約のコツ

- `get_ui_tree` は最後の手段にする（複雑なアプリでは数千トークン消費する可能性がある）
- `find_element` は `get_ui_tree` より軽い（対象ラベルにマッチした要素だけ返す）
- applescriptコマンドが分からないときは、まずアプリ名+コマンドで試す（`play`, `pause`, `next track`, `activate` など）
- 不明なコマンドはWebSearchや `tell application "AppName" to get properties` で調べられる
- 同じアプリへの連続操作は1回ずつ確認せず、まとめて実行する

## よく使うapplescriptコマンド集

### Music（ミュージック）
```applescript
play                          # 再生
pause                         # 一時停止
playpause                     # 再生/一時停止トグル
next track                    # 次の曲
previous track                # 前の曲
set sound volume to 50        # 音量（0〜100）
get name of current track     # 現在の曲名
get artist of current track   # アーティスト名
get album of current track    # アルバム名
get duration of current track # 曲の長さ（秒）
get player position           # 再生位置（秒）
get player state              # 再生状態
play playlist "名前"          # プレイリスト再生
get name of every playlist    # プレイリスト一覧
```

### Safari
```applescript
open location "https://example.com"                    # URLを開く
make new document                                      # 新しいウィンドウ
get URL of current tab of front window                 # 現在のURL
get name of front window                               # ページタイトル
get name of every tab of front window                  # 全タブのタイトル
set URL of current tab of front window to "https://…"  # タブのURL変更
do JavaScript "document.title" in current tab of front window  # JS実行
```

### Finder
```applescript
open POSIX file "/Users/me/Downloads"          # フォルダを開く
get POSIX path of (target of front Finder window as alias)  # 現在のパス
get name of every item of (target of front Finder window)   # ファイル一覧
make new Finder window                         # 新しいウィンドウ
reveal POSIX file "/path/to/file"              # ファイルを表示
```

### メモ（Notes）
```applescript
make new note at folder "メモ" with properties {name:"タイトル", body:"内容"}
get name of every note                         # ノート一覧
get body of note "タイトル"                     # ノート内容を取得
```

### カレンダー（Calendar）
```applescript
get name of every calendar                     # カレンダー一覧
get summary of every event of calendar "個人"   # イベント一覧
```

### 共通
```applescript
activate        # フォーカスを当てる（前面に出す）
quit            # 終了
get name of every window  # ウィンドウ一覧
```

### システム操作（System Events経由ではなくshellコマンド）
```
# 音量操作はapplescriptではなくshellで:
# osascript -e "set volume output volume 50"
# → perform_action(action="applescript", text="set volume output volume 50") で直接実行可
```
