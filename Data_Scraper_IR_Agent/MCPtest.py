from mcp.server.fastmcp import FastMCP
from phi.agent import Agent
from phi.model.ollama import Ollama
from DataScraperIR import collect_and_index, ir_search
import json

# --- Initialize MCP Server ---
mcp = FastMCP("MarketPipeline")

# --- Agent Definitions ---

@mcp.tool()
def scraper(query: str) -> dict:
    """Scrape data and return raw docs + IR hits"""
    docs = collect_and_index(query, k_search=10, k_index=6)
    hits = ir_search(query, limit=5)
    return {"query": query, "scraped_docs": docs, "ir_hits": hits}

@mcp.tool()
def summarizer(scraper_output: dict) -> dict:
    """Summarize competitor findings from scraped data"""
    context_text = "\n".join([f"- {h['title']} ({h['source']})" for h in scraper_output["ir_hits"]])
    agent = Agent(
        name="SummarizerAgent",
        model=Ollama(id="llama3.2"),
        instructions="Summarize competitors and market highlights from:\n" + context_text
    )
    summary = agent.run(scraper_output["query"])
    return {"summary": summary, "ir_hits": scraper_output["ir_hits"]}

@mcp.tool()
def research(summary_output: dict, query: str) -> dict:
    """Provide competitor analysis & recommendations"""
    context = f"Query: {query}\n\nSummary:\n{summary_output['summary']}"
    agent = Agent(
        name="ResearchAgent",
        model=Ollama(id="llama3.2"),
        instructions="Analyze competitors, risks, opportunities, and strategies."
    )
    insights = agent.run(context)
    return {"research_insights": insights}

@mcp.tool()
def trends(scraper_output: dict) -> dict:
    """Analyze emerging market trends"""
    context = "\n".join([f"- {doc.get('title','Untitled')}" for doc in scraper_output["scraped_docs"][:10]])
    agent = Agent(
        name="TrendAgent",
        model=Ollama(id="llama3.2"),
        instructions="Identify emerging trends, demand shifts, and growth areas."
    )
    result = agent.run(context)
    return {"trends": result}

# --- Run MCP Server ---
if __name__ == "__main__":
    mcp.run()
