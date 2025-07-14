from fastapi import APIRouter, Depends, HTTPException
import os
import tempfile
import shutil
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
from pydantic import BaseModel
import logging
from database import db_dependency
from routes.utils import add_conversations, add_chat
from models import Conversation, message
load_dotenv()
router = APIRouter()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize LLM
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.7,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

# Pydantic models for request/response
class QueryRequest(BaseModel):
    question: str
    conversation_id: int

class QueryResponse(BaseModel):
    answer: str
    conversation_id: int
    sources: list = []
    conversation_id:int

# User dependency
user_dependency = Annotated[dict, Depends(get_current_user)]
form_data = Annotated[UploadFile, File(...)]

# Azure configuration
AZURE_CONNECTION_STRING = os.getenv("AZURE_CONNECTION_STRING")
CONTAINER_NAME = os.getenv("CONTAINER_NAME")

def get_embeddings():
    """Get embeddings instance with proper configuration"""
    return AzureOpenAIEmbeddings(
        model="text-embedding-3-small",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
    )

def create_vector_db(documents, username):
    """Create vector database from documents"""
    try:
        # Validate documents
        if not documents:
            raise ValueError("No documents were loaded from the PDF")
        
        logger.info(f"Processing {len(documents)} documents for user: {username}")
        
        # Filter empty documents
        non_empty_docs = [doc for doc in documents if doc.page_content.strip()]
        if not non_empty_docs:
            raise ValueError("All documents are empty")
        
        # Chunking
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, 
            chunk_overlap=200,  # Better overlap for context
            length_function=len
        )
        chunks = text_splitter.split_documents(non_empty_docs)
        
        if not chunks:
            raise ValueError("No chunks were created from documents")
        
        logger.info(f"Created {len(chunks)} chunks")
        
        # Create embeddings
        embeddings = get_embeddings()
        
        # Create FAISS index
        faiss_index = FAISS.from_documents(chunks, embedding=embeddings)
        
        # Create user directory if it doesn't exist
        user_dir = f"vector_stores/{username}"
        os.makedirs(user_dir, exist_ok=True)
        
        # Save FAISS index
        faiss_index.save_local(f"{user_dir}/faiss_index")
        
        logger.info(f"Successfully created vector database for user: {username}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating vector database: {str(e)}")
        raise

def load_vector_db(username):
    """Load existing vector database for a user"""
    try:
        user_dir = f"vector_stores/{username}"
        index_path = f"{user_dir}/faiss_index"
        
        if not os.path.exists(index_path):
            raise FileNotFoundError(f"No vector database found for user: {username}")
        
        embeddings = get_embeddings()
        faiss_index = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
        
        return faiss_index
        
    except Exception as e:
        logger.error(f"Error loading vector database: {str(e)}")
        raise

def create_conversation_chain(vector_store, conversation_id: int, db: db_dependency):
    """Create conversation chain with memory"""
    try:
        conversation_id=int(conversation_id)
        data = db.query(message).filter(message.conversation_id == conversation_id).all()
        
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )

        for msg in data:
            if msg.sender == "user":
                memory.chat_memory.add_user_message(msg.content)
            elif msg.sender == "ai":
                memory.chat_memory.add_ai_message(msg.content)
        print(memory.load_memory_variables({}))
        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 1}
            ),
            memory=memory,
            return_source_documents=True,
            verbose=True
        )
        return qa_chain

    except Exception as e:
        import traceback
        logger.error(f"Error creating conversation chain: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Failed to create conversation chain.")




# @router.post('/createConversation')
# async def create_conversation(username: str):


@router.post('/upload')
async def upload_file(file: form_data, user: user_dependency, db:db_dependency):
    """Upload PDF file and create vector database"""
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Upload to Azure Blob Storage
        prefix = f"{user['username']}/"
        blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
        blob_client = blob_service_client.get_blob_client(
            container=CONTAINER_NAME, 
            blob=f"{prefix}{file.filename}"
        )
        
        content = await file.read()
        blob_client.upload_blob(content, overwrite=True)
        
        # Download and process PDF
        pdf_bytes = blob_client.download_blob().readall()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(pdf_bytes)
            tmp_path = tmp.name
        
        # Load PDF documents
        loader = PyPDFLoader(file_path=tmp_path)
        documents = loader.load()
        # db.add()
        # Clean up temporary file
        os.remove(tmp_path)
        
        # Create vector database
        create_vector_db(documents, user['username'])
        conversation_id=add_conversations(db,user['id'],file.filename,f'analysis_{file.filename}')

        return {
            "message": f"Successfully uploaded and processed {file.filename}",
            "document_count": len(documents),
            "status": "ready_for_queries",
            "conversation_id" :  conversation_id
        }
        
    except Exception as e:
        logger.error(f"Error in upload_file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/query', response_model=QueryResponse)
async def query_documents(request: QueryRequest, user: user_dependency, db:db_dependency):
    """Query the vector database"""
    try:
        # Load user's vector database
        vector_store = load_vector_db(user['username'])
        
        # Create conversation chain
        qa_chain = create_conversation_chain(vector_store, request.conversation_id, db)
        
        # Query the chain
        result = qa_chain.invoke({"question": request.question})
        
        # Extract sources
        sources = []
        if 'source_documents' in result:
            sources = [
                {
                    "content": doc.page_content[:200] + "...",
                    "metadata": doc.metadata
                } 
                for doc in result['source_documents']
            ]
        request.conversation_id
        question = request.question
        answer = result['answer']

        add_chat(db, conversation_id=request.conversation_id, content=question, sender='user')
        add_chat(db, conversation_id=request.conversation_id, content=answer, sender='ai')
        return QueryResponse(
            answer=result['answer'],
            conversation_id=request.conversation_id or "default",
            sources=sources
            
        )
        
    except FileNotFoundError:
        raise HTTPException(
            status_code=404, 
            detail="No documents found. Please upload a PDF file first."
        )
    except Exception as e:
        logger.error(f"Error in query_documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/documents')
async def list_user_documents(user: user_dependency):
    """List all documents uploaded by the user"""
    try:
        prefix = f"{user['username']}/"
        blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
        container_client = blob_service_client.get_container_client(CONTAINER_NAME)
        
        documents = []
        for blob in container_client.list_blobs(name_starts_with=prefix):
            documents.append({
                "filename": blob.name.replace(prefix, ""),
                "size": blob.size,
                "last_modified": blob.last_modified
            })
        
        return {"documents": documents}
        
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete('/documents/{filename}')
async def delete_document(filename: str, user: user_dependency):
    """Delete a specific document"""
    try:
        prefix = f"{user['username']}/"
        blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
        blob_client = blob_service_client.get_blob_client(
            container=CONTAINER_NAME,
            blob=f"{prefix}{filename}"
        )
        
        blob_client.delete_blob()
        
        return {"message": f"Successfully deleted {filename}"}
        
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/health')
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "RAG API"}

@router.delete('/deleteVectorDB')
async def delete_vector(user: user_dependency):
    try:
        username = user['username']
        user_dir = f"vector_stores/{username}"

        if os.path.exists(user_dir):
            shutil.rmtree(user_dir)
            return {"message": f"Vector store for user '{username}' deleted successfully."}
        else:
            raise HTTPException(status_code=404, detail="Vector store not found.")
    except Exception as e:
        logger.error(f"Error deleting vector store: {str(e)}")
        raise HTTPException(status_code=500, detail="Error deleting vector store.")

@router.get('/getConversations')
def get_conversations(user:user_dependency, db:db_dependency):
    try:
        userId = user['id']
        data = db.query(Conversation).filter(Conversation.user_id==userId).all()
        return {'data':data}
    except Exception as e:
        logger.error(f"Error getting conversations: {str(e)}")

@router.get('/getMessages')
def get_conversations(conId:int, db:db_dependency):
    try:
        conId = int(conId)
        data = db.query(message).filter(message.conversation_id==conId).all()
        return {'data':data}
    except Exception as e:
        logger.error(f"Error getting conversations: {str(e)}")

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import Conversation, message  # Assuming correct import
from database import get_db  # Your db dependency

@router.delete('/deleteConversation')
async def delete_conversation(conId: int, db: Session = Depends(get_db)):
    try:
        # Step 1: Check if conversation exists
        conversation = db.query(Conversation).filter(Conversation.id == conId).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Step 2: Delete all related messages
        db.query(message).filter(message.conversation_id == conId).delete()

        # Step 3: Delete the conversation
        db.delete(conversation)

        # Step 4: Commit
        db.commit()

        return {"success": True, "message": "Conversation and related messages deleted successfully"}

    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"Error deleting conversation: {str(e)}"}
