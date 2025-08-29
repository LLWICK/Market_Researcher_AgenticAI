
import json
import os
from Data_Scraper_IR_Agent.DataScraperIR import collect_and_index, ir_search
from MessageStructure import AgentMessage 
from phi.agent import Agent
from phi.model.ollama import Ollama
from dotenv import load_dotenv
from phi.model.groq import Groq

def DataScraper_agent(query: str) -> AgentMessage:
    scrape_result = collect_and_index(query, k_search=10, k_index=6)
    hits = ir_search(query, limit=5)
    return AgentMessage(
        sender="DataScraperAgent",
        content={"query": query, "scraped_docs": scrape_result, "ir_hits": hits}
    )


def Summarizer_agent(message: AgentMessage) -> AgentMessage:
    query = message.content["query"]
    hits = message.content["ir_hits"]

    context_text = "\n".join([f"- {h['title']} ({h['source']})" for h in hits])
    agent = Agent(
        name="SummarizerAgent",
        model=Groq(id="openai/gpt-oss-20b"),
        instructions="Summarize competitors and market highlights.\n" + context_text
    )

    response = agent.run(query)
    return AgentMessage(
        sender="SummarizerAgent",
        content={"summary": str(response), "ir_hits": hits}
    )


def MarketResearch_agent(message: AgentMessage) -> AgentMessage:
    summary = message.content["summary"]
    hits = message.content["ir_hits"]

    context = f"Summary:\n{summary}\n\nKey Sources:\n"
    context += "\n".join([f"- {h['title']} ({h['source']})" for h in hits])

    agent = Agent(
        name="MarketResearchAgent",
        model=Groq(id="openai/gpt-oss-20b"),
        instructions="Analyze competitors, risks, and recommend strategies."
    )

    response = agent.run(context)
    return AgentMessage(
        sender="MarketResearchAgent",
        content={"research_insights": str(response)}
    )
