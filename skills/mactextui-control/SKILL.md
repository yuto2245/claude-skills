---
name: mactextui-control
description: >
  MacのネイティブアプリをAppleScript・AXアクセシビリティAPIで操作するスキル。
  以下のような言葉が出たら積極的に使うこと:
  - 「〇〇を開いて」「〇〇アプリを起動して」「アプリを切り替えて」
  - 「Safariで〇〇を開いて」「このURLをSafariで表示して」
  - 「音楽をかけて」「次の曲に」「Musicを操作して」「再生して/止めて」
  - 「クリックして」「ボタンを押して」「入力して」
  - 「ウィンドウの要素を取得して」「UIツリーを見て」
  ブラウザ操作でSafariが対象の場合は Chrome MCP ではなくこのスキルを使うこと。
---

# mactextui-control スキル

MacのネイティブアプリをMCPツール経由でテキストベースに操作する。
スクリーンショット不要・ピクセル座標不要で、AXツリーとAppleScriptを使って確実に操作する。

## 利用できるツール

| ツール | 用途 |
|---|---|
| get_app_list | 起動中のアプリ一覧を取得 |
| focus_app | 指定アプリを前面に表示（未起動なら起動も行う） |
| get_ui_tree | アプリのUI要素ツリーを取得（ボタン・フィールドの座標含む） |
| find_element | ラベル名でUI要素を検索して座標を返す |
| perform_action | クリック・入力・キー操作・AppleScript実行 |

## 基本の操作パターン

### 1. アプリを起動・前面表示する
focus_app(app_name="Safari")
focus_app(app_name="ミュージック")
まず get_app_list で起動状態を確認してから focus_app を呼ぶと確実。

### 2. SafariでURLを開く
Chrome MCPは使わない。AppleScriptで直接Safariを操作する。
perform_action(action="applescript", text="tell application 'Safari'
activate
open location 'https://example.com'
end tell")

### 3. UI要素をクリックする
find_element(label="送信", app_name="Safari")
perform_action(action="click", x=100, y=200)

### 4. テキストを入力する
perform_action(action="click", x=入力欄のx, y=入力欄のy)
perform_action(action="type", text="入力したい文字")

### 5. キーボードショートカット
perform_action(action="key", key="cmd+c")
perform_action(action="key", key="return")
perform_action(action="key", key="escape")

## Musicアプリの操作

### プレイリスト一覧を取得
perform_action(action="applescript", text="tell application 'Music'
return name of every playlist as list
end tell")

### 再生開始（プレイリスト指定）
perform_action(action="applescript", text="tell application 'Music'
activate
play playlist 'お気に入りの曲'
delay 1
return (name of current track) & ' - ' & (artist of current track)
end tell")

### 再生コントロール
perform_action(action="applescript", app_name="Music", text="next track")
perform_action(action="applescript", app_name="Music", text="previous track")
perform_action(action="applescript", app_name="Music", text="stop")
perform_action(action="applescript", app_name="Music", text="playpause")

## よくあるエラーと対処

| エラー | 原因 | 対処 |
|---|---|---|
| App not found | アプリ未起動 or 名前違い | get_app_list で正式名を確認してから再試行 |
| Accessibility permission required | アクセシビリティ権限なし | AppleScript に切り替える |
| player state is stopped | Musicにトラックなし | playlist を明示して play する |
| Chrome MCP を使ってしまった | Safariが対象なのに間違えた | AppleScript の open location で Safari に直接URLを渡す |

## 使い分けの判断

- Safari/ネイティブアプリ操作 → このスキル（perform_action + AppleScript）
- Chromeの特定タブを操作 → Chrome MCP（mcp__Claude_in_Chrome__*）
- ファイル操作・コード実行 → Bash / Read / Write ツール

## AppleScript 実行のコツ

perform_action(action="applescript", app_name="アプリ名", text="コマンド") と書くと、
自動的に tell application "アプリ名" ... end tell でラップして実行される。
アプリをまたぐ処理は app_name を省略してフルのAppleScriptを text に書く。
