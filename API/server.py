# main.py
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from pipeline import run_pipeline
from bson import ObjectId
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from Middleware.auth import hash_password, verify_password, create_access_token
from models.models import UserRegister, UserLogin, QueryRequest

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

client = "mongodb+srv://Linal:wicramadoc@cluster0.btgpfo9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
db = MongoClient['MarketResearcher_AgentiAI']

@app.post("/register")
def register(user: UserRegister):
    if db.users.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already exists")
    db.users.insert_one({
        "username": user.username,
        "email": user.email,
        "password": hash_password(user.password)
    })
    return {"message": "User registered successfully"}

@app.post("/login")
def login(user: UserLogin):
    db_user = db.users.find_one({"email": user.email})
    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token = create_access_token({"user_id": str(db_user["_id"])})
    return {"access_token": token, "username": db_user["username"]}

@app.post("/analyze")
async def analyze(query: Query):
    result = run_pipeline(query.query)
    return result
