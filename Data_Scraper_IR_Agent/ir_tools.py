from agno.tool import Tool
from typing import Dict, Any
from DataScraperIR import collect_and_index, ir_search

class InformationRetrieverTool(Tool):
    """
    An Agno Tool that wraps a complete Information Retrieval (IR) pipeline.
    It can scrape new data from the web and retrieve relevant information from a local index.
    """
    def __init__(self):
        super().__init__(
            name="InformationRetrieverTool",
            description="Performs web searches, scrapes articles, and retrieves relevant documents from a local knowledge base. Use this tool to find and analyze information."
        )

    def run(self, action: str, query: str) -> Dict[str, Any]:
        """
        Executes the IR pipeline based on a specified action.
        
        Args:
            action: The action to perform. Can be 'collect' or 'retrieve'.
            query: The search query.
            
        Returns:
            A dictionary with the results of the action.
        """
        if action == "collect":
            # This action scrapes the web and builds the local index.
            result = collect_and_index(query)
            return {"status": "success", "message": f"Collected and indexed {result['indexed']} new documents for query: {query}"}
        
        elif action == "retrieve":
            # This action searches the local index for existing documents.
            retrieved_docs = ir_search(query)
            if not retrieved_docs:
                return {"status": "error", "message": "No relevant documents found in the local index."}
            
            return {"status": "success", "results": retrieved_docs}
        
        else:
            return {"status": "error", "message": f"Invalid action: {action}. Please use 'collect' or 'retrieve'."}