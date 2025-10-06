from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from passlib.hash import bcrypt

SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")



def hash_password(password: str) -> str:
    if len(password.encode("utf-8")) > 72:
        password = password[:72]
    return bcrypt.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if len(plain_password.encode("utf-8")) > 72:
        plain_password = plain_password[:72]
    return bcrypt.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = timedelta(hours=2)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
