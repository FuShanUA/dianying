#!/bin/bash
# 🎬 Movie Database Revival One-Click Sync Tool
# Resides at: /Users/shanfu/cc/Projects/movie-database-revival/sync_to_cloud.sh

PROJECT_DIR="/Users/shanfu/cc/Projects/movie-database-revival"
cd "$PROJECT_DIR" || exit 1

echo "=================================================="
echo "🚀 [1/3] Uploading new posters to Google Drive..."
echo "=================================================="
/Users/shanfu/cc/.venv/bin/python sync_covers.py

echo ""
echo "=================================================="
echo "📦 [2/3] Staging metadata database & Drive maps..."
echo "=================================================="
git add movies.db covers_gdrive.json

echo ""
echo "=================================================="
echo "☁️ [3/3] Committing & pushing to GitHub Cloud..."
echo "=================================================="
# Auto-generate timestamped commit message
COMMIT_MSG="data: update movies metadata and covers map ($(date '+%Y-%m-%d %H:%M:%S'))"
git commit -m "$COMMIT_MSG"

echo ""
echo "📤 Pushing upstream to trigger cloud auto-rebuild..."
git push origin main

echo ""
echo "=================================================="
echo "🎉 SUCCESS: Synchronization completed perfectly!"
echo "=================================================="
