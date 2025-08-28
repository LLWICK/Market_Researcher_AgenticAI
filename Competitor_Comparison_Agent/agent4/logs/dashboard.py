#dashboard.py
#!/usr/bin/env python3
"""
Streamlit Dashboard for Agent 4: Competitor Comparison & Security

This dashboard visualizes the competitor comparison results and provides
interactive insights into the market analysis data.

To run:
    streamlit run dashboard.py
"""

import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from pathlib import Path
from datetime import datetime
import base64
from typing import Dict, Any, List

# Try to import configuration
try:
    from config import get_dashboard_config
    dashboard_config = get_dashboard_config()
    DASHBOARD_PORT = dashboard_config.port
    DASHBOARD_HOST = dashboard_config.host
    DASHBOARD_THEME = dashboard_config.theme
    DASHBOARD_LAYOUT = dashboard_config.layout
    DASHBOARD_SIDEBAR_STATE = dashboard_config.sidebar_state
except ImportError:
    # Fallback to defaults if config not available
    DASHBOARD_PORT = 8501
    DASHBOARD_HOST = "localhost"
    DASHBOARD_THEME = "light"
    DASHBOARD_LAYOUT = "wide"
    DASHBOARD_SIDEBAR_STATE = "expanded"

# Page configuration
st.set_page_config(
    page_title=f"Agent 4: Competitor Analysis Dashboard",
    page_icon="🔒",
    layout=DASHBOARD_LAYOUT,
    initial_sidebar_state=DASHBOARD_SIDEBAR_STATE
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        padding: 1rem;
        background: linear-gradient(90deg, #f0f2f6, #e1e5ea);
        border-radius: 10px;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin: 0.5rem 0;
    }
    .security-badge {
        background: #28a745;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .warning-badge {
        background: #ffc107;
        color: black;
        padding: 0.25rem 0.5rem;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .info-box {
        background: #f8f9fa;
        border-left: 4px solid #007bff;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

def load_comparison_data() -> Dict[str, Any]:
    """Load competitor comparison data from JSON file"""
    try:
        # Try to load from the outbound directory
        data_path = Path(__file__).resolve().parents[1] / "data" / "outbound" / "competitor_comparison_result.json"
        
        if not data_path.exists():
            st.error(f"❌ Data file not found at: {data_path}")
            st.info("💡 Make sure Agent 4 has been run to generate comparison data.")
            return {}
        
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        st.success(f"✅ Data loaded successfully from: {data_path}")
        return data
        
    except Exception as e:
        st.error(f"❌ Error loading data: {e}")
        return {}

def create_competitor_dataframe(data: Dict[str, Any]) -> pd.DataFrame:
    """Convert competitor data to pandas DataFrame"""
    if not data or 'comparison' not in data:
        return pd.DataFrame()
    
    comparison = data['comparison']
    scores = comparison.get('scores', {})
    ranking = comparison.get('ranking', [])
    
    if not scores or not ranking:
        return pd.DataFrame()
    
    # Create DataFrame
    df = pd.DataFrame([
        {
            'Competitor': comp,
            'Score': scores[comp],
            'Rank': rank + 1,
            'Score_Normalized': (scores[comp] - min(scores.values())) / (max(scores.values()) - min(scores.values())) if len(scores) > 1 else 0.5
        }
        for rank, comp in enumerate(ranking)
    ])
    
    return df

def create_feature_analysis_dataframe(data: Dict[str, Any]) -> pd.DataFrame:
    """Create DataFrame for feature analysis"""
    if not data or 'request' not in data:
        return pd.DataFrame()
    
    request = data['request']
    feature_weights = request.get('feature_weights', {})
    
    # Create feature analysis DataFrame
    features_df = pd.DataFrame([
        {
            'Feature': feature,
            'Weight': weight,
            'Category': 'Feature Weight'
        }
        for feature, weight in feature_weights.items()
    ])
    
    # Add KPI and pricing weights
    kpi_weight = request.get('kpi_weight', 0)
    price_weight = request.get('price_weight', 0)
    
    weights_df = pd.DataFrame([
        {'Feature': 'KPI Analysis', 'Weight': kpi_weight, 'Category': 'Analysis Weight'},
        {'Feature': 'Pricing Analysis', 'Weight': price_weight, 'Category': 'Analysis Weight'},
        {'Feature': 'Feature Analysis', 'Weight': request.get('feature_weight', 0), 'Category': 'Analysis Weight'}
    ])
    
    return pd.concat([features_df, weights_df], ignore_index=True)

def create_radar_chart(df: pd.DataFrame) -> go.Figure:
    """Create radar chart for competitor comparison"""
    if df.empty or len(df) < 2:
        # Create a simple bar chart instead if not enough data for radar
        fig = px.bar(
            df, 
            x='Competitor', 
            y='Score',
            title="Competitor Performance (Alternative View)",
            height=400
        )
        fig.update_layout(
            xaxis_title="Competitors",
            yaxis_title="Score"
        )
        return fig
    
    # Create a proper radar chart with multiple dimensions
    # For now, create a more suitable visualization
    fig = go.Figure()
    
    # Create a horizontal bar chart with better visualization
    fig = go.Figure(data=[
        go.Bar(
            x=df['Score'],
            y=df['Competitor'],
            orientation='h',
            text=[f"#{row['Rank']} - {row['Score']:.2f}" for _, row in df.iterrows()],
            textposition='auto',
            marker_color=px.colors.qualitative.Set1[:len(df)]
        )
    ])
    
    fig.update_layout(
        title="Competitor Performance Ranking",
        xaxis_title="Score",
        yaxis_title="Competitors",
        height=400,
        showlegend=False
    )
    
    return fig

def create_score_comparison_chart(df: pd.DataFrame) -> go.Figure:
    """Create bar chart for score comparison"""
    if df.empty:
        return go.Figure()
    
    # Market Strength Index (business-friendly label for composite score)
    fig = px.bar(
        df,
        x='Competitor',
        y='Score',
        color='Score',
        color_continuous_scale='RdYlGn',
        title="Market Strength Index (Who leads now)",
        height=400
    )
    
    fig.update_layout(
        xaxis_title="Competitors",
        yaxis_title="Market Strength Index",
        showlegend=False
    )
    
    # Add rank annotations
    for i, row in df.iterrows():
        fig.add_annotation(
            x=row['Competitor'],
            y=row['Score'],
            text=f"#{row['Rank']}",
            showarrow=False,
            yshift=10,
            font=dict(size=14, color='white', weight='bold')
        )
    
    return fig

def create_feature_weights_chart(features_df: pd.DataFrame) -> go.Figure:
    """Create chart for feature weights analysis"""
    if features_df.empty:
        return go.Figure()
    
    # Filter for feature weights only
    feature_weights = features_df[features_df['Category'] == 'Feature Weight']
    
    if feature_weights.empty:
        return go.Figure()
    
    fig = px.pie(
        feature_weights,
        values='Weight',
        names='Feature',
        title="Feature Importance Weights",
        height=400
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    
    return fig

def create_momentum_chart(df: pd.DataFrame) -> go.Figure:
    """Create a Market Momentum Score visualization.
    Proxy calculation: z-score of current strength vs peers, rescaled to 0-100.
    Higher = gaining traction. Uses green for higher, red for lower.
    """
    if df.empty:
        return go.Figure()
    
    scores = df['Score']
    mean = scores.mean()
    std = scores.std()
    if std == 0 or pd.isna(std):
        momentum = pd.Series([50.0] * len(df), index=df.index)
    else:
        z = (scores - mean) / std
        momentum = (50 + z * 10).clip(0, 100)
    
    momentum_df = pd.DataFrame({
        'Competitor': df['Competitor'],
        'Momentum': momentum
    }).sort_values('Momentum', ascending=False)
    
    fig = px.bar(
        momentum_df,
        x='Competitor',
        y='Momentum',
        color='Momentum',
        color_continuous_scale='RdYlGn',
        title="Market Momentum Score (Who/what is growing)",
        height=400
    )
    
    fig.update_layout(
        xaxis_title="Competitors",
        yaxis_title="Market Momentum Score",
        showlegend=False
    )
    
    # Add directional arrows via annotations
    for i, row in momentum_df.iterrows():
        arrow = "🔼" if row['Momentum'] >= 50 else "🔽"
        fig.add_annotation(
            x=row['Competitor'],
            y=row['Momentum'],
            text=arrow,
            showarrow=False,
            yshift=10,
        )
    return fig

def create_analysis_weights_chart(features_df: pd.DataFrame) -> go.Figure:
    """Create chart for analysis weights"""
    if features_df.empty:
        return go.Figure()
    
    # Filter for analysis weights
    analysis_weights = features_df[features_df['Category'] == 'Analysis Weight']
    
    if analysis_weights.empty:
        return go.Figure()
    
    fig = px.bar(
        analysis_weights,
        x='Feature',
        y='Weight',
        color='Weight',
        color_continuous_scale='plasma',
        title="Analysis Method Weights",
        height=400
    )
    
    fig.update_layout(
        xaxis_title="Analysis Method",
        yaxis_title="Weight",
        showlegend=False
    )
    
    return fig

def create_trend_analysis_chart(data: Dict[str, Any]) -> go.Figure:
    """Create chart for trend analysis if available"""
    if not data or 'request' not in data:
        return go.Figure()
    
    request = data['request']
    primary_kpis = request.get('primary_kpis', [])
    
    if not primary_kpis:
        return go.Figure()
    
    # Create sample KPI data for visualization
    kpi_data = pd.DataFrame([
        {'KPI': kpi, 'Importance': 1.0, 'Category': 'Primary KPI'}
        for kpi in primary_kpis
    ])
    
    fig = px.bar(
        kpi_data,
        x='KPI',
        y='Importance',
        color='Importance',
        color_continuous_scale='blues',
        title="Primary KPI Analysis",
        height=300
    )
    
    fig.update_layout(
        xaxis_title="Key Performance Indicators",
        yaxis_title="Importance Score",
        showlegend=False
    )
    
    return fig

def display_security_metrics(data: Dict[str, Any]):
    """Display security and metadata information"""
    if not data or 'metadata' not in data:
        return
    
    metadata = data['metadata']
    
    st.subheader("🔒 Security & Metadata")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Generated By",
            value=metadata.get('generated_by', 'Unknown'),
            help="Agent that generated this analysis"
        )
    
    with col2:
        st.metric(
            label="Competitors Analyzed",
            value=metadata.get('competitors_analyzed', 0),
            help="Number of competitors in the analysis"
        )
    
    with col3:
        security_status = metadata.get('security_validated', False)
        if security_status:
            st.markdown('<div class="security-badge">✅ Security Validated</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="warning-badge">⚠️ Security Not Validated</div>', unsafe_allow_html=True)
    
    with col4:
        timestamp = metadata.get('timestamp', 'Unknown')
        if timestamp != 'Unknown':
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                st.metric(
                    label="Generated At",
                    value=dt.strftime("%H:%M:%S"),
                    help=f"Date: {dt.strftime('%Y-%m-%d')}"
                )
            except:
                st.metric(label="Generated At", value="Unknown")
        else:
            st.metric(label="Generated At", value="Unknown")

def display_executive_summary(data: Dict[str, Any]):
    """Display executive summary if available"""
    if not data or 'executive_summary' not in data:
        return
    
    summary = data['executive_summary']
    
    if summary and summary != "LLM analysis unavailable - using baseline scoring only.":
        st.subheader("📊 Executive Summary")
        st.info(summary)
    else:
        st.subheader("📊 Analysis Status")
        st.warning("LLM analysis unavailable - using baseline scoring only.")

def main():
    """Main dashboard function"""
    
    # Header
    st.markdown('<div class="main-header">🔒 Agent 4: Competitor Analysis Dashboard</div>', unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.title("🎛️ Dashboard Controls")
    
    # Load data
    st.sidebar.info("📁 Loading competitor comparison data...")
    data = load_comparison_data()
    
    if not data:
        st.error("❌ No data available. Please run Agent 4 first to generate comparison data.")
        st.info("💡 Use the command: `uv run python -m Competitor_Comparison_Agent.agent4.main`")
        return
    
    # Data overview
    competitors_count = len(data.get('comparison', {}).get('scores', {}))
    st.sidebar.success(f"✅ Loaded {competitors_count} competitors")
    
    # Refresh button
    if st.sidebar.button("🔄 Refresh Data"):
        st.rerun()
    
    # Main content
    if data:
        # Security metrics
        display_security_metrics(data)
        
        # Executive summary
        display_executive_summary(data)
        
        # Create dataframes
        competitors_df = create_competitor_dataframe(data)
        features_df = create_feature_analysis_dataframe(data)
        
        if not competitors_df.empty:
            # Key metrics
            st.subheader("📈 Key Performance Metrics")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                top_competitor = competitors_df.iloc[0]
                st.metric(
                    label="🏆 Top Performer",
                    value=top_competitor['Competitor'],
                    delta=f"Score: {top_competitor['Score']:.2f}"
                )
            
            with col2:
                avg_score = competitors_df['Score'].mean()
                st.metric(
                    label="📊 Average Score",
                    value=f"{avg_score:.2f}",
                    delta=f"±{competitors_df['Score'].std():.2f}"
                )
            
            with col3:
                score_range = competitors_df['Score'].max() - competitors_df['Score'].min()
                st.metric(
                    label="📏 Score Range",
                    value=f"{score_range:.2f}",
                    delta="Max - Min"
                )
            
            with col4:
                total_competitors = len(competitors_df)
                st.metric(
                    label="👥 Total Competitors",
                    value=total_competitors,
                    delta="Analyzed"
                )
            
            # Plain-language interpretation guide for business users
            st.markdown(
                """
                <div class="info-box">
                <strong>How to read the KPIs:</strong><br/>
                • <em>Market Strength Index</em>: Higher score = competitor is stronger now (pricing, features, sentiment).<br/>
                • <em>Market Momentum Score</em>: Higher score = gaining traction compared to peers (relative momentum).
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Charts
            st.subheader("📊 Decision KPIs: Strength vs Momentum")
            
            # Create two columns for charts
            col1, col2 = st.columns(2)
            
            with col1:
                try:
                    score_chart = create_score_comparison_chart(competitors_df)
                    st.plotly_chart(score_chart, use_container_width=True)
                except Exception as e:
                    st.error(f"Error creating score chart: {e}")
                    st.info("Displaying data table instead")
                    st.dataframe(competitors_df)
            
            with col2:
                try:
                    momentum_chart = create_momentum_chart(competitors_df)
                    st.plotly_chart(momentum_chart, use_container_width=True)
                except Exception as e:
                    st.error(f"Error creating momentum chart: {e}")
                    st.info("Displaying alternative visualization")
                    st.bar_chart(competitors_df.set_index('Competitor')['Score'])
            
            # Feature analysis
            if not features_df.empty:
                st.subheader("⚙️ Feature & Analysis Weights")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    try:
                        feature_chart = create_feature_weights_chart(features_df)
                        st.plotly_chart(feature_chart, use_container_width=True)
                    except Exception as e:
                        st.error(f"Error creating feature chart: {e}")
                        st.dataframe(features_df[features_df['Category'] == 'Feature Weight'])
                
                with col2:
                    try:
                        analysis_chart = create_analysis_weights_chart(features_df)
                        st.plotly_chart(analysis_chart, use_container_width=True)
                    except Exception as e:
                        st.error(f"Error creating analysis chart: {e}")
                        st.dataframe(features_df[features_df['Category'] == 'Analysis Weight'])
                
                # KPI analysis
                try:
                    kpi_chart = create_trend_analysis_chart(data)
                    if kpi_chart.data:
                        st.plotly_chart(kpi_chart, use_container_width=True)
                except Exception as e:
                    st.error(f"Error creating KPI chart: {e}")
            
            # Detailed data table
            st.subheader("📋 Detailed Competitor Data")
            st.dataframe(
                competitors_df.style.highlight_max(axis=0, color='lightgreen'),
                use_container_width=True
            )
            
            # Raw data viewer
            with st.expander("🔍 View Raw JSON Data"):
                st.json(data)
        
        else:
            st.warning("⚠️ No competitor data found in the loaded file.")
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
            <p>🔒 <strong>Agent 4: Competitor Comparison & Security</strong> | 
            Built with Streamlit & Plotly | 
            <a href='#' target='_blank'>Documentation</a></p>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()