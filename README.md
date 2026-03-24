# claude-skills

Claude Cowork & claude.ai カスタムスキル管理リポジトリ

## 目的

Cowork と claude.ai の両環境でスキルを同期管理するための Single Source of Truth（唯一の正）。

## スキル一覧（19個）

| スキル名 | 説明 |
|---|---|
| brand-guidelines | Anthropic ブランドカラー・タイポグラフィの適用 |
| canvas-design | ビジュアルアート・ポスター・デザイン生成 |
| career-consultant | キャリア相談・転職支援・経済分析 |
| chat-summarizer | チャット引き継ぎ・概要作成 |
| docx | Word文書の作成・編集 |
| eyecatch-maker | ブログ用OGPアイキャッチ画像生成（1200×630px） |
| mcp-builder | MCPサーバー構築ガイド |
| mentoring-harness-teaching-style-absorber | ジュニアエンジニア向けメンタリング |
| notion-sync | 会話内容をNotionに保存・呼び出し |
| pdf | PDF作成・編集・テキスト抽出 |
| pptx | PowerPointスライド作成・編集 |
| question-analyzer | 質問の構造分析と改善提案 |
| quiz-maker | 選択式クイズ作成・出題 |
| review-scheduler | エビングハウス忘却曲線に基づく復習スケジューラ |
| schedule | 定期タスク作成 |
| skill-creator | 新規スキルの作成・最適化 |
| skill-updater | 既存スキルのアップデート |
| web-artifacts-builder | React/Tailwind/shadcn WebアーティファクトBuilder |
| xlsx | Excel スプレッドシート作成・編集・分析 |

## ディレクトリ構造

```
claude-skills/
└── skills/
    ├── <スキル名>/
    │   └── SKILL.md
    └── ...
```

## 同期方法

### Cowork → GitHub
```bash
cd ~/claude-skills
git add -A
git commit -m "Update skills"
git push origin main
```

### GitHub → Cowork（スキルフォルダへ反映）
```bash
cd ~/claude-skills
git pull origin main
# Finderで確認できるCoworkのスキルフォルダにコピー
```
