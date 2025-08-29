#launch_dashboard.bat

@echo off
echo 🔒 Agent 4: Competitor Analysis Dashboard
echo ================================================
echo.
echo Starting Streamlit dashboard...
echo.
echo Dashboard will open at: http://localhost:8501
echo Press Ctrl+C to stop the dashboard
echo.
pause
uv run streamlit run dashboard.py --server.port 8501
pause





