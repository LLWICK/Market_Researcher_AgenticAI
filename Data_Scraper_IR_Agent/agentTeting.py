import json
import os
from DataScraperIR import collect_and_index, ir_search
from phi.agent import Agent
from phi.model.groq import Groq
from dotenv import load_dotenv
from phi.model.ollama import Ollama

load_dotenv()

def Scraper_agent(query: str, json_file: str = "scraped_docs.json") -> str:
    """
    Scrapes data for the query, saves to JSON, then runs the Phi agent
    over the pre-scraped content and returns the summary.
    """

    # --- Step 1: Scrape & index ---
    print(f"Scraping data for query: {query}")
    scrape_result = collect_and_index(query, k_search=10, k_index=6)

    # --- Step 2: Save scraped data to JSON ---
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(scrape_result, f, ensure_ascii=False, indent=2)

    # --- Step 3: Load saved data ---
    with open(json_file, "r", encoding="utf-8") as f:
        docs_data = json.load(f)

    # --- Step 4: Gather context ---
    # Better: include search hits (titles + sources)
    hits = ir_search(query, limit=5)
    context_text = ""
    for h in hits:
        context_text += f"- {h['title']} ({h['source']})\n"

    # --- Step 5: Create Agent ---
    agent = Agent(
    name="LocalFileAgent",
    model=Ollama(id="llama3.2"),
    instructions=(
        "You are a research assistant. You have access to the following pre-scraped documents:\n"
        f"{context_text}\n"
        "Answer the user query based only on this information. "
        "Summarize clearly and concisely."
    )
)

    # --- Step 6: Run agent ---
    response = agent.run(query)
    return response


# --- Example usage ---
if __name__ == "__main__":
    summary = Scraper_agent("What are the top competitors in Laptop market? Should we enter this market?")
    print(summary)
