import os
from chromadb import PersistentClient
from chromadb.utils import embedding_functions

class ChromaManager:
    def __init__(self, base_path="vectorstore"):
        os.makedirs(base_path, exist_ok=True)
        self.base_path = base_path
        self.client = PersistentClient(path=base_path)
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

    def get_collection(self, user_id: str):
        return self.client.get_or_create_collection(
            name=f"user_{user_id}",
            embedding_function=self.embedding_fn
        )

    def add_document(self, user_id: str, doc_id: str, text: str, metadata: dict = None):
        collection = self.get_collection(user_id)
        collection.add(documents=[text], ids=[doc_id], metadatas=[metadata or {}])

    def query(self, user_id: str, query: str, top_k: int = 3):
        collection = self.get_collection(user_id)
        return collection.query(query_texts=[query], n_results=top_k)
    

    def delete_document(self, user_id: str, doc_id: str):
        collection = self.get_collection(user_id)
        collection.delete(ids=[doc_id])

