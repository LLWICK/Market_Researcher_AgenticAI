from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from pipeline import run_pipeline
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from Middleware.auth import hash_password, verify_password, create_access_token
from models.models import UserRegister, UserLogin, QueryRequest
from jose import jwt, JWTError

# =========================================
# FastAPI setup
# =========================================
app = FastAPI(title="Agentic AI Backend")

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:8000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================
# Database setup
# =========================================
client = MongoClient(
    "mongodb+srv://Linal:wicramadoc@cluster0.btgpfo9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",
    server_api=ServerApi('1')
)
db = client["MarketResearcher_AgentiAI"]

# =========================================
# Models
# =========================================
class Query(BaseModel):
    query: str

SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"

# =========================================
# JWT authentication helper
# =========================================
def get_current_user(authorization: str = Header(...)):
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError("Invalid token scheme")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["user_id"]
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# =========================================
# Auth Routes
# =========================================
@app.post("/register") 
def register(user: UserRegister):
    if db.users.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already exists")
    db.users.insert_one({
        "username": user.username,
        "email": user.email,
        "password": user.password
    })
    return {"message": "User registered successfully"}

@app.post("/login")
def login(user: UserLogin):
    db_user = db.users.find_one({"email": user.email})
    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token = create_access_token({"user_id": str(db_user["_id"])})
    return {"access_token": token, "username": db_user["username"]}

# =========================================
# Analyze Route (Protected)
# =========================================
@app.post("/analyzed")
async def analyze(query: Query, user_id: str = Depends(get_current_user)):
    result = run_pipeline(query.query)

    # store query + result in MongoDB for history
    db.queries.insert_one({
        "user_id": user_id,
        "query": query.query,
        "response": result
    })

    return result

# =========================================
# User history
# =========================================
@app.get("/history")
async def get_history(user_id: str = Depends(get_current_user)):
    history = list(db.queries.find({"user_id": user_id}))
    for h in history:
        h["_id"] = str(h["_id"])
    return {"history": history}


@app.post("/analyze")
async def analyze(query: Query):
    result = run_pipeline(query.query)
    return result
