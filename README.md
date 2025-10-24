

#  Agentic AI Market Researcher

An AI-powered Market Research System that combines intelligent agents, web scraping, and retrieval-augmented generation (RAG) to deliver deep market insights — instantly.

Built using FastAPI, React, MongoDB, and ChromaDB, this system allows users to:

Query multiple AI agents for competitor, social, and trend analysis.

Upload personal documents for AI-powered contextual search (RAG).

Manage user authentication, chat history, and custom document knowledge bases.

 Features - 

1. AI Agent Team – Multiple collaborating AI agents analyze web data, trends, and events.
2. RAG Agent Integration – Upload PDFs or text documents to enhance contextual understanding.
3. Dual Pipeline Toggle – Switch between the IR Scraper Pipeline and RAG Pipeline.
4. User Authentication – Secure JWT-based user registration and login.
5. Personal Chat History – Persistent chat storage per user in MongoDB.
6. Vector Database – ChromaDB-powered embedding storage for personalized RAG responses.
7. Frontend Dashboard – Interactive research interface built with React and Tailwind CSS.

 Tech Stack- 
Layer	Technology

1. Agent integration - Phi Data (Agno) framework.
2. AI Models	- Groq / Llama 3.3, Open AI .
3. Authentication	JWT Tokens (FastAPI + passlib).
4. Frontend	React, Tailwind CSS, Axios.
5. Backend	FastAPI, Python 3.10+.
6. Database	MongoDB (User Auth + Chat History).
7. Vector Store	ChromaDB (with SentenceTransformer embeddings).


If you are running the cloned repository for the first time, follow the given instructions

first you should install uv on your pc



# Run the project on your PC

uv pip install -r requirements.txt

backend - 
1. cd API
2. fastapi run server.py

frontend - 
1. cd FRONTEND
2.  npm install
3. npm run dev



