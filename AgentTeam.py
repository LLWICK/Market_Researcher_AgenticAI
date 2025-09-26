from agent_protocol import AgentProtocol
from phi.agent import Agent
from phi.model.groq import Groq
from dotenv import load_dotenv
from Data_Scraper_IR_Agent.DataScraperIR import collect_and_index, ir_search
from phi.tools.yfinance import YFinanceTools
from utills.cleaning import extract_clean_text,clean_output
import re
from phi.tools.duckduckgo import DuckDuckGo

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
    model=Groq(id="deepseek-r1-distill-llama-70b"),
    tools=[DuckDuckGo()],
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
4. If the provided documents are not enough please use the tools provided (**DuckDuckGo()**) and get the relevant information

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











# ---------------------------
# Optional: Full pipeline runner
# ---------------------------
def run_full_pipeline(query: str):
    DataScraper_agent(query)
    Summarizer_agent()
    MarketResearch_agent()
    return 

# Example usage:
# results = run_full_pipeline("Electric Vehicle market trends 2025")
# print(results)
