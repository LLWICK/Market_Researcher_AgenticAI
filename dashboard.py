import json
from pathlib import Path
import streamlit as st
from html import escape

# ---------- helpers ----------
def read_json_file(file_path: Path):
    try:
        if not file_path.exists():
            return None
        with file_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Failed to read {file_path}: {e}")
        return None

def render_card(title_html: str, body_html: str, path_note: str | None = None):
    """Renders a complete card as a single HTML block so all content stays inside."""
    note_html = f'<div class="path-note">{escape(path_note)}</div>' if path_note else ""
    st.markdown(
        f'''
        <div class="result-card">
            <div class="rc-title">{title_html}</div>
            <div class="rc-body">{body_html}</div>
            {note_html}
        </div>
        ''',
        unsafe_allow_html=True,
    )

def list_or_dash(items):
    return ", ".join(map(str, items)) if items else "-"

def scores_table_html(scores: dict[str, float]) -> str:
    # Return just the label, we'll handle the table separately
    return "<p><strong>Scores</strong></p>"

# ---------- app ----------
def main() -> None:
    st.set_page_config(page_title="Agent 4 Dashboard", layout="wide")

    # Global CSS (colors, cards, header bar, typography)
    st.markdown(
        """
        <style>
        :root{
            --bg: #2e2e2e;          /* page background dark gray */
            --card: #1f1f1f;        /* dark cards */
            --text: #ffffff;        /* white text */
            --muted: #aaaaaa;       /* secondary text */
            --accent: #3b82f6;      /* blue accent */
            --radius: 14px;
            --shadow: 0 6px 18px rgba(0,0,0,.5);
            --border: rgba(255,255,255,.12);
            --row: rgba(255,255,255,.04);
        }

        .stApp { background: var(--bg); color: var(--text); }

        .topbar {
            position: sticky; top: 0; z-index: 100;
            background: #111111; 
            color: #f9f9f9;
            padding: 16px 20px;
            border-bottom: 1px solid rgba(255,255,255,.15);
            margin: -1.5rem -1.5rem 1.5rem -1.5rem;
        }
        .topbar h1 { margin: 0; font-size: 1.3rem; font-weight: 700; }
        .topbar small { color: #cccccc; }

        .result-card {
            background: var(--card);
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            padding: 20px;
            margin-bottom: 1rem;
            transition: transform .15s ease, box-shadow .15s ease;
            color: var(--text);
            border: 1px solid var(--border);
        }
        .result-card:hover { transform: translateY(-3px); box-shadow: 0 10px 28px rgba(0,0,0,.6); }

        .rc-title { font-size: 1.1rem; font-weight: 700; margin-bottom: .75rem; color: var(--accent); }
        .rc-body p { margin: .4rem 0; }
        .path-note { color: var(--muted); font-size: .75rem; margin-top: .6rem; word-break: break-all; }

        .prompt-wrap {
            background: var(--card);
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            padding: 16px 18px;
            margin-bottom: 18px;
            color: var(--text);
            border: 1px solid var(--border);
        }

        /* Dark table styling inside cards */
        .table-wrap { overflow-x: auto; }
        .dark-table {
            width: 100%;
            border-collapse: collapse;
            border: 1px solid var(--border);
            border-radius: 12px;
            overflow: hidden;
        }
        .dark-table th, .dark-table td {
            padding: 10px 12px;
            border-bottom: 1px solid var(--border);
            text-align: left;
        }
        .dark-table thead th {
            background: #151515;
            color: #eaeaea;
            font-weight: 700;
        }
        .dark-table tbody tr:nth-child(odd) { background: var(--row); }
        .dark-table tbody tr:hover { background: rgba(59,130,246,.12); }

                 /* Neutralize any code-block look inside cards */
         .result-card pre, .result-card code, .rc-body pre, .rc-body code {
           background: transparent !important;
           color: inherit !important;
           border: 0 !important;
           box-shadow: none !important;
           padding: 0 !important;
           margin: 0 !important;
           font-family: inherit !important;
           font-size: inherit !important;
           white-space: normal !important;
         }
+
+        /* Hide any remaining code-like elements */
+        .result-card .stCodeBlock, .result-card .stMarkdown {
+          display: none !important;
+        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Top bar
    st.markdown(
        """
        <div class="topbar">
            <h1>📊 Competitor Comparison</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---------- DATA PATHS ----------
    base_dir = Path(__file__).parent
    # This file already lives inside Market_Researcher_AgenticAI, so don't repeat that segment
    agent_dir = base_dir / "Competitor_Comparison_Agent" / "agent4"
    outbound_file = agent_dir / "data" / "outbound" / "competitor_comparison_result.json"
    trends_file = agent_dir / "data" / "inbound" / "trends.json"

    # ---------- PROMPT INPUT (UI ONLY) ----------
    st.markdown('<div class="prompt-wrap">', unsafe_allow_html=True)
    user_prompt = st.text_input(
        "Describe the market, focus areas, competitors to analyze, etc.",
        value="",
        placeholder="e.g., EV charging in Southeast Asia, last 12 months, focus on pricing + partnerships",
        label_visibility="collapsed",
    )
    if user_prompt:
        st.info("Prompt captured. (No backend changes triggered as requested.)")
    st.markdown("</div>", unsafe_allow_html=True)

    # ---------- LOAD DATA ----------
    result_data = read_json_file(outbound_file)
    trends_data = read_json_file(trends_file)

    # ---------- LAYOUT ----------
    col1, col2, col3 = st.columns([1, 1, 1])

    # Research Summary (card-rendered, escaped to avoid code look)
    with col1:
        if result_data and isinstance(result_data, dict):
            summary = result_data.get("executive_summary")
            if summary:
                safe_summary = escape(str(summary)).replace("\n", "<br/>")
                body = f"<p>{safe_summary}</p>"
            else:
                body = '<p style="color:#fca5a5;">No executive summary found in output.</p>'
        else:
            body = '<p style="color:#fca5a5;">Result file not found or invalid. Run the agent to generate outputs.</p>'
        render_card("📑 Research Summary", body, str(outbound_file))

    # Trends (card-rendered)
    with col2:
        if trends_data and isinstance(trends_data, dict):
            topics = list_or_dash(trends_data.get("topics", []))
            sentiment = trends_data.get("sentiment_score")
            sentiment_text = str(sentiment) if sentiment is not None else "-"
            growth = list_or_dash(trends_data.get("growth_keywords", []))
            regions = list_or_dash(trends_data.get("regions", []))
            body = f"""
                <p><strong>Topics</strong><br/>{escape(topics)}</p>
                <p><strong>Sentiment Score</strong><br/>{escape(sentiment_text)}</p>
                <p><strong>Growth Keywords</strong><br/>{escape(growth)}</p>
                <p><strong>Regions</strong><br/>{escape(regions)}</p>
            """
        else:
            body = '<p style="color:#fca5a5;">Trends file not found or invalid.</p>'
        render_card("📈 Trends", body, str(trends_file))

    # Competitors (card-rendered, pure HTML)
    with col3:
        if result_data and isinstance(result_data, dict):
            comparison = result_data.get("comparison", {})
            ranking = comparison.get("ranking") or result_data.get("ranking")
            scores = comparison.get("scores") or result_data.get("scores")

            parts = []
            if ranking:
                items = "".join(f"<li>{escape(str(name))}</li>" for name in ranking)
                parts.append(f"<p><strong>Ranking</strong></p><ol>{items}</ol>")
            else:
                parts.append("<p>No ranking available.</p>")

            body = "\n".join(parts)
            
            # Render the card first
            render_card("🏁 Competitors", body, str(outbound_file))
            
            # Then add the scores table below the card using native Streamlit
            if isinstance(scores, dict) and scores:
                st.markdown("**Scores**")
                # Create data for the table
                table_data = [{"Competitor": k, "Score": round(v, 2)} for k, v in sorted(scores.items(), key=lambda x: x[1], reverse=True)]
                st.table(table_data)
        else:
            body = '<p style="color:#fca5a5;">Result file not found or invalid.</p>'
            render_card("🏁 Competitors", body, str(outbound_file))


if __name__ == "__main__":
    main()
