from fastapi import APIRouter, Depends
import os
import tempfile
from fastapi import FastAPI, File, UploadFile
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import AzureOpenAIEmbeddings
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_groq import ChatGroq
from routes.auth import get_current_user
from typing import Annotated
load_dotenv()
router = APIRouter()

llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.7,
        max_tokens=None,  # or set a specific output token limit
        # reasoning_format="parsed",  # optional: enables structured reasoning output
        timeout=None,
        max_retries=2,
    )

def create_vector_db(documents, username):
    if not documents:
        raise ValueError("No documents were loaded from the PDF")
# Chunking
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    chunks = text_splitter.split_documents(documents)
# Embeddings using Azure OpenAI
    embeddings = AzureOpenAIEmbeddings(model="text-embedding-3-small")
    faiss_index = FAISS.from_documents(chunks, embedding=embeddings)
    faiss_index.save_local(f"{username}/faiss_index")


user_dependency = Annotated[dict,Depends(get_current_user)]
AZURE_CONNECTION_STRING = os.getenv("AZURE_CONNECTION_STRING")
CONTAINER_NAME = os.getenv("CONTAINER_NAME")
form_data= Annotated[UploadFile, File(...)]

@router.post('/upload')
async def upload_file(file: form_data,user: user_dependency):
    prefix = f"{user['username']}/"
    BLOB_NAME=file.filename
    blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
    blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=f"{prefix}{file.filename}")
    content = await file.read()
    blob_client.upload_blob(content, overwrite=True)
    blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
    blob_client = blob_service_client.get_container_client(CONTAINER_NAME).get_blob_client(f"{prefix}{file.filename}")
    pdf_bytes = blob_client.download_blob().readall()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(pdf_bytes)
        tmp_path = tmp.name  

    loader = PyPDFLoader(file_path=tmp_path)
    documents = loader.load()
    os.remove(tmp_path)
    create_vector_db(documents,user['username'])
    return {"message": f"Uploaded {file.filename} to Azure Blob Storage"}