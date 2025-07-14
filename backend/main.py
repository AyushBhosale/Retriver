from fastapi import FastAPI
from database import Base, engine
from routes import auth, rag, trial
from fastapi.middleware.cors import CORSMiddleware
Base.metadata.create_all(bind=engine)
app=FastAPI()
origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router,prefix='/auth',tags=['auth'])
app.include_router(trial.router,prefix='/rag',tags=['rag'])