# EventBot - Quick Deployment Script (Windows)
# =============================================
# Jalankan: .\deploy.ps1

Write-Host "🚀 EventBot Deployment Preparation" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Check if git is installed
try {
    $null = git --version
} catch {
    Write-Host "❌ Git tidak ditemukan. Install git terlebih dahulu." -ForegroundColor Red
    exit 1
}

# Check current branch
$branch = git branch --show-current
Write-Host "📍 Current branch: $branch" -ForegroundColor Yellow

# Add all changes
Write-Host "📦 Menambahkan perubahan..." -ForegroundColor Green
git add .

# Show status
Write-Host ""
Write-Host "📊 Status file:" -ForegroundColor Cyan
git status --short

# Commit
Write-Host ""
$commitMsg = Read-Host "💬 Commit message (Enter untuk default)"
if ([string]::IsNullOrWhiteSpace($commitMsg)) {
    $commitMsg = "Prepare for deployment"
}

git commit -m $commitMsg

# Push
Write-Host ""
Write-Host "⬆️ Pushing ke GitHub..." -ForegroundColor Yellow
git push origin $branch

Write-Host ""
Write-Host "✅ Code berhasil di-push!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Langkah selanjutnya:" -ForegroundColor Cyan
Write-Host "   1. Deploy database: https://neon.tech"
Write-Host "   2. Deploy backend: https://railway.app"
Write-Host "   3. Deploy frontend: https://share.streamlit.io"
Write-Host ""
Write-Host "📖 Dokumentasi lengkap: DEPLOYMENT_GUIDE.md" -ForegroundColor Magenta
Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
