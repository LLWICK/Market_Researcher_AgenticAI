import json
import os
from DataScraperIR import collect_and_index, make_doc, ir_search
from phi.agent import Agent
from phi.model.groq import Groq

def research_agent_full_content(query: str, json_file: str = "scraped_docs_full.json") -> dict:
    """
    Scrapes & indexes documents, saves full content to JSON, runs Phi agent
    over full scraped documents, returns structured JSON output.
    """

    # --- Step 1: Scrape & index ---
    scrape_result = collect_and_index(query, k_search=10, k_index=6)

    # --- Step 2: Load full document content from cache ---
    docs_full = []
    for url_title in scrape_result.get("examples", []):
        # make_doc will load from cache if available
        doc = make_doc(url_title)
        if doc:
            docs_full.append({
                "title": doc.title,
                "url": str(doc.url),
                "content": doc.content[:5000],  # truncate very long content if needed
                "source": doc.source,
                "published_at": doc.published_at.isoformat() if doc.published_at else None
            })

    # --- Step 3: Save full documents to JSON ---
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(docs_full, f, ensure_ascii=False, indent=2)

    # --- Step 4: Prepare context text for the agent ---
    context_text = ""
    for doc in docs_full:
        context_text += (
            f"Title: {doc['title']}\n"
            f"URL: {doc['url']}\n"
            f"Source: {doc.get('source', 'N/A')}\n"
            f"Published: {doc.get('published_at', 'N/A')}\n"
            f"Content: {doc['content']}\n\n"
        )

    # --- Step 5: Initialize Phi LLM ---
    llm = Groq(model="llama-3.3-70b-versatile", api_key=os.getenv("GROQ_API_KEY"))

    # --- Step 6: Create agent ---
    agent = Agent(
        name="LocalFileAgent",
        model=Groq(id="deepseek-r1-distill-llama-70b"),
        instructions=(
            "You are a research assistant. You have access to the following pre-scraped documents:\n"
            f"{context_text}\n"
            "Answer the user query based only on this information."
        )
    )

    # --- Step 7: Run agent ---
    summary = agent.run(query)

    # --- Step 8: Return structured JSON ---
    return {
        "query": query,
        "scraped_docs": docs_full,
        "summary": summary
    }

# --- Example usage ---
if __name__ == "__main__":
    result_json = research_agent_full_content("Summarize Nvidia stock insights for 2025")
    print(json.dumps(result_json, ensure_ascii=False, indent=2))
