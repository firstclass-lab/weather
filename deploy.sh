#!/bin/bash

# 1. Pythonを実行してHTMLを生成
python weather.py

# 2. GitHubにアップロード
git add .
git commit -m "Update weather site: $(date '+%Y-%m-%d %H:%M:%S')"
git push origin main --force

echo "---------------------------------------"
echo "デプロイが完了しました！"