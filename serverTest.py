# agent2_scraper.py
from fastapi import FastAPI
import uvicorn
import json
from Data_Scraper_IR_Agent.agentTeting import DataScraper_agent

app = FastAPI()

@app.post("/scrape")
def scrape(query: str):
    result = DataScraper_agent(query)
    return result  # already JSON structured

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
