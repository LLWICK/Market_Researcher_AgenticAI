# agent2_scraper.py
from fastapi import FastAPI
import uvicorn
import json
from Data_Scraper_IR_Agent.agentTeting import Scraper_agent

app = FastAPI()

@app.post("/scrape")
def scrape(query: str):
    result = Scraper_agent(query)
    return result  # already JSON structured

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
