from agent_protocol import AgentProtocol
from phi.agent import Agent
from phi.model.groq import Groq
from dotenv import load_dotenv

load_dotenv()

protocol = AgentProtocol()

# Agent 1: Data Scraper
def DataScraper_agent(query: str):
    print(f"[DataScraperAgent] Running for query: {query}")
    result = {"query": query, "docs": [f"Doc {i} about {query}" for i in range(5)]}
    protocol.send("DataScraperAgent", "SummarizerAgent", result)
    return result

# Agent 2: Summarizer
def Summarizer_agent():
    data = protocol.receive("SummarizerAgent")
    query, docs = data["query"], data["docs"]

    context = "\n".join(docs)
    agent = Agent(
        name="SummarizerAgent",
        model=Groq(id="openai/gpt-oss-20b"),
        instructions=f"Summarize documents about: {query}"
    )
    response = agent.run(context)

    summary = str(response) if not hasattr(response, "output_text") else response.output_text
    result = {"summary": summary}
    protocol.send("SummarizerAgent", "MarketResearchAgent", result)
    return result

# Agent 3: Market Research
def MarketResearch_agent():
    data = protocol.receive("MarketResearchAgent")
    summary = data["summary"]

    agent = Agent(
        name="MarketResearchAgent",
        model=Groq(id="openai/gpt-oss-20b"),
        instructions="Analyze competitors, risks, and opportunities."
    )
    response = agent.run(summary)
    insights = str(response) if not hasattr(response, "output_text") else response.output_text

    protocol.send("MarketResearchAgent", "TrendAnalyzerAgent", {"insights": insights})
    return {"insights": insights}

# Agent 4: Trend Analyzer
def TrendAnalyzer_agent():
    data = protocol.receive("TrendAnalyzerAgent")
    insights = data["insights"]

    agent = Agent(
        name="TrendAnalyzerAgent",
        model=Groq(id="openai/gpt-oss-20b"),
        instructions="Extract key trends and patterns."
    )
    response = agent.run(insights)
    trends = str(response) if not hasattr(response, "output_text") else response.output_text

    return {"trends": trends}
