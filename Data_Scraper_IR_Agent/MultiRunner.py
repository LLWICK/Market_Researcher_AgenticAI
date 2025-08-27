import json
import os
from DataScraperIR import collect_and_index, ir_search
from phi.agent import Agent
from phi.model.ollama import Ollama
from dotenv import load_dotenv

load_dotenv()


def DataScraper_agent(query: str, json_file: str = "scraped_docs.json") -> dict:
    print(f"[DataScraperAgent] Scraping data for query: {query}")
    scrape_result = collect_and_index(query, k_search=10, k_index=6)

    # Save scraped results
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(scrape_result, f, indent=2, ensure_ascii=False)

    # IR search for context
    hits = ir_search(query, limit=5)
    return {
        "query": query,
        "scraped_docs": scrape_result,
        "ir_hits": hits
    }



def Summarizer_agent(scraper_output: dict) -> dict:
    query = scraper_output["query"]
    hits = scraper_output["ir_hits"]

    # Build context from IR
    context_text = "\n".join([f"- {h['title']} ({h['source']})" for h in hits])

    agent = Agent(
        name="SummarizerAgent",
        model=Ollama(id="llama3.2"),
        instructions=(
            "You are a Summarizer Agent. Based on the following documents and search results, "
            "summarize the key competitors and market highlights.\n"
            f"{context_text}"
        )
    )

    summary = agent.run(query)
    return {"summary": summary, "ir_hits": hits}


def MarketResearch_agent(summary_output: dict, query: str) -> dict:
    summary = summary_output["summary"]
    hits = summary_output["ir_hits"]

    context = f"Query: {query}\n\nSummary:\n{summary}\n\nKey Sources:\n"
    context += "\n".join([f"- {h['title']} ({h['source']})" for h in hits])

    agent = Agent(
        name="MarketResearchAgent",
        model=Ollama(id="llama3.2"),
        instructions=(
            "You are a Market Research Analyst. Based on the summary and sources, "
            "analyze competitors, opportunities, risks, and recommend market strategies."
        )
    )

    insights = agent.run(context)
    return {"research_insights": insights}


def TrendAnalyzer_agent(scraper_output: dict) -> dict:
    docs = scraper_output.get("scraped_docs", [])
    
    if not isinstance(docs, list):
        print("[TrendAnalyzer] Warning: scraped_docs is not a list")
        return {"trend_analysis": "No docs to analyze", "trends": ""}

    selected_docs = docs[:10]

    trends_text = "\n".join([
        f"- {doc.get('title', 'No Title')} ({doc.get('url', 'No URL')})"
        for doc in selected_docs
    ])

    return {
        "trend_analysis": f"Analyzed {len(selected_docs)} documents",
        "trends": trends_text
    }



# -------------------------
# Pipeline Execution
# -------------------------
if __name__ == "__main__":
    query = "What are the top competitors in Laptop market?"

    # Step 1: Scraper
    scraper_output = DataScraper_agent(query)

    # Step 2: Summarizer
    summary_output = Summarizer_agent(scraper_output)

    # Step 3: Market Research
    research_output = MarketResearch_agent(summary_output, query)

    # Step 4: Trend Analyzer
    trend_output = TrendAnalyzer_agent(scraper_output)

    # Save pipeline results
    final_output = {
        "scraper": scraper_output,
        "summary": summary_output,
        "research": research_output,
        "trends": trend_output
    }

    #with open("pipeline_output.json", "w", encoding="utf-8") as f:
     #   json.dump(final_output, f, indent=2, ensure_ascii=False)

    print("\n--- Market Research Insights ---\n")
    print(research_output["research_insights"])

    print("\n--- Emerging Trends ---\n")
    print(trend_output["trends"])

