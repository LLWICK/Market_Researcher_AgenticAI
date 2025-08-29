import json
import os
from DataScraperIR import collect_and_index, ir_search
from phi.agent import Agent
from phi.model.ollama import Ollama
from dotenv import load_dotenv
from phi.tools.yfinance import YFinanceTools

load_dotenv()


# -------------------------
# Data Scraper Agent
# -------------------------
def DataScraper_agent(query: str, json_file: str = "scraped_docs.json") -> dict:
    """Scrapes data for the query, saves to JSON, then summarizes with an LLM."""

    print(f"[DataScraperAgent] Scraping data for query: {query}")
    scrape_result = collect_and_index(query, k_search=10, k_index=6)

    # Save scraped metadata to JSON
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(scrape_result, f, ensure_ascii=False, indent=2)

    with open(json_file, "r", encoding="utf-8") as f:
        docs_data = json.load(f)

    # Gather context from IR
    hits = ir_search(query, limit=5)
    context_text = "Pre-scraped document titles:\n"
    for h in hits:
        context_text += f"- {h['title']} ({h['source']})\n"

    # Summarizer agent
    agent = Agent(
        name="DataScraperAgent",
        model=Ollama(id="llama3.2"),  # make sure this model exists in ollama list
        instructions=(
            "You are a Data Scraper Agent. "
            "Summarize the following pre-scraped documents clearly and concisely:\n\n"
            f"{context_text}",
            "Also use given tools to get market insights"
        ),
        #tools= [YFinanceTools(stock_price=True, analyst_recommendations=True, stock_fundamentals=True)],
        show_tool_calls=True,
        markdown=True,
    )

    summary = agent.run(query)

    return {
        "query": query,
        "scraped_docs": docs_data,
        "ir_hits": hits,
        "summary": summary
    }


# -------------------------
# Market Research Agent
# -------------------------
def MarketResearch_agent(scraper_output: dict) -> str:
    """Uses scraper output to analyze competitors & market trends."""

    query = scraper_output["query"]
    summary = scraper_output["summary"]
    hits = scraper_output["ir_hits"]

    context = f"Query: {query}\n\n"
    context += f"Scraper Summary:\n{summary}\n\n"
    context += "Key sources:\n"
    for h in hits:
        context += f"- {h['title']} ({h['source']})\n"

    agent = Agent(
        name="MarketResearchAgent",
        model=Ollama(id="llama3.2"),
        instructions=(
            "You are a Market Research Analyst. "
            "Based on the findings, analyze competitors, opportunities, risks, "
            "and provide recommendations on market entry."
        )
    )

    return agent.run(context)


# -------------------------
# Pipeline Execution
# -------------------------
if __name__ == "__main__":
    # Step 1: Scraper Agent
    scraper_output = DataScraper_agent("What are the top competitors in Smartphone market?")

    # Step 2: Market Research Agent
    insights = MarketResearch_agent(scraper_output)

    print("\n--- Scraper Summary ---\n")
    print(scraper_output["summary"])

    print("\n--- Market Research Insights ---\n")
    print(insights) 
""" 
    with open("pipeline_output.json", "w", encoding="utf-8") as f:
        json.dump({
            "scraper": scraper_output,
            "research_insights": insights
        }, f, indent=2, ensure_ascii=False) """
