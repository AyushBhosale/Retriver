# Imports
from fastapi import HTTPException, Depends, status, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from models import User, UserBase
from database import engine, Base, SessionLocal, db_dependency
from sqlalchemy.orm import Session
from typing import Annotated
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
import os
from dotenv import load_dotenv
from fastapi import Request
router = APIRouter()
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated = 'auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')
load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM')

def authenticate_user(username, password, db:db_dependency):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    if not bcrypt_context.verify(password ,user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    return user

def create_access_token(user, expires_delta: timedelta):
    encode={'username': user.username, 'id': user.id}
    expire=datetime.now(timezone.utc) + expires_delta
    return jwt.encode({'exp': expire, 'data': encode}, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(db: db_dependency, token: str = Depends(oauth2_bearer)):
    payload=jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    data = payload.get("data")
    username: str = data.get('username')
    user_id: int = data.get('id')
    if username is None or user_id is None:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    user = db.query(User).filter(User.username == username).first()
    return {
        'username': username,
        'id': user_id,
    }

@router.post('/register')
async def register(db:db_dependency, data:UserBase):
    data=data.model_dump()
    data['hashed_password']=bcrypt_context.hash(data['hashed_password'])
    new_user = User(**data)
    db.add(new_user)
    db.commit()
    return {'message': 'User created'}

@router.post('/token')
async def login_for_access_token(db:db_dependency, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    try:
        user = authenticate_user(form_data.username, form_data.password, db)
        token = create_access_token(user, timedelta(minutes=30))
        return { "access_token": token, "token_type": "bearer" }
    except HTTPException as e:
        raise e
    