from phi.agent import Agent, Tool
from phi.model.groq import Groq
from DataScraperIR import collect_and_index, ir_search
import os
from dotenv import load_dotenv

load_dotenv()

# --- Step 1: Define Python functions ---
def scrape_marketing_data(prompt: str):
    return collect_and_index(prompt, k_search=15, k_index=8)

def search_index(query: str):
    return ir_search(query)[:5]

# --- Step 2: Wrap them as Tools ---
scrape_tool = Tool(
    type="function",
    func=scrape_marketing_data,
    name="scrape_marketing_data",   # must match function.__name__
    description="Scrapes & indexes marketing data based on user prompt"
)

search_tool = Tool(
    type="function",
    func=search_index,
    name="search_index",
    description="Searches indexed documents for insights"
)

# --- Step 3: Only init LLM here ---
llm = Groq(
    id="deepseek-r1-distill-llama-70b",
    api_key=os.getenv("GROQ_API_KEY")
)

# --- Step 4: Create the Agent ---
marketing_agent = Agent(
    name="Marketing Research Agent",
    model=llm,
    instructions="You are a marketing research assistant. Use the scraping and IR tools.",
    tools=[scrape_tool, search_tool]   # ✅ Tools go here, not in Groq()
)

# --- Step 5: Run the Agent ---
prompt = "Get me the latest 2025 digital marketing spend forecasts in Asia and summarize top insights."

for chunk in marketing_agent.run(prompt):
    print(chunk, end="")
