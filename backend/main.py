from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import Column, Integer, String, create_engine, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import chromadb
from chromadb.config import Settings
import pdfplumber
import uuid
import os
from dotenv import load_dotenv
import os


load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# ========== CONFIGURACIÓN BÁSICA ==========
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Base de datos local con SQLAlchemy
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ========== MODELO SQLALCHEMY ==========
class CV(Base):
    __tablename__ = "cvs"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    content = Column(Text)
    role = Column(String)
    experience = Column(String)

Base.metadata.create_all(bind=engine)

# ========== CHROMA DB ==========
chroma_client = chromadb.Client(Settings(chroma_db_impl="duckdb+parquet", persist_directory="./chroma_storage"))
collection = chroma_client.get_or_create_collection(name="cv_embeddings")

# ========== UTILIDAD PARA EXTRAER TEXTO DE PDF ==========
def extract_text_from_pdf(file) -> str:
    with pdfplumber.open(file) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    return text

# ========== ENDPOINT PARA SUBIR UN CV ==========
@app.post("/upload")
def upload_cv(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF")

    # Guardar archivo temporal
    temp_file = f"temp_{uuid.uuid4()}.pdf"
    with open(temp_file, "wb") as f:
        f.write(file.file.read())

    # Extraer texto
    content = extract_text_from_pdf(temp_file)

    # Simular clasificación usando palabras clave
    role = "Desarrollador" if "Python" in content else "Otro"
    experience = "Senior" if "5 años" in content else "Junior"

    # Guardar en SQLite
    db = SessionLocal()
    db_cv = CV(filename=file.filename, content=content, role=role, experience=experience)
    db.add(db_cv)
    db.commit()
    db.refresh(db_cv)

    # Guardar embedding en ChromaDB (simulado como texto plano por ahora)
    collection.add(
        documents=[content],
        metadatas=[{"role": role, "experience": experience}],
        ids=[str(db_cv.id)]
    )

    os.remove(temp_file)
    return {"status": "ok", "id": db_cv.id, "role": role, "experience": experience}

# ========== ENDPOINT PARA BUSCAR CANDIDATOS ==========
@app.get("/search")
def search_cvs(query: str):
    results = collection.query(query_texts=[query], n_results=5)
    return {"matches": results}