import os
import tempfile
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import AzureOpenAIEmbeddings
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_groq import ChatGroq  # ✅ Groq import

load_dotenv()

# Azure Blob Storage
AZURE_CONNECTION_STRING = os.getenv("AZURE_CONNECTION_STRING")
CONTAINER_NAME = os.getenv("CONTAINER_NAME")
BLOB_NAME = "PDF - Wikipedia.pdf"

blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
blob_client = blob_service_client.get_container_client(CONTAINER_NAME).get_blob_client(BLOB_NAME)
pdf_bytes = blob_client.download_blob().readall()

with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
    tmp.write(pdf_bytes)
    tmp_path = tmp.name  

loader = PyPDFLoader(file_path=tmp_path)
documents = loader.load()
os.remove(tmp_path)

# Chunking
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
chunks = text_splitter.split_documents(documents)

# Embeddings using Azure OpenAI
embeddings = AzureOpenAIEmbeddings(model="text-embedding-3-small")
faiss_index = FAISS.from_documents(chunks, embedding=embeddings)
faiss_index.save_local("faiss_index")

# Chat memory
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# ✅ Groq LLM setup
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.7,
    max_tokens=None,  # or set a specific output token limit
    # reasoning_format="parsed",  # optional: enables structured reasoning output
    timeout=None,
    max_retries=2,
)

# Conversational Retrieval Chain with Groq
qa_chain = ConversationalRetrievalChain.from_llm(
    llm=llm,
    retriever=faiss_index.as_retriever(),
    memory=memory
)

# Query
response = qa_chain.run("What are the symptoms of Parkinson's?")
print(response)
