#run_dasshboard.py

#!/usr/bin/env python3
"""
Launcher script for Agent 4 Dashboard

This script launches the Streamlit dashboard for competitor analysis.
It can be run directly or used to start the dashboard with custom settings.
"""

import subprocess
import sys
import os
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import streamlit
        import plotly
        import pandas
        print("✅ All dashboard dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("💡 Install dependencies with: uv add streamlit plotly pandas")
        return False

def check_data_file():
    """Check if competitor comparison data exists"""
    data_path = Path(__file__).resolve().parents[1] / "data" / "outbound" / "competitor_comparison_result.json"
    
    if data_path.exists():
        print(f"✅ Data file found: {data_path}")
        return True
    else:
        print(f"❌ Data file not found: {data_path}")
        print("💡 Run Agent 4 first to generate data:")
        print("   uv run python -m Competitor_Comparison_Agent.agent4.main")
        return False

def launch_dashboard(port=8501, host="localhost"):
    """Launch the Streamlit dashboard"""
    dashboard_path = Path(__file__).parent / "dashboard.py"
    
    if not dashboard_path.exists():
        print(f"❌ Dashboard file not found: {dashboard_path}")
        return False
    
    print(f"🚀 Launching dashboard on http://{host}:{port}")
    print("💡 Press Ctrl+C to stop the dashboard")
    
    try:
        # Launch Streamlit
        cmd = [
            sys.executable, "-m", "streamlit", "run",
            str(dashboard_path),
            "--server.port", str(port),
            "--server.address", host,
            "--server.headless", "false"
        ]
        
        subprocess.run(cmd, check=True)
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to launch dashboard: {e}")
        return False
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped by user")
        return True

def main():
    """Main launcher function"""
    print("🔒 Agent 4: Competitor Analysis Dashboard Launcher")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        return False
    
    # Check data file
    if not check_data_file():
        print("\n⚠️ Dashboard can still be launched, but will show no data")
        response = input("Continue anyway? (y/N): ").lower().strip()
        if response != 'y':
            return False
    
    print("\n🎯 Dashboard Configuration:")
    print("   - Port: 8501 (default)")
    print("   - Host: localhost")
    print("   - URL: http://localhost:8501")
    
    # Ask for custom configuration
    custom_port = input("\nEnter custom port (press Enter for default 8501): ").strip()
    port = int(custom_port) if custom_port.isdigit() else 8501
    
    custom_host = input("Enter custom host (press Enter for localhost): ").strip()
    host = custom_host if custom_host else "localhost"
    
    print(f"\n🚀 Starting dashboard with configuration:")
    print(f"   - Port: {port}")
    print(f"   - Host: {host}")
    print(f"   - URL: http://{host}:{port}")
    
    # Launch dashboard
    return launch_dashboard(port, host)

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Launcher stopped by user")
        sys.exit(0)





