from fastapi import FastAPI, HTTPException
from pydantic import BaseModel,Field
from Data_Scraper_IR_Agent.DSIR2 import DataScraperAgent
import uvicorn
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

app = FastAPI(
    title="Agentic AI System API",
    description="An API for a multi-agent system built with phidata and FastAPI."
)

# Initialize the Data Scraper Agent
data_scraper_agent = DataScraperAgent()

class ScrapeRequest(BaseModel):
    url: str = Field(..., description="The URL to scrape.")

@app.post("/scrape")
async def scrape_data(request: ScrapeRequest):
    """
    API endpoint to trigger the Data Scraper Agent to scrape a URL.
    """
    logging.info(f"Received request to scrape URL: {request.url}")
    try:
        # Run the agent's workflow
        raw_output = data_scraper_agent.run_with_url(request.url)
        # Assuming the agent returns a JSON string, parse it
        # Note: The agent's output might vary based on LLM behavior.
        # This is a robust way to handle it.
        try:
            result = json.loads(raw_output)
        except json.JSONDecodeError:
            result = {"scraped_data": raw_output}
        
        logging.info("Scraping and processing complete.")
        return {"status": "success", "data": result}
    except Exception as e:
        logging.error(f"Error during scraping process: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("serverTest:app", host="0.0.0.0", port=8000, reload=True)