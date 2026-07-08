#!/bin/bash
# EventBot - Quick Deployment Script
# ===================================
# Script ini mempersiapkan deployment ke cloud

echo "🚀 EventBot Deployment Preparation"
echo "===================================="
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git tidak ditemukan. Install git terlebih dahulu."
    exit 1
fi

# Check if on main branch
BRANCH=$(git branch --show-current)
echo "📍 Current branch: $BRANCH"

# Add all changes
echo "📦 Menambahkan perubahan..."
git add .

# Show status
echo ""
echo "📊 Status file:"
git status --short

# Commit
echo ""
read -p "💬 Commit message: " COMMIT_MSG
if [ -z "$COMMIT_MSG" ]; then
    COMMIT_MSG="Prepare for deployment"
fi

git commit -m "$COMMIT_MSG"

# Push
echo ""
echo "⬆️ Pushing ke GitHub..."
git push origin $BRANCH

echo ""
echo "✅ Code berhasil di-push!"
echo ""
echo "📋 Langkah selanjutnya:"
echo "   1. Deploy database: https://neon.tech"
echo "   2. Deploy backend: https://railway.app"
echo "   3. Deploy frontend: https://share.streamlit.io"
echo ""
echo "📖 Dokumentasi lengkap: DEPLOYMENT_GUIDE.md"
