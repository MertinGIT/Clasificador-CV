import chromadb
from chromadb.config import Settings

settings = Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory="./chroma_storage"
)
chroma_client = chromadb.PersistentClient(path="./chroma_storage")
collection = chroma_client.get_or_create_collection(name="cv_embeddings")

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
