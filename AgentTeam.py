from agent_protocol import AgentProtocol
from phi.agent import Agent
from phi.model.groq import Groq
from dotenv import load_dotenv
from Data_Scraper_IR_Agent.DataScraperIR import collect_and_index, ir_search
from phi.tools.yfinance import YFinanceTools
from utills.cleaning import extract_clean_text,clean_output
import re

load_dotenv()

protocol = AgentProtocol()

# ---------------------------
# Helper function
# ---------------------------
def get_text(response):
    """Safely extract text from Groq responses"""
    return getattr(response, "output_text", str(response))

def chunk_text(text: str, max_words: int = 500) -> list[str]:
    """Split long text into smaller chunks"""
    words = text.split()
    chunks, i = [], 0
    while i < len(words):
        chunks.append(" ".join(words[i:i+max_words]))
        i += max_words
    return chunks

# ---------------------------
# Agents
# ---------------------------
summarizer_agent = Agent(
    name="SummarizerAgent",
    model=Groq(id="openai/gpt-oss-20b"),
    instructions="""
You are a **Market Insight Summarizer Agent**.

Your task:
1. Read the provided documents.
2. Write a clear, concise **market overview** (150–200 words).
3. Extract and highlight **only information relevant for market research**:
   - Key **market size / growth trends** (CAGR, YoY growth, demand shifts).
   - Key **competitors** (companies, brands, or products).
   - **Opportunities** (emerging markets, tech advances, consumer demand).
   - **Risks / challenges** (supply chain issues, regulations, costs).
   - Any **quantifiable metrics** (percentages, revenue figures, unit counts).

Formatting:
- Start with a short **executive summary (2–3 sentences)**.
- Then provide **bullet points** under these sections:
   • Market Trends  
   • Competitors  
   • Opportunities  
   • Risks / Challenges  
   • Key Metrics  

Rules:
- Keep total output ≤ 200 words.
- If no data is available for a section, write: "Not mentioned".
- Avoid generic filler text.
"""
)

market_research_agent = Agent(
    name="MarketResearchAgent",
    model=Groq(id="deepseek-r1-distill-llama-70b"),
    instructions="Analyze competitors, risks, and opportunities in the market.",



)

trend_analyzer_agent = Agent(
    name="TrendAnalyzerAgent",
    model=Groq(id="deepseek-r1-distill-llama-70b"),
    instructions="Extract key trends and patterns from market insights. Use the given tools if you need to",
    tools=[YFinanceTools(stock_price=True, analyst_recommendations=True, company_info=True)],
)


trend_stats_agent = Agent(
    name="TrendStatsAgent",
    model=Groq(id="deepseek-r1-distill-llama-70b"),
    instructions="""From the given market insights, extract **3–6 quantifiable statistics**.  
Always return ONLY valid JSON in this format:

[
  {"metric": "EV sales growth", "value": 12, "unit": "% CAGR"},
  {"metric": "Battery cost reduction", "value": 8, "unit": "% YoY"},
  {"metric": "Charging stations expansion", "value": 1500, "unit": "units"}
]

No text outside JSON.
"""
)


CompetitorComparison_agent = Agent(
    name="Competitor Comparison Agent",
    role="Analyze competitors in the given industry",
    model=Groq(id="mixtral-8x7b-32768"),
    instructions=[
        "Given an industry query, identify top 3–5 competitors.",
        "Provide approximate figures for: Sales (in millions), MarketShare (%), GrowthRate (%).",
        "Return the results as JSON array of objects, e.g.: "
        "[{'Competitor': 'X', 'Sales': 1200, 'MarketShare': 25, 'GrowthRate': 8}, {...}]",
        "If exact numbers aren't available, provide estimates."
    ]
)

# ---------------------------
# Agent Functions
# ---------------------------
def DataScraper_agent(query: str, k_search: int = 15, k_index: int = 5):
    """Scrape and index data, then send to SummarizerAgent"""
    print(f"[DataScraperAgent] Running for query: {query}")
    try:
        result = collect_and_index(query, k_search=k_search, k_index=k_index)
    except Exception as e:
        print(f"[DataScraperAgent] Error during collection: {e}")
        result = {"docs": []}

    docs = []
    for doc in result.get("docs", []):
        # Keep only title + first 1000 chars to avoid oversize
        text_preview = (doc.get("content") or "")[:1000]
        docs.append(f"{doc.get('title','No Title')} ({doc.get('url','No URL')})\n{text_preview}")

    if not docs:
        print("[DataScraperAgent] Warning: No documents found.")

    payload = {"query": query, "docs": docs}
    protocol.send("DataScraperAgent", "SummarizerAgent", payload)
    return payload


def Summarizer_agent():
    """Receive docs, summarize them safely in chunks, then send to MarketResearchAgent"""
    data = protocol.receive("SummarizerAgent") or {"query": "", "docs": []}
    docs = data.get("docs", [])

    if not docs:
        print("[SummarizerAgent] No docs received.")
        summary = "No documents to summarize."
    else:
        doc_summaries = []
        for doc in docs:
            chunks = chunk_text(doc, max_words=400)  # smaller chunks
            partials = []
            for chunk in chunks:
                try:
                    s = extract_clean_text(get_text(summarizer_agent.run(
                        f"Summarize this into <=150 words:\n\n{chunk}"
                    )))
                    partials.append(s)
                except Exception as e:
                    print(f"[SummarizerAgent] Error while summarizing chunk: {e}")
            # Merge chunks of a single doc
            doc_summary = " ".join(partials)[:1000]  # hard cap length
            doc_summaries.append(doc_summary)

        # Final: combine all doc summaries into one manageable text
        try:
            summary = extract_clean_text(get_text(summarizer_agent.run(
                f"Combine these summaries into a single concise market overview (<=300 words):\n\n{doc_summaries}"
            )))
        except Exception as e:
            summary = f"[Error] {e}"

    protocol.send("SummarizerAgent", "MarketResearchAgent", {"summary": summary})
    return {"summary": summary}


def MarketResearch_agent():
    """Receive summary, generate market insights, send to TrendAnalyzerAgent"""
    data = protocol.receive("MarketResearchAgent") or {"summary": ""}
    try:
        insights = extract_clean_text(get_text(market_research_agent.run(data.get("summary", ""))))
    except Exception as e:
        insights = f"[Error] {e}"
        print(f"[MarketResearchAgent] Error: {e}")

    protocol.send("MarketResearchAgent", "TrendAnalyzerAgent", {"insights": insights})
    return {"insights": insights}


def CompetitorComparison_agent(query: str, docs: list):
    """
    Analyze competitors in a given industry using web-scraped docs as context.
    Returns dict with structured data (if possible) and raw text.
    """
    context = "\n\n".join(docs[:10]) if docs else "No scraped documents available."

    prompt = f"""
    You are a competitor analysis agent. Your task is to analyze competitors in the industry.

    User Query: "{query}"

    Context (from web scraping, may contain articles, reports, or financial data):
    {context}

    Instructions:
    1. Identify the top 3–5 competitors in this industry.
    2. For each competitor, extract or estimate:
       - Sales (numeric, in millions USD, e.g., 4500 = $4.5B)
       - MarketShare (percentage 0–100)
       - GrowthRate (percentage 0–100)
    3. If exact figures are unavailable, make reasonable estimates.
    4. Respond **only** with a valid JSON array of objects in this format:

    [
      {{"Competitor": "Competitor A", "Sales": 1200, "MarketShare": 25, "GrowthRate": 8}},
      {{"Competitor": "Competitor B", "Sales": 800, "MarketShare": 15, "GrowthRate": 5}}
    ]

    Rules:
    - Do NOT include explanations outside JSON.
    - Ensure values are numbers (no % symbols, no commas).
    - Sales should be integers representing millions of USD.
    """

    agent = Agent(
        name="Competitor Comparison Agent",
        role="Extract and analyze competitor data from scraped context",
        model=Groq(id="deepseek-r1-distill-llama-70b"),
    )

    raw_output = get_text(agent.run(prompt))

    parsed = []
    try:
        json_match = re.search(r"\[.*\]", raw_output, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())
    except Exception as e:
        print(f"[CompetitorComparison_agent] Failed to parse JSON: {e}")

    return {"data": parsed, "raw": raw_output}



def TrendAnalyzer_agent():
    """Receive market insights, extract trends"""
    data = protocol.receive("TrendAnalyzerAgent") or {"insights": ""}
    try:
        trends = extract_clean_text(get_text(trend_analyzer_agent.run(data.get("insights", ""))))
    except Exception as e:
        trends = f"[Error] {e}"
        print(f"[TrendAnalyzerAgent] Error: {e}")

    print("[TrendAnalyzerAgent] Trends extracted successfully.")
    return {"trends": trends}





import json

def TrendStats_agent():
    """Receive market insights, extract structured stats for charts"""
    data = protocol.receive("TrendAnalyzerAgent") or {"insights": ""}
    raw_output = ""
    try:
        raw_output = get_text(trend_stats_agent.run(data.get("insights", "")))
        stats = json.loads(raw_output)
    except Exception as e:
        print(f"[TrendStatsAgent] Error parsing stats: {e}")
        stats = []
    
    print("[TrendStatsAgent] Stats extracted successfully.")
    return {"stats": stats, "raw": raw_output}


# ---------------------------
# Optional: Full pipeline runner
# ---------------------------
def run_full_pipeline(query: str):
    DataScraper_agent(query)
    Summarizer_agent()
    MarketResearch_agent()
    trends = TrendAnalyzer_agent()
    return trends

# Example usage:
# results = run_full_pipeline("Electric Vehicle market trends 2025")
# print(results)
