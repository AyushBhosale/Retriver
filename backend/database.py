from sqlalchemy import create_engine
from fastapi import Depends
from sqlalchemy.orm import sessionmaker,session
from sqlalchemy.ext.declarative import declarative_base
from typing import Annotated
URL="mysql+pymysql:///retriver"
engine = create_engine(URL)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[session, Depends(get_db)]
