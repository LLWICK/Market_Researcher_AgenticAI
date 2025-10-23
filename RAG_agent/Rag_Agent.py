# RAG_agent/Rag_Agent.py
from phi.agent import Agent
from phi.model.groq import Groq
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from vectorStore.chroma_manager import ChromaManager


class RAGAgent:
    def __init__(self):
        self.vector_manager = ChromaManager()

    def add_document(self, user_id: str, text: str, metadata=None):
        doc_id = metadata.get("filename", "doc")
        self.vector_manager.add_document(user_id, doc_id, text, metadata)

    def query(self, user_id: str, query: str):
        results = self.vector_manager.query(user_id, query)
        context = "\n".join([d for d in results["documents"][0]])

        agent = Agent(
            name="RAGAgent",
            model=Groq(id="llama-3.3-70b-versatile"),
            instructions="Use the provided context to answer the user's query accurately.",
        )

        response = agent.run(f"Context:\n{context}\n\nQuestion:\n{query}")
        return response.content if response else "No answer found."

    def get_user_documents(self, user_id: str):
        """Return metadata of all user docs in vectorstore"""
        collection = self.vector_manager.get_collection(user_id)
        data = collection.get()
        return [
            {
                "id": doc_id,
                "metadata": meta,
            }
            for doc_id, meta in zip(data["ids"], data["metadatas"])
        ]
    

    def delete_document(self, user_id: str, doc_id: str):
        """Delete a document from a user's Chroma collection"""
        try:
            collection = self.vector_manager.get_collection(user_id)
            collection.delete(ids=[doc_id])
            return True
        except Exception as e:
            print(f"Error deleting doc {doc_id}: {e}")
            return False

