import json
import os
from DataScraperIR import collect_and_index, ir_search
from phi.agent import Agent
from phi.model.ollama import Ollama
from dotenv import load_dotenv
from phi.model.groq import Groq

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

    context_text = "\n".join([f"- {h['title']} ({h['source']})" for h in hits])

    agent = Agent(
        name="SummarizerAgent",
        #model=Ollama(id="llama3.2"),
        model=Groq(id="openai/gpt-oss-20b"),
        instructions=(
            "You are a Summarizer Agent. Based on the following documents and search results, "
            "summarize the key competitors and market highlights.\n"
            f"{context_text}"
        )
    )

    response = agent.run(query)
    summary_text = str(response) if not hasattr(response, "output_text") else response.output_text

    return {"summary": summary_text, "ir_hits": hits}


def MarketResearch_agent(summary_output: dict, query: str) -> dict:
    summary = summary_output["summary"]
    hits = summary_output["ir_hits"]

    context = f"Query: {query}\n\nSummary:\n{summary}\n\nKey Sources:\n"
    context += "\n".join([f"- {h['title']} ({h['source']})" for h in hits])

    agent = Agent(
        name="MarketResearchAgent",
        model=Groq(id="openai/gpt-oss-20b"),
        #model=Ollama(id="llama3.2"),
        instructions=(
            "You are a Market Research Analyst. Based on the summary and sources, "
            "analyze competitors, opportunities, risks, and recommend market strategies."
        )
    )

    response = agent.run(context)
    insights_text = str(response) if not hasattr(response, "output_text") else response.output_text

    return {"research_insights": insights_text}



def TrendAnalyzer_agent(scraper_output: dict) -> dict:
    scraped_docs = scraper_output.get("ir_hits", [])

    # ✅ Ensure scraped_docs is always a list of strings
    if not isinstance(scraped_docs, list):
        print("[TrendAnalyzer] Warning: scraped_docs is not a list. Forcing conversion.")
        scraped_docs = [str(scraped_docs)]
    else:
        scraped_docs = [str(doc) for doc in scraped_docs]

    context = "\n".join(scraped_docs)

    agent = Agent(
        name="TrendAnalyzerAgent",
        #model=Ollama(id="llama3.2"),
        model=Groq(id="openai/gpt-oss-20b"),
        instructions=(
            "You are a Trend Analyzer. Based on the scraped documents, "
            "identify emerging trends, competitor movements, and shifts in consumer demand."
        )
    )

    response = agent.run(context)
    trends_text = str(response) if not hasattr(response, "output_text") else response.output_text

    return {"trends": trends_text}




# -------------------------
# Pipeline Execution
# -------------------------
# -------------------------
# Pipeline Execution
# -------------------------
if __name__ == "__main__":
    query = "What are the latest trends in online grocery delivery services?"

    # Step 1: Scraper
    scraper_output = DataScraper_agent(query)
    print("\n=== Step 1: Data Scraper Output ===")
    print(json.dumps(scraper_output, indent=2, ensure_ascii=False))

    # Step 2: Summarizer
    summary_output = Summarizer_agent(scraper_output)
    print("\n=== Step 2: Summarizer Output ===")
    print(json.dumps(summary_output, indent=2, ensure_ascii=False))

    # Step 3: Market Research
    research_output = MarketResearch_agent(summary_output, query)
    print("\n=== Step 3: Market Research Insights ===")
    print(research_output["research_insights"])

    # Step 4: Trend Analyzer
    trend_output = TrendAnalyzer_agent(scraper_output)
    print("\n=== Step 4: Trend Analyzer Output ===")
    print(trend_output["trends"])

    # Save pipeline results (JSON safe)
    final_output = {
        "scraper": {k: str(v) for k, v in scraper_output.items()},
        "summary": {k: str(v) for k, v in summary_output.items()},
        "research": {k: str(v) for k, v in research_output.items()},
        "trends": {k: str(v) for k, v in trend_output.items()}
    }

    with open("pipeline_output.json", "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2, ensure_ascii=False)

    print("\n✅ All agent outputs have been saved to pipeline_output.json")


