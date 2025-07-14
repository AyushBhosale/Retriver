from database import SessionLocal, engine, Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from pydantic import BaseModel, Field, EmailStr
from typing import Annotated
from datetime import datetime,timezone

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(10), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)


class UserBase(BaseModel):
    username: Annotated[str, Field(...,max_length=10)]
    email: Annotated[EmailStr, Field(...)]
    hashed_password : Annotated[str, Field(...)]

class LoginUserBase(BaseModel):
    username: Annotated[str, Field(...,max_length=10)]
    hashed_password : Annotated[str, Field(...)]

class Conversation(Base):
    __tablename__ = 'conversations'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    file_name = Column(String(255), nullable=False)
    title = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))

class message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'))
    content = Column(String(10000), nullable=False)
    sender = Column(String(10), nullable=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))