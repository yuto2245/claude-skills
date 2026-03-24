---
name: skill-updater
description: |
  既存のClaudeスキルをベストプラクティス・最新情報に基づいて継続的にアップデートするスキル。
  ユーザーが手動で「このスキルを更新して」「最新化して」「見直して」と指示したときに使う。

  Use this skill when the user says things like:
  - "このスキルを最新化して" / "update this skill"
  - "ベストプラクティスに合わせてスキルを更新して"
  - "〇〇のバージョンが上がったのでスキルを直して"
  - "スキルをレビューして改善点を教えて"
  - "skill を見直して"

  Always use this skill when the user explicitly asks to review, refresh, or improve an existing skill file.
---

# Skill Updater

ユーザーの手動指示を起点に、既存スキルをベストプラクティス・最新情報へアップデートするスキル。

---

## 原理：なぜスキルは陳腐化するのか

スキル（SKILL.md）は「Claudeへの指示書」であり、以下3つの理由で陳腐化する：

1. **技術の進化** — ライブラリのAPI変更、非推奨メソッド、新バージョンのリリース
2. **ベストプラクティスの更新** — コミュニティが発見した改善パターンの普及
3. **ユースケースの拡張** — 新しいエッジケースや追加要件の発生

このスキルはその3つを体系的に検出し、差分を提示してから修正する。

---

## ワークフロー

### Step 1: 対象スキルを読み込む

ユーザーが指定したスキルのSKILL.mdを読み込み、以下を把握する：

```bash
# 指定されている場合
view /mnt/skills/user/<skill-name>/SKILL.md

# どのスキルか不明な場合はリストアップして確認
ls /mnt/skills/user/
ls /mnt/skills/examples/
```

読み込み後に抽出する情報：

| 項目 | 抽出例 |
|------|--------|
| 依存ライブラリ | `python-pptx==0.6.21`, `openpyxl` など |
| 使用APIやメソッド | `Presentation()`, `add_slide()` など |
| pip/npmコマンド | `pip install python-pptx --break-system-packages` |
| バージョン固定の有無 | バージョンが明記されているかどうか |

### Step 2: 情報収集（3つの情報源を並行活用）

抽出した依存ライブラリ・ツールについて、以下の3つの情報源から最新情報を取得する。

#### 情報源 A: 既存スキル内のコードを静的解析

SKILL.md内のコードブロック・コマンド例を直接読み込み、陳腐化パターンを検出する：

- 古い pip オプション（`--user` が不要になったケース等）
- ハードコードされたバージョン番号
- 廃止予定が既に記述されていたAPI

#### 情報源 B: GitHubのChangelog / Release Notes

```
# 検索クエリ例
{library} github changelog latest release
{library} site:github.com releases
```

GitHubのReleasesページから破壊的変更（Breaking Changes）・非推奨（Deprecated）・新機能を確認する。

#### 情報源 C: Webサーチ（公式ドキュメント・技術ブログ）

```
# 検索クエリ例
{library} best practices 2025
{library} deprecated methods migration
{technology} official docs changelog
```

複数の観点を並行して調査し、変更が必要な箇所を特定する。
変更が**ない**場合もその旨を明確に伝える（「現時点で更新不要」も重要な結論）。

### Step 3: 差分を提示する（確認フェーズ）

調査結果を before/after 形式で提示し、ユーザーの承認を得る。

**提示フォーマット：**

```
## 更新提案サマリー

変更箇所: X件  
情報ソース: {URL1}, {URL2}

---

### 変更 1/X 🔴: {変更の概要}

**変更理由:** {なぜこの変更が必要か・技術的根拠}

**Before:**
{現在の記述}

**After:**
{更新後の記述}

---

### 変更 2/X 🟡: ...
```

提示後に必ず確認する：
> 「上記の変更を適用しますか？番号を指定して部分的に選ぶことも可能です（例：「1番と3番だけ」）」

### Step 4: 承認後に適用する

```bash
# /mnt/skills/ は読み取り専用のためコピーして作業
cp -r /mnt/skills/user/<skill-name>/ /tmp/<skill-name>/

# str_replace または file_create で /tmp/ 内のファイルを編集

# パッケージ化してユーザーに提示
cd /mnt/skills/examples/skill-creator
python -m scripts.package_skill /tmp/<skill-name>/ /mnt/user-data/outputs/
```

⚠️ **重要：** `/mnt/skills/` は読み取り専用。必ず `/tmp/` にコピーしてから編集すること。

---

## 優先度の付け方

変更提案には必ず優先度を付けて提示する：

- 🔴 **Critical** — セキュリティ脆弱性、動作不能になるAPI破壊的変更
- 🟡 **Recommended** — 非推奨メソッド、新しいベストプラクティスへの移行
- 🟢 **Optional** — マイナーな改善、記述の明確化、コードスタイル統一

提示時はCriticalから順に並べ、Optionalは最後にまとめる。

---

## カテゴリ別：調査の重点ポイント

### コード生成系スキル（docx, pptx, xlsx等）
- ライブラリのバージョン（python-docx, openpyxl, python-pptx等）
- `pip install` オプションの変更（`--break-system-packages` の要否など）
- APIシグネチャの変更（引数名・戻り値の型など）

### フロントエンド系スキル（React, Vue, Tailwind等）
- フレームワークのメジャーバージョン変更
- 廃止されたhooks / コンポーネントAPI
- 推奨パターンの変化（例：Vue3 Composition API、React Server Components）

### AI/LLM系スキル（Claude API, OpenAI等）
- モデル名の変更（例：`claude-3-opus` → `claude-opus-4`）
- APIパラメータの追加・廃止
- 新機能（tools, extended thinking等）の反映

### インフラ・DevOps系スキル
- CLIコマンドの変更
- 設定ファイルフォーマットの変化

---

## 注意事項

- スキルの**コア設計**（何をするか）は変更しない。変えるのは「どうやるか」の実装詳細のみ。
- **ユーザーの承認なしに自動で上書きしない**（Step 3の確認が必須）。
- 情報ソースのURLは必ず提示する（根拠のない更新はしない）。
- 複数スキルを一度に更新する場合は、スキルごとに順番に処理する。
