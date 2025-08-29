#launch_dashboard.ps1
# Agent 4: Competitor Analysis Dashboard Launcher
# PowerShell Script

Write-Host "🔒 Agent 4: Competitor Analysis Dashboard" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

# Check if data exists
$dataPath = "..\data\outbound\competitor_comparison_result.json"
if (Test-Path $dataPath) {
    Write-Host "✅ Data file found" -ForegroundColor Green
    $data = Get-Content $dataPath | ConvertFrom-Json
    $competitorCount = ($data.comparison.scores | Get-Member -MemberType NoteProperty).Count
    Write-Host "   - Competitors: $competitorCount" -ForegroundColor Green
} else {
    Write-Host "❌ Data file not found" -ForegroundColor Red
    Write-Host "💡 Run Agent 4 first: uv run python -m Competitor_Comparison_Agent.agent4.main" -ForegroundColor Yellow
    Write-Host ""
    $continue = Read-Host "Continue anyway? (y/N)"
    if ($continue -ne "y") {
        exit
    }
}

Write-Host ""
Write-Host "🚀 Starting Streamlit dashboard..." -ForegroundColor Green
Write-Host ""
Write-Host "Dashboard will open at: http://localhost:8501" -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop the dashboard" -ForegroundColor Yellow
Write-Host ""

# Launch dashboard
try {
    uv run streamlit run dashboard.py --server.port 8501
} catch {
    Write-Host "❌ Error launching dashboard: $_" -ForegroundColor Red
    Write-Host "💡 Make sure all dependencies are installed: uv add streamlit plotly pandas" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Dashboard stopped" -ForegroundColor Cyan
Read-Host "Press Enter to exit"





