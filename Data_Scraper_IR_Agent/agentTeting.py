import json
import os
from DataScraperIR import collect_and_index, ir_search
from phi.agent import Agent
from phi.model.ollama import Ollama
from dotenv import load_dotenv

load_dotenv()


# -------------------------
# Data Scraper Agent
# -------------------------
def DataScraper_agent(query: str, json_file: str = "scraped_docs.json") -> dict:
    """
    Scrapes data for the query, saves to JSON, then runs the Phi agent
    over the pre-scraped content and returns structured output.
    """

    # --- Step 1: Scrape & index ---
    print(f"[DataScraperAgent] Scraping data for query: {query}")
    scrape_result = collect_and_index(query, k_search=10, k_index=6)

    # --- Step 2: Save scraped data to JSON ---
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(scrape_result, f, ensure_ascii=False, indent=2)

    # --- Step 3: Load saved data ---
    with open(json_file, "r", encoding="utf-8") as f:
        docs_data = json.load(f)

    # --- Step 4: Gather context from IR ---
    hits = ir_search(query, limit=5)
    context_text = ""
    for h in hits:
        context_text += f"- {h['title']} ({h['source']})\n"

    # --- Step 5: Create Agent for summarization ---
    agent = Agent(
        name="DataScraperAgent",
        model=Ollama(id="llama3.2"),
        instructions=(
            "You are a Data Scraper Agent. You have collected the following pre-scraped documents:\n"
            f"{context_text}\n"
            "Summarize the key points clearly and concisely for downstream analysis."
        )
    )

    # --- Step 6: Run agent ---
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
    """
    Market Research Agent that uses scraper output
    to provide competitor analysis & recommendations.
    """

    query = scraper_output["query"]
    summary = scraper_output["summary"]
    hits = scraper_output["ir_hits"]

    # Build context for reasoning
    context = f"Query: {query}\n\n"
    context += f"Scraper Summary:\n{summary}\n\n"
    context += "Key sources:\n"
    for h in hits:
        context += f"- {h['title']} ({h['source']})\n"

    # Create Market Research Agent
    agent = Agent(
        name="MarketResearchAgent",
        model=Ollama(id="llama3.2"),
        instructions=(
            "You are a Market Research Analyst. "
            "Based on the provided findings, analyze the competitive landscape "
            "and provide actionable insights and recommendations. "
            "Focus on: major competitors, market opportunities, risks, and whether to enter the market."
        )
    )

    # Run reasoning
    insights = agent.run(context)
    return insights


# -------------------------
# Pipeline Execution
# -------------------------
if __name__ == "__main__":
    # Step 1: Run Data Scraper Agent
    scraper_output = DataScraper_agent("What are the top competitors in Laptop market?")

    # Step 2: Run Market Research Agent with scraper’s output
    """ insights = MarketResearch_agent(scraper_output)

    print("\n--- Scraper Summary ---\n")
    print(scraper_output["summary"])

    print("\n--- Market Research Insights ---\n") """
    print(scraper_output)
