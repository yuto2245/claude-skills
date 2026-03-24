#!/bin/bash
set -e

echo "=== Claude Skills GitHub Setup ==="

# GitHub認証チェック
if ! gh auth status &>/dev/null; then
  echo "❌ GitHub未認証。先に 'gh auth login' を実行してください。"
  exit 1
fi

GH_USER=$(gh api user --jq .login)
echo "✅ GitHubユーザー: $GH_USER"

# リポジトリ作成（既存なら skip）
if gh repo view "$GH_USER/claude-skills" &>/dev/null; then
  echo "ℹ️  リポジトリは既に存在します: github.com/$GH_USER/claude-skills"
else
  gh repo create claude-skills --public --description "Claude Cowork & claude.ai カスタムスキル管理リポジトリ"
  echo "✅ リポジトリ作成: github.com/$GH_USER/claude-skills"
fi

# Gitセットアップ
cd "$(dirname "$0")"

if [ ! -d .git ]; then
  git init
  git branch -M main
fi

git add -A
git commit -m "Initial commit: Add all Claude custom skills (19 skills)" || echo "Nothing to commit"

# リモート設定
if git remote get-url origin &>/dev/null; then
  git remote set-url origin "https://github.com/$GH_USER/claude-skills.git"
else
  git remote add origin "https://github.com/$GH_USER/claude-skills.git"
fi

git push -u origin main

echo ""
echo "🎉 完了！"
echo "リポジトリURL: https://github.com/$GH_USER/claude-skills"
