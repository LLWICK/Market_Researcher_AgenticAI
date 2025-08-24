from phi.agent import Agent, Tool
from phi.model.groq import Groq
from DataScraperIR import collect_and_index, ir_search
import os
from dotenv import load_dotenv

load_dotenv()

# --- Step 1: Python functions must have proper __name__
def scrape_marketing_data(prompt: str):
    return collect_and_index(prompt, k_search=15, k_index=8)

scrape_marketing_data.__name__ = "scrape_marketing_data"  # explicit name

def search_index(query: str):
    return ir_search(query)[:5]

search_index.__name__ = "search_index"  # explicit name

# --- Step 2: Wrap as Tools with type="function" ---
scrape_tool = Tool(
    type="function",  # required by Groq
    func=scrape_marketing_data,
    name="ScrapeMarketingData",
    description="Scrapes & indexes marketing data based on user prompt"
)

search_tool = Tool(
    type="function",
    func=search_index,
    name="SearchIndex",
    description="Searches indexed documents for insights"
)

# --- Step 3: Initialize the LLM ---
llm = Groq(
    id="deepseek-r1-distill-llama-70b",  # check if model exists
    api_key=os.getenv("GROQ_API_KEY")
)

# --- Step 4: Create the agent ---
marketing_agent = Agent(
    name="Marketing Research Agent",
    model=llm,
    instructions=(
        "You are a marketing research assistant. "
        "Use the scraping and IR tools to fetch and summarize marketing data."
    ),
    tools=[scrape_tool, search_tool]
)

# --- Step 5: Run the agent ---
prompt = (
    "Get me the latest 2025 digital marketing spend forecasts in Asia "
    "and summarize the top insights."
)

for chunk in marketing_agent.run(prompt):
    print(chunk)
