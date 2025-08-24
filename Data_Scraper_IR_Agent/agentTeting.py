import json
import os
from DataScraperIR import collect_and_index, ir_search
from phi.agent import Agent
from phi.model.groq import Groq

def research_agent(query: str, json_file: str = "scraped_docs.json") -> str:
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

    # --- Step 3: Load the saved data ---
    with open(json_file, "r", encoding="utf-8") as f:
        docs_data = json.load(f)

    # --- Step 4: Prepare context for the agent ---
    context_text = ""
    for title in docs_data.get("examples", []):
        context_text += f"- {title}\n"

  

    # --- Step 6: Create agent ---
    agent = Agent(
        name="LocalFileAgent",
        model = Groq(id="deepseek-r1-distill-llama-70b"),
        instructions=(
            "You are a research assistant. You have access to the following pre-scraped documents:\n"
            f"{context_text}\n"
            "Answer the user query based only on this information.",
            "Give response according to a json format"
        )
    )

    # --- Step 7: Run agent ---
    response = agent.run(query)
    return response

# --- Example usage ---
if __name__ == "__main__":
    summary = research_agent("Top EV car market comparisons")
    print(summary)