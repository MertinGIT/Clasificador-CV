# vector_store.py

import chromadb
from chromadb.config import Settings

client = chromadb.Client(Settings(
    chroma_db_impl="duckdb+parquet", 
    persist_directory="./chroma_db"
))

collection = client.get_or_create_collection(name="cv_embeddings")

def add_cv_to_chroma(cv_id: str, content: str, metadata: dict):
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    embedding = model.encode(content).tolist()
    
    collection.add(
        documents=[content],
        metadatas=[metadata],
        ids=[str(cv_id)],
        embeddings=[embedding]
    )

def query_similar_cvs(query_text: str, n_results=5):
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    query_embedding = model.encode(query_text).tolist()
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )
    return results
