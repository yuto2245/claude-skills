---
name: eyecatch-maker
description: >
  アップロードされた画像（ロゴ・アイコン等）を使って、ブログ用OGPアイキャッチ画像（1200×630px）を生成するスキル。
  以下のような言葉が出たら積極的に使うこと:
  - 「アイキャッチ画像にして」「OGP画像を作って」「ブログの画像を作って」
  - 「この画像をアイキャッチに」「サムネイル画像にして」
  - 「ロゴをアイキャッチにして」「画像をOGPサイズにして」
  - 「1200x630にして」「SNSシェア用の画像にして」
  画像がアップロードされていてアイキャッチ・OGP・ブログ・サムネイルという言葉が出たら必ずこのスキルを使うこと。
---

# Eyecatch Maker

アップロードされた画像をOGP標準サイズ（1200×630px）のアイキャッチ画像に変換する。

## 前提

- 入力: ユーザーがアップロードした画像（ロゴ・アイコン・イラスト等）
- 出力: 1200×630px のアイキャッチ画像（PNG）
- ツール: Python + Pillow（`pip install Pillow --break-system-packages`）

## ユーザーへの確認事項

スキル実行前に、以下が未指定であれば確認する（1回のメッセージでまとめて聞く）：

| 項目 | デフォルト | 選択肢 |
|------|-----------|--------|
| 背景色 | 白 (#FFFFFF) | 白 / 黒 / カスタムカラー |
| ロゴサイズ | キャンバスの短辺の60% | 自由指定も可 |
| テキスト | なし | タイトル等を追加することも可 |

ユーザーが「シンプルに」「そのまま」と言っている場合はデフォルトで即実行する。

## 実装手順

### Step 1: 画像ファイルの確認

```python
import os
# アップロードファイルは /mnt/user-data/uploads/ に存在する
upload_dir = "/mnt/user-data/uploads/"
files = os.listdir(upload_dir)
# 画像ファイル（png, jpg, jpeg, webp, svg）を探す
```

### Step 2: 基本実装（白背景・センタリング）

```python
from PIL import Image, ImageOps

W, H = 1200, 630

# 背景作成
bg_color = (255, 255, 255)  # 白。黒なら (0, 0, 0)
img = Image.new("RGB", (W, H), bg_color)

# ロゴ読み込み・リサイズ
logo = Image.open("/mnt/user-data/uploads/<filename>").convert("RGBA")

# ロゴサイズ決定: 短辺（630）の60% = 378px を基準に縦横比維持
max_size = int(H * 0.60)  # = 378
logo.thumbnail((max_size, max_size), Image.LANCZOS)

# センタリング
lw, lh = logo.size
x = (W - lw) // 2
y = (H - lh) // 2

# 貼り付け（RGBA対応: アルファチャンネルをマスクとして使用）
img.paste(logo, (x, y), logo)

# 保存
img.save("/mnt/user-data/outputs/eyecatch.png")
```

### Step 3: 黒背景の場合の追加処理

黒背景のとき、ロゴが黒・ダーク系の場合は白に反転する：

```python
from PIL import ImageOps

r, g, b, a = logo.split()
rgb = Image.merge("RGB", (r, g, b))
inverted = ImageOps.invert(rgb)
gray = inverted.convert("L")

white_logo = Image.new("RGBA", logo.size, (0, 0, 0, 0))
pixels = white_logo.load()
for px in range(logo.size[0]):
    for py in range(logo.size[1]):
        val = gray.getpixel((px, py))
        if val > 20:
            pixels[px, py] = (255, 255, 255, min(255, val + 15))

logo = white_logo
```

### Step 4: ファイル出力・軽量化

```python
# PNG（ロスレス・透過対応）
img.save("/mnt/user-data/outputs/eyecatch.png", optimize=True)

# JPEG（さらに軽量・透過不要の場合）
img.convert("RGB").save("/mnt/user-data/outputs/eyecatch.jpg", quality=85, optimize=True)
```

## ファイルサイズの目安

| 形式 | 特徴 | 用途 |
|------|------|------|
| PNG | ロスレス・透過対応 | 文字・ロゴが鮮明 |
| JPEG | 最軽量・圧縮あり | 写真系・容量優先 |
| WebP | 軽量・透過対応 | モダンブログ推奨 |

## 完了後

1. `present_files` ツールでファイルをユーザーに渡す
2. ファイルサイズを伝える（`ls -lh` で確認）
3. 「フォーマットを変えたい場合はお知らせください」と添える

