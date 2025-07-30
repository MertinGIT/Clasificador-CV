from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import engine, SessionLocal
import chromadb
from chromadb.config import Settings
import pdfplumber
import uuid
import os
from dotenv import load_dotenv
from ollama import Client as OllamaClient
from chromadb.config import Settings
from model import Base, CV
import chromadb
from UniversalCVClassifier import UniversalCVClassifier
from typing import Dict, List, Optional

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

# Base de datos con SQLAlchemy
Base.metadata.create_all(bind=engine)

# Inyectamos la dependencia
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_classifier(db: Session = Depends(get_db)):
    return UniversalCVClassifier(db)

# ========== CHROMA DB ==========
settings = Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory="./chroma_storage"
)
chroma_client = chromadb.PersistentClient(path="./chroma_storage")
collection = chroma_client.get_or_create_collection(name="cv_embeddings")

# ========== UTILIDAD PARA EXTRAER TEXTO DE PDF ==========
def extract_text_from_pdf(file) -> str:
    try:
        with pdfplumber.open(file) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        return text.strip()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al procesar PDF: {str(e)}") 

# ========== ENDPOINT PARA SUBIR UN CV ==========
@app.post("/upload")
async def upload_cv(
    file: UploadFile = File(...),
    classifier: UniversalCVClassifier = Depends(get_classifier)
):
    """
    Sube y procesa un CV PDF usando el UniversalCVClassifier
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF")

    # Guardar archivo temporal
    temp_file = f"temp_{uuid.uuid4()}.pdf"
    try:
        # Guardar archivo temporalmente
        with open(temp_file, "wb") as f:
            content = await file.read()
            f.write(content)

        # Extraer texto del PDF
        text_content = extract_text_from_pdf(temp_file)
        
        if not text_content.strip():
            raise HTTPException(status_code=400, detail="No se pudo extraer texto del PDF")

        # Procesar CV con el clasificador avanzado
        cv = classifier.save_cv(text_content, file.filename)
        
        # Crear metadata para ChromaDB
        metadata = {
            "cv_id": cv.id,
            "role": cv.rol.nombre if cv.rol else "No especificado",
            "experience": f"{cv.anhos_experiencia} años",
            "seniority": classifier.classify_seniority(text_content, cv.anhos_experiencia),
            "industry": cv.industria.nombre if cv.industria else "No especificado",
            "score": cv.overall_score,
            "skills_count": len(cv.habilidades),
            "languages_count": len(cv.lenguajes)
        }
        
        # Guardar en ChromaDB para búsquedas semánticas
        collection.add(
            documents=[text_content],
            metadatas=[metadata],
            ids=[str(cv.id)]
        )

        # Preparar respuesta con información detallada
        response_data = {
            "status": "success",
            "cv_id": cv.id,
            "filename": cv.filename,
            "overall_score": cv.overall_score,
            "analysis": {
                "nombre": cv.nombre_completo,
                "email": cv.email,
                "telefono": cv.telefono,
                "industria": cv.industria.nombre if cv.industria else None,
                "rol": cv.rol.nombre if cv.rol else None,
                "puesto": cv.puesto.nombre if cv.puesto else None,
                "anhos_experiencia": cv.anhos_experiencia,
                "seniority": classifier.classify_seniority(text_content, cv.anhos_experiencia),
                "habilidades": [h.nombre for h in cv.habilidades][:10],  # Mostrar solo primeras 10
                "idiomas": [l.nombre for l in cv.lenguajes],
                "redes_sociales": {
                    "linkedin": cv.linkedin_url,
                    "github": cv.github_url,
                    "portafolio": cv.portafolio_url
                }
            }
        }
        
        return response_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando CV: {str(e)}")
    finally:
        # Limpiar archivo temporal
        if os.path.exists(temp_file):
            os.remove(temp_file)

            
@app.get("/cv/{cv_id}/analisis")
def get_cv_analysis(
    cv_id: int,
    classifier: UniversalCVClassifier = Depends(get_classifier)
):
    """
    Obtiene análisis detallado de un CV específico
    """
    analisis = classifier.get_cv_analysis(cv_id)
    if not analisis:
        raise HTTPException(status_code=404, detail="CV no encontrado")
    
    return analisis


# endpoint para listar los CVs
@app.get("/cvs")
def list_cvs(
    skip: int = 0,
    limit: int = 20,
    min_score: Optional[float] = None,
    industry: Optional[str] = None,
    role: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Lista CVs con filtros opcionales
    """
    query = db.query(CV)
    
    if min_score is not None:
        query = query.filter(CV.overall_score >= min_score)
    
    if industry:
        query = query.join(CV.industria).filter(CV.industria.has(nombre=industry))
    
    if role:
        query = query.join(CV.rol).filter(CV.rol.has(nombre=role))
    
    cvs = query.offset(skip).limit(limit).all()
    
    return {
        "cvs": [
            {
                "id": cv.id,
                "filename": cv.filename,
                "nombre": cv.nombre_completo,
                "score": cv.overall_score,
                "industria": cv.industria.nombre if cv.industria else None,
                "rol": cv.rol.nombre if cv.rol else None,
                "experiencia": cv.anhos_experiencia,
                "email": cv.email,
                "created_at": cv.created_at if hasattr(cv, 'created_at') else None
            }
            for cv in cvs
        ],
        "total": query.count()
    }

# ========== ENDPOINT PARA BUSCAR CANDIDATOS ==========
@app.get("/search")
def search_cvs(
    query: str,
    n_results: int = 10,
    min_score: Optional[float] = None,
    industry_filter: Optional[str] = None,
    role_filter: Optional[str] = None
):
    """
    Busca CVs usando ChromaDB con filtros adicionales
    """
    try:
        # Construir filtros para ChromaDB
        where_conditions = {}
        if min_score is not None:
            where_conditions["score"] = {"$gte": min_score}
        if industry_filter:
            where_conditions["industry"] = industry_filter
        if role_filter:
            where_conditions["role"] = role_filter
        
        # Realizar búsqueda en ChromaDB
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where_conditions if where_conditions else None
        )
        
        # Formatear resultados
        matches = []
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        
        for doc, meta, distance in zip(documents, metadatas, distances):
            matches.append({
                "cv_id": meta.get("cv_id"),
                "score": meta.get("score"),
                "role": meta.get("role"),
                "experience": meta.get("experience"),
                "industry": meta.get("industry"),
                "seniority": meta.get("seniority"),
                "skills_count": meta.get("skills_count"),
                "languages_count": meta.get("languages_count"),
                "similarity": round(1 - distance, 3) if distance else None,
                "preview": doc[:200] + "..." if len(doc) > 200 else doc
            })
        
        return {
            "query": query,
            "total_matches": len(matches),
            "matches": matches
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en búsqueda: {str(e)}")


from ollama import Client as OllamaClient

ollama_client = OllamaClient(host='http://localhost:11434') 

# ========== Funciones para conectar con la LLM ==========
def query_with_llm(question: str, context_filter: Optional[Dict] = None):
    """
    Realiza consulta usando LLM con contexto de CVs
    """
    try:
        # Buscar CVs relevantes en ChromaDB
        search_params = {
            "query_texts": [question],
            "n_results": 5
        }
        
        if context_filter:
            search_params["where"] = context_filter
            
        results = collection.query(**search_params)
        
        docs = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        if not docs:
            return "No se encontraron CVs relevantes para tu consulta."

        # Construir contexto para la LLM
        context_parts = []
        for i, (doc, meta) in enumerate(zip(docs, metadatas), 1):
            context_parts.append(f"""
CV #{i}:
- ID: {meta.get('cv_id', 'N/A')}
- Rol: {meta.get('role', 'N/A')}
- Experiencia: {meta.get('experience', 'N/A')}
- Seniority: {meta.get('seniority', 'N/A')}
- Industria: {meta.get('industry', 'N/A')}
- Score: {meta.get('score', 'N/A')}/100
- Contenido (extracto): {doc[:500]}...
""")

        context = "\n".join(context_parts)

        prompt = f"""
Eres un reclutador senior experto en selección de personal con más de 10 años de experiencia. 
Tu especialidad es identificar el talento ideal basándote en CVs y matching con requisitos específicos.

CONTEXTO - CVs disponibles:
{context}

CONSULTA DEL RECLUTADOR:
{question}

INSTRUCCIONES:
- Analiza cada CV de forma crítica y profesional
- Proporciona recomendaciones específicas basadas en los datos
- Si recomiendas candidatos, explica exactamente por qué
- Menciona fortalezas y posibles áreas de preocupación
- Sé conciso pero detallado en tu análisis
- Si ningún CV es adecuado, explica qué se necesitaría buscar

RESPUESTA:
        """

        # Enviar a LLM
        response = ollama_client.chat(
            model='llama2',  # Puedes cambiar el modelo según disponibilidad
            messages=[{"role": "user", "content": prompt}]
        )

        return response['message']['content']
        
    except Exception as e:
        return f"Error al procesar consulta con LLM: {str(e)}"

@app.get("/ask")
def ask_llm(query: str):
    try:
        answer = query_with_llm(query)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    