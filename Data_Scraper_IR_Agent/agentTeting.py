from phi.agent import Agent, Tool
from phi.model.groq import Groq
from DataScraperIR import collect_and_index, ir_search
import os
from dotenv import load_dotenv
load_dotenv()

# Initialize Phi LLM
llm = Groq(model="openai/gpt-oss-120b", api_key=os.getenv("GROQ_API_KEY"))

# Properly named Python functions
def scrape_marketing_data(prompt: str) -> str:
    return collect_and_index(prompt, k_search=15, k_index=8)

def search_index(query: str) -> list:
    return ir_search(query)[:5]

# Wrap as Tools
scrape_tool = Tool(
    type="function",
    name="ScrapeMarketingData",
    description="Scrapes & indexes marketing data based on user prompt",
    func=scrape_marketing_data  # regular function with proper name
)

search_tool = Tool(
    type="function",
    name="SearchIndex",
    description="Searches indexed documents for insights",
    func=search_index
)

# Create the agent with tools
marketing_agent = Agent(
    name="Marketing Research Agent",
    
    model=Groq(id="deepseek-r1-distill-llama-70b"),
    instructions=(
        "You are a marketing research assistant. "
        "Your job is to fetch and summarize the latest marketing data using the provided scraping & IR tools."
    ),
    tools=[scrape_tool, search_tool]
)

# Run the agent with a prompt
response = marketing_agent.run(
    "Get me the latest 2025 digital marketing spend forecasts in Asia "
    "and summarize the top insights."
)
print(response)
