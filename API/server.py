from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from pipeline import run_pipeline
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from Middleware.auth import hash_password, verify_password, create_access_token
from models.models import UserRegister, UserLogin, QueryRequest,ChatHistory
from jose import jwt, JWTError
from bson import ObjectId

# Custom encoder for ObjectId → string
def serialize_doc(doc):
    """Converts MongoDB document ObjectIds to strings recursively."""
    if isinstance(doc, list):
        return [serialize_doc(d) for d in doc]
    if isinstance(doc, dict):
        return {k: serialize_doc(v) for k, v in doc.items()}
    if isinstance(doc, ObjectId):
        return str(doc)
    return doc


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
    if not db_user or not  (user.password == db_user["password"]):
    #if not db_user or not verify_password(user.password, db_user["password"]):
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
@app.post("/save_chat")
def save_chat(chat: ChatHistory):
    db.chat_history.insert_one(chat.dict(by_alias=True, exclude_none=True))
    return {"message": "Chat saved successfully"}

@app.get("/get_chats/{user_id}")
def get_chats(user_id: str):
    chats = list(db.chat_history.find({"user_id": user_id}))
    chats = serialize_doc(chats)
    return {"history": chats}

@app.delete("/delete_chat/{chat_id}")
def delete_chat(chat_id: str):
    """Delete a specific chat from history using its MongoDB ObjectId."""
    result = db.chat_history.delete_one({"_id": ObjectId(chat_id)})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Chat not found")

    return {"message": f"Chat {chat_id} deleted successfully"}



@app.post("/analyze")
async def analyze(query: Query):
    result = run_pipeline(query.query)
    return result


##############################################################################
#RAG Agent

# routes/rag_routes.py

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import tempfile, shutil, os, sys
from PyPDF2 import PdfReader

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from RAG_agent.Rag_Agent import RAGAgent

router = APIRouter()
rag_agent = RAGAgent()

def extract_text_from_pdf(path):
    reader = PdfReader(path)
    return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])


@app.post("/upload-document")
async def upload_document(user_id: str = Form(...), file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    text = (
        extract_text_from_pdf(tmp_path)
        if file.filename.endswith(".pdf")
        else open(tmp_path, encoding="utf-8").read()
    )

    rag_agent.add_document(user_id=user_id, text=text, metadata={"filename": file.filename})
    return {"message": f"{file.filename} added successfully for user {user_id}"}


@app.get("/rag/documents")
async def list_documents(user_id: str):
    docs = rag_agent.get_user_documents(user_id)
    return {"documents": docs}


@app.delete("/rag/delete-document/{user_id}/{doc_id}")
async def delete_document(user_id: str, doc_id: str):
    success = rag_agent.delete_document(user_id, doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": f"Document {doc_id} deleted for user {user_id}"}



@app.post("/rag/query")
async def query_documents(user_id: str = Form(...), query: str = Form(...)):
    """Run a user query against their uploaded docs."""
    try:
        answer = rag_agent.query(user_id, query)
        return {"response": answer}
    except Exception as e:
        return {"error": str(e)}