

# 🧠 Agentic AI Market Researcher

An AI-powered Market Research System that combines intelligent agents, web scraping, and retrieval-augmented generation (RAG) to deliver deep market insights — instantly.

Built using FastAPI, React, MongoDB, and ChromaDB, this system allows users to:

Query multiple AI agents for competitor, social, and trend analysis.

Upload personal documents for AI-powered contextual search (RAG).

Manage user authentication, chat history, and custom document knowledge bases.

🚀 Features

✅ AI Agent Team – Multiple collaborating AI agents analyze web data, trends, and events.
✅ RAG Agent Integration – Upload PDFs or text documents to enhance contextual understanding.
✅ Dual Pipeline Toggle – Switch between the IR Scraper Pipeline and RAG Pipeline.
✅ User Authentication – Secure JWT-based user registration and login.
✅ Personal Chat History – Persistent chat storage per user in MongoDB.
✅ Vector Database – ChromaDB-powered embedding storage for personalized RAG responses.
✅ Frontend Dashboard – Interactive research interface built with React and Tailwind CSS.

🧩 Tech Stack
Layer	Technology

Agent integration - Phi Data (Agno) framework
AI Models	- Groq / Llama 3.3, Open AI 
Authentication	JWT Tokens (FastAPI + passlib)
Frontend	React, Tailwind CSS, Axios
Backend	FastAPI, Python 3.10+
Database	MongoDB (User Auth + Chat History)
Vector Store	ChromaDB (with SentenceTransformer embeddings)


If you are running the cloned repository for the first time, follow the given instructions

first you should install uv on your pc



# Run the project on your PC

backend - 
cd API
// fastapi run server.py

frontend - 
cd FRONTEND
// npm install
// npm run dev



