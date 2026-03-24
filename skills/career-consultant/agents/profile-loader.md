# Profile Loader Agent

ユーザーのGoogle SpreadsheetからCSV形式の経歴・ナレッジデータを取得し、
後続エージェントが使いやすい形に整形して保存する。

## 役割

毎回リアルタイムでSpreadsheetを読み込むことで、常に最新の経歴・スキル情報を使う。
ダウンロードは不要。公開URLから直接取得する。

## 入力パラメータ

- **spreadsheet_url**: Google SpreadsheetのエクスポートURL
  - 形式: `https://docs.google.com/spreadsheets/d/{ID}/export?format=csv&gid={SHEET_ID}`
- **output_path**: 結果を保存するJSONファイルパス（例: `/tmp/yuto_profile.json`）

## 処理手順

### Step 1: CSVを取得する

`scripts/fetch_profile.py` を実行してSpreadsheetからCSVを取得する。

```bash
python3 /path/to/career-consultant/scripts/fetch_profile.py \
  --url "{spreadsheet_url}" \
  --output "{output_path}"
```

スクリプトが失敗した場合（URLが未設定・アクセス拒否など）は、
エラーを `{output_path}.error` に書き込み、呼び出し元に失敗を報告する。

### Step 2: データを検証する

取得したJSONに以下のフィールドが含まれているか確認する：

- `経歴` または `career` : 職歴リスト
- `スキル` または `skills` : スキルリスト
- `資格` または `certifications` : 資格リスト
- `目標` または `goals` : キャリア目標

不足しているフィールドがあれば、空配列でパディングして後続処理を止めない。

### Step 3: 結果を保存する

```json
{
  "fetched_at": "2025-xx-xx HH:MM",
  "source_url": "...",
  "raw_csv_rows": [...],
  "parsed": {
    "career": [...],
    "skills": [...],
    "certifications": [...],
    "goals": [...],
    "notes": [...]
  }
}
```

## エラー時の挙動

CSVが取得できなかった場合、以下のフォールバックデータを使う：

```json
{
  "fetched_at": "fallback",
  "source_url": "unavailable",
  "parsed": {
    "career": [
      {"period": "2022-2024", "role": "SAPコンサルタント", "years": 2.5,
       "detail": "ECC→S/4HANAマイグレーション、FIモジュール、チームリーダー経験"},
      {"period": "2024-現在", "role": "バックエンドエンジニア", "years": 0.2,
       "detail": "PHP/Laravel、Vue.js、3層アーキテクチャ"}
    ],
    "skills": ["SAP S/4HANA", "PHP", "Laravel", "Vue.js", "Python", "SQL"],
    "certifications": ["基本情報技術者試験"],
    "goals": ["1年以内にSAP×エンジニアのハイブリッドコンサルとして転職"],
    "notes": ["25歳", "岡山在住", "東京への上京を検討中", "技術ブログ sapjp.net 月500PV"]
  }
}
```
