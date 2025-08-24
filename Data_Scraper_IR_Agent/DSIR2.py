import requests
from bs4 import BeautifulSoup
from phi.assistant import Assistant
from phi.tools.toolkit import Toolkit
#from phi.llm.openai import OpenAIChat
from pydantic import BaseModel, Field
import json
import logging
from phi.model.groq import Groq
from phi.model.ollama import Ollama


# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class DataScraperTools(Toolkit):
    """
    A collection of tools for the Data Scraper Agent.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.register(self.scrape_website)
        self.register(self.preprocess_data)

    def scrape_website(self, url: str) -> str:
        """
        Scrapes a website and returns the content.
        This function performs web scraping and returns the main text content.
        """
        logging.info(f"Scraping content from URL: {url}")
        try:
            # Add headers to mimic a browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status() # Raise an error for bad status codes
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract text from common tags, like paragraphs and headers
            text_content = ' '.join(p.get_text() for p in soup.find_all(['p', 'h1', 'h2', 'h3']))
            logging.info(f"Scraping successful. Extracted {len(text_content)} characters.")

            # Placeholder for security: Input sanitization
            # In a real-world scenario, you would sanitize the scraped data to prevent XSS or other vulnerabilities.

            return text_content[:2000] # Return a truncated version for a demo
        except requests.RequestException as e:
            logging.error(f"Error scraping {url}: {e}")
            return f"Error: Could not scrape content from {url}. Reason: {e}"

    def preprocess_data(self, raw_data: str) -> str:
        """
        Cleans and preprocesses raw, scraped text data.
        This is a placeholder for NLP cleaning tasks like removing stopwords,
        tokenization, and handling special characters.
        """
        logging.info("Preprocessing raw data...")
        # Placeholder for data cleaning (e.g., removing HTML tags, extra spaces)
        cleaned_data = " ".join(raw_data.split())
        logging.info("Data preprocessing complete.")
        return cleaned_data

class DataScraperAgent(Assistant):
    """
    Agent responsible for scraping and preprocessing data.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "Data Scraper Agent"
        self.role = "Acts as the system's data collector and retriever."
        self.llm = Groq(id="deepseek-r1-distill-llama-70b") # Use your preferred LLM
        self.tools = [DataScraperTools()]
        self.instructions = [
            "You are a data scraper and information retrieval agent.",
            "Your main function is to scrape content from a given URL.",
            "Use the `scrape_website` tool to retrieve data.",
            "After scraping, use the `preprocess_data` tool to clean the text.",
            "Return the preprocessed, cleaned data as a JSON object with a 'scraped_data' key.",
            "If the URL is invalid, return an error message."
        ]
    
    def run_with_url(self, url: str) -> str:
        """
        Executes the agent's full scraping and processing workflow for a given URL.
        """
        logging.info(f"Starting DataScraperAgent workflow for URL: {url}")
        prompt = f"Scrape and preprocess the content from the following URL: {url}"
        response = self.print_response(prompt, stream=False)
        return response