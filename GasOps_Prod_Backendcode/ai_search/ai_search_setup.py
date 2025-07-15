import asyncio
import os
import logging
from langchain_community.vectorstores.azuresearch import AzureSearch
from langchain_openai import AzureOpenAIEmbeddings
from langchain_core.documents import Document
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Load environment variables from .env file
load_dotenv()

# Azure configuration
azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
azure_openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
azure_openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION")
azure_deployment = os.getenv("AZURE_SEARCH_DEPLOYMENT") # Embedding deployment name

vector_store_address = os.getenv("AZURE_SEARCH_ENDPOINT")
vector_store_password = os.getenv("AZURE_SEARCH_KEY")
index_name = "cedemo"

# Initialize embeddings
embeddings = AzureOpenAIEmbeddings(
    azure_deployment=azure_deployment,
    openai_api_version=azure_openai_api_version,
    azure_endpoint=azure_endpoint,
    api_key=azure_openai_api_key,
)

# Function to initialize AzureSearch
def initialize_vector_store(index_name:str):
    logging.info("Initializing vector store...")
    return AzureSearch(
        azure_search_endpoint=vector_store_address,
        azure_search_key=vector_store_password,
        index_name=index_name,
        embedding_function=embeddings.embed_query,
        additional_search_client_options={"retry_total": 4},
    )

# Custom text splitter
class EmptyLineTextSplitter(CharacterTextSplitter):
    def split_text(self, text: str):
        return text.strip().split("\n\n")

# Function to process documents
def process_documents(file_path: str):
    logging.info(f"Loading documents from {file_path}...")
    loader = TextLoader(file_path, encoding="utf-8")
    documents = loader.load()

    logging.info("Splitting documents into chunks...")
    text_splitter = EmptyLineTextSplitter(chunk_size=1000, chunk_overlap=0)
    docs = [
        Document(page_content=chunk)
        for doc in documents
        for chunk in text_splitter.split_text(doc.page_content)
    ]

    logging.info(f"Created {len(docs)} document chunks.")
    return docs

# Function to perform similarity search
def perform_similarity_search(vector_store, query: str, k: int):
    logging.info("Performing similarity search...")
    results = vector_store.similarity_search(query=query, k=k, search_type="similarity")
    logging.info("Similarity search completed.")
    return results

# Main execution
if __name__ == "__main__":
    
    try:
        # vector_store = initialize_vector_store(index_name="cedemo")
        # docs = process_documents("cedemo_examples.txt")
        # asyncio.run(vector_store.add_documents(documents=docs))
        vector_store = initialize_vector_store(index_name="oamscm")
        docs = process_documents("oamscm_examples.txt")
        asyncio.run(vector_store.add_documents(documents=docs))
        
    finally:
        logging.info("Closing vector store.")
        if hasattr(vector_store, 'close'):
            vector_store.close()
