# main.py
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from pipeline import run_pipeline

app = FastAPI(title="Agentic AI Backend")

origins = [
    "http://localhost:5173",
    'http://127.0.0.1:8000' 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Query(BaseModel):
    query: str

@app.post("/analyze")
async def analyze(query: Query):
    result = run_pipeline(query.query)
    return result
