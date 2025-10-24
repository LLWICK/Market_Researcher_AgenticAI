

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

# Repo Structure
```

Market_Researcher_AgenticAI/
├── API/                                   # Backend API (FastAPI-based)
│   ├── Middleware/
│   │   └── auth.py                        # JWT authentication middleware
│   ├── models/
│   │   └── models.py                      # MongoDB schemas
│   ├── storage/                           # Local storage or uploads (optional)
│   ├── vectorstore/                       # Vector DB initialization and persistence
│   ├── Agent_setup.py                     # RAG + Agent backend setup
│   ├── MongoDBCon.py                      # MongoDB connection helper
│   ├── pipeline.py                        # FastAPI route orchestration for RAG pipeline
│   └── server.py                          # Main FastAPI app entry point

├── FRONTEND/                              # Frontend (React + Vite + Tailwind)
│   ├── public/
│   ├── src/
│   │   ├── assets/                        # Images, icons
│   │   ├── components/                    # UI Components (Cards, Charts, Tables, etc.)
│   │   ├── pages/                         # App pages (Dashboard, Library, etc.)
│   │   ├── routes/                        # React Router routes
│   │   ├── App.jsx                        # Root React component
│   │   ├── App.css                        # Global styles
│   │   ├── index.css                      # Tailwind setup
│   │   └── main.jsx                       # Entry point
│   ├── package.json
│   ├── vite.config.js
│   └── README.md

├── RAG_agent/                             # Retrieval-Augmented Generation logic
│   └── Rag_Agent.py                       # Core RAG pipeline for contextual retrieval

├── SocialMedia_Trend_Agent/               # Social trend collection and analysis
│   ├── cookies.json
│   ├── sns scrape_patch.py                # Patching for sns scraping
│   ├── SocialAgent.py                     # Handles trend scraping, sentiment tagging
│   └── test.py

├── Trend_Analyzer_Agent/
│   └── Trend_Analyzer_Agent.py            # Analyzes extracted trend data

├── Data_Scraper_IR_Agent/                 # Web/IR data scraping module
│   └── (Python scripts for data scraping and preprocessing)

├── Market_Researcher_Agent/               # Agent coordinating insights and synthesis
│   └── (Core scripts for overall market research logic)

├── Competitor_Comparison_Agent/           # Agent comparing competitor performance
│   └── (Analysis helpers for competitor metrics)

├── utills/                                # Utility functions
│   ├── cleaning.py                        # Data cleaning helpers
│   ├── extractUtills.py                   # Extraction and parsing logic
│   ├── scope_utils.py                     # Scope filtering helpers
│   ├── ta_helpers.py                      # Technical analysis helper functions
│   └── ticker_cache.py                    # Ticker caching utilities

├── vectorStore/
│   └── chroma_manager.py                  # ChromaDB vector store management

├── storage/                               # Cache and index storage
│   ├── cache/
│   └── index/

├── pre_testing/                           # Jupyter notebooks (prototype testing)
│   ├── Kasuni.ipynb
│   ├── Linal.ipynb
│   ├── Thushan.ipynb
│   └── Tiyani.ipynb
├── agent_protocol.py                      # Agent communication protocol
├── AgentTeam.py                           # Defines all AI agents and interactions
├── MessageStructure.py                    # Agent message format schema
├── requirements.txt                        # Backend dependencies
├── TrendChart2.py                          # Data visualization or testing script
└── README.md

```
# Contributors 

1. WICKRAMAARACHCHI  L T B - Data scraper pipeline and RAG agent, vector database
2. SENARATNA S T S - Market researcher and summarizer agent
3. GURUSINGHE T M - Trend analyzer and event spike agents
4. JAYATHILAKA K A - Social Trend analyzer (Reddit API) agent and Fast API setup for the backend



If you are running the cloned repository for the first time, follow the given instructions

first you should install UV on your pc



# Run the project on your PC

uv pip install -r requirements.txt

backend - 
1. cd API
2. fastapi run server.py

frontend - 
1. cd FRONTEND
2.  npm install
3. npm run dev



