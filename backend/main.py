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

# Funciones embedding
def generate_embedding(text: str, model: str = "nomic-embed-text"):
    """
    Genera embeddings usando Ollama
    """
    try:
        response = ollama_client.embeddings(model=model, prompt=text)
        return response["embedding"]
    except Exception as e:
        print(f"Error generando embedding: {e}")
        # Fallback: usar el texto como embedding simple (solo para desarrollo)
        return None
    
def create_cv_embedding_text(cv_data: Dict) -> str:
    """
    Crea un texto optimizado para embeddings combinando datos clave del CV.
    """
    embedding_parts = []

    # Información personal
    nombre = cv_data.get("nombre", "").strip()
    if nombre:
        embedding_parts.append(f"Nombre: {nombre}")

    # Información profesional
    rol = cv_data.get("rol", "").strip()
    if rol:
        embedding_parts.append(f"Rol: {rol.lower()}")

    industria = cv_data.get("industria", "").strip()
    if industria:
        embedding_parts.append(f"Industria: {industria.lower()}")

    experiencia = cv_data.get("experiencia")
    if experiencia is not None:
        try:
            años = float(experiencia)
            embedding_parts.append(f"Experiencia: {años} años")
        except ValueError:
            embedding_parts.append(f"Experiencia: {experiencia}")

    seniority = cv_data.get("seniority", "").strip()
    if seniority:
        embedding_parts.append(f"Nivel: {seniority.lower()}")

    # Habilidades
    habilidades = cv_data.get("habilidades", [])
    if isinstance(habilidades, list) and habilidades:
        skills_text = ", ".join(h.lower().strip() for h in habilidades[:15])
        embedding_parts.append(f"Habilidades: {skills_text}")

    # Idiomas
    idiomas = cv_data.get("idiomas", [])
    if isinstance(idiomas, list) and idiomas:
        languages_text = ", ".join(i.lower().strip() for i in idiomas)
        embedding_parts.append(f"Idiomas: {languages_text}")

    # Contenido original (extracto)
    contenido = cv_data.get("contenido_original", "")
    if contenido:
        content_words = contenido.strip().split()
        excerpt = " ".join(content_words[:500])
        embedding_parts.append(f"Contenido: {excerpt}")

    return " | ".join(embedding_parts)

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

        cv_embedding_data = {
            "nombre": cv.nombre_completo,
            "rol": cv.rol.nombre if cv.rol else None,
            "industria": cv.industria.nombre if cv.industria else None,
            "experiencia": cv.anhos_experiencia,
            "seniority": classifier.classify_seniority(text_content, cv.anhos_experiencia),
            "habilidades": [h.nombre for h in cv.habilidades],
            "idiomas": [l.nombre for l in cv.lenguajes],
            "contenido_original": text_content
        }
        
        embedding_text = create_cv_embedding_text(cv_embedding_data)
        
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

        embedding = generate_embedding(embedding_text)

        if embedding:
            collection.add(
                documents=[embedding_text], 
                embeddings=[embedding],      
                metadatas=[metadata],
                ids=[str(cv.id)]
            )
        else:
            # Fallback sin embedding
            print(f"Warning: No se pudo generar embedding para CV {cv.id}, usando solo texto")
            collection.add(
                documents=[embedding_text],
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
                "habilidades": [h.nombre for h in cv.habilidades][:20],  
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
    role_filter: Optional[str] = None,
    use_embeddings: bool = True
):
    """
    Busca CVs usando ChromaDB con embeddings semánticos y filtros adicionales
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
        
        if use_embeddings:
            # Generar embedding para la consulta
            query_embedding = generate_embedding(query)
            
            if query_embedding:
                # Búsqueda usando embeddings
                results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=n_results,
                    where=where_conditions if where_conditions else None
                )
            else:
                # Fallback a búsqueda por texto
                results = collection.query(
                    query_texts=[query],
                    n_results=n_results,
                    where=where_conditions if where_conditions else None
                )
        else:
            # Búsqueda tradicional por texto
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
            # Calcular score de similitud
            similarity_score = round(1 - distance, 3) if distance is not None else None
            
            matches.append({
                "cv_id": meta.get("cv_id"),
                "nombre": meta.get("nombre"),
                "filename": meta.get("filename"),
                "score": meta.get("score"),
                "role": meta.get("role"),
                "experience": meta.get("experience"),
                "industry": meta.get("industry"),
                "seniority": meta.get("seniority"),
                "skills_count": meta.get("skills_count"),
                "languages_count": meta.get("languages_count"),
                "similarity": similarity_score,
                "match_strength": "Excelente" if similarity_score and similarity_score > 0.8 
                                else "Bueno" if similarity_score and similarity_score > 0.6 
                                else "Regular" if similarity_score and similarity_score > 0.4 
                                else "Bajo",
                "preview": doc[:200] + "..." if len(doc) > 200 else doc
            })
        
        # Ordenar por similitud si está disponible
        if matches and matches[0]["similarity"] is not None:
            matches.sort(key=lambda x: x["similarity"], reverse=True)
        
        return {
            "query": query,
            "search_method": "embeddings" if use_embeddings and query_embedding else "text",
            "filters_applied": {
                "min_score": min_score,
                "industry": industry_filter,
                "role": role_filter
            },
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
    Realiza consulta usando LLM con contexto de CVs y embeddings
    """
    try:
        # Generar embedding para la pregunta
        question_embedding = generate_embedding(question)
        
        # Configurar parámetros de búsqueda
        search_params = {"n_results": 5}
        
        if context_filter:
            search_params["where"] = context_filter
        
        # Usar embedding si está disponible, sino usar texto
        if question_embedding:
            search_params["query_embeddings"] = [question_embedding]
        else:
            search_params["query_texts"] = [question]
            
        results = collection.query(**search_params)
        
        docs = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        if not docs:
            return "No se encontraron CVs relevantes para tu consulta."

        # Construir contexto enriquecido para la LLM
        context_parts = []
        for i, (doc, meta, distance) in enumerate(zip(docs, metadatas, distances), 1):
            similarity = round(1 - distance, 3) if distance is not None else "N/A"
            
            context_parts.append(f"""
CV #{i} (Relevancia: {similarity}):
- ID: {meta.get('cv_id', 'N/A')}
- Nombre: {meta.get('nombre', 'N/A')}
- Archivo: {meta.get('filename', 'N/A')}
- Rol: {meta.get('role', 'N/A')}
- Experiencia: {meta.get('experience', 'N/A')}
- Seniority: {meta.get('seniority', 'N/A')}
- Industria: {meta.get('industry', 'N/A')}
- Score Global: {meta.get('score', 'N/A')}/100
- Habilidades: {meta.get('skills_count', 'N/A')} detectadas
- Idiomas: {meta.get('languages_count', 'N/A')} detectados
- Contenido relevante: {doc[:400]}...
""")

        context = "\n".join(context_parts)

        prompt = f"""
Eres un reclutador senior experto con más de 15 años de experiencia en selección de personal tecnológico y empresarial. 
Tienes acceso a un sistema avanzado de análisis de CVs con embeddings semánticos que te proporciona los candidatos más relevantes.

CONTEXTO - CVs más relevantes (ordenados por relevancia semántica):
{context}

CONSULTA DEL RECLUTADOR:
{question}

INSTRUCCIONES ESPECÍFICAS:
- Analiza la relevancia semántica de cada CV (valores más altos = mejor match)
- Prioriza candidatos con mayor score global y relevancia
- Para cada recomendación, menciona el ID del CV para referencia
- Identifica patrones y tendencias en los candidatos encontrados
- Si recomiendas un candidato, explica específicamente por qué es ideal
- Menciona tanto fortalezas como posibles limitaciones
- Si ningún CV es perfecto, sugiere el mejor match disponible y qué buscar adicionalmente
- Sé conciso pero detallado, máximo 500 palabras

FORMATO DE RESPUESTA:
1. Resumen ejecutivo (2-3 líneas)
2. Candidatos recomendados (con IDs)
3. Análisis de gaps si los hay
4. Recomendaciones adicionales

RESPUESTA:
        """

        # Enviar a LLM con modelo optimizado para análisis
        response = ollama_client.chat(
            model='llama2',  # Puedes usar 'mixtral' o 'codellama' si están disponibles
            messages=[{"role": "user", "content": prompt}],
            options={
                "temperature": 0.3,  # Más determinístico para análisis profesional
                "top_p": 0.9,
                "top_k": 40
            }
        )

        return response['message']['content']
        
    except Exception as e:
        return f"Error al procesar consulta con LLM: {str(e)}"

@app.get("/ask")
@app.get("/ask")
def ask_llm(
    query: str,
    industry_filter: Optional[str] = None,
    min_score: Optional[float] = None,
    role_filter: Optional[str] = None
):
    """
    Realiza consulta inteligente sobre CVs usando LLM
    """
    try:
        # Construir filtros opcionales
        context_filter = {}
        if industry_filter:
            context_filter["industry"] = industry_filter
        if min_score is not None:
            context_filter["score"] = {"$gte": min_score}
        if role_filter:
            context_filter["role"] = role_filter
        
        answer = query_with_llm(query, context_filter if context_filter else None)
        
        return {
            "query": query,
            "filters_applied": {
                "industry": industry_filter,
                "min_score": min_score,
                "role": role_filter
            },
            "answer": answer
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando consulta: {str(e)}")
    

@app.post("/regenerate-embeddings")
def regenerate_all_embeddings(db: Session = Depends(get_db)):
    """
    Regenera embeddings para todos los CVs existentes
    """
    try:
        cvs = db.query(CV).all()
        updated_count = 0
        errors = []
        
        for cv in cvs:
            try:
                # Preparar datos para embedding
                cv_embedding_data = {
                    "nombre": cv.nombre_completo,
                    "rol": cv.rol.nombre if cv.rol else None,
                    "industria": cv.industria.nombre if cv.industria else None,
                    "experiencia": cv.anhos_experiencia,
                    "seniority": "N/A",  # No podemos recalcular sin el texto original
                    "habilidades": [h.nombre for h in cv.habilidades],
                    "idiomas": [l.nombre for l in cv.lenguajes],
                    "contenido_original": cv.contenido if hasattr(cv, 'contenido') else ""
                }
                
                embedding_text = create_cv_embedding_text(cv_embedding_data)
                embedding = generate_embedding(embedding_text)
                
                if embedding:
                    # Actualizar en ChromaDB
                    metadata = {
                        "cv_id": cv.id,
                        "role": cv.rol.nombre if cv.rol else "No especificado",
                        "experience": f"{cv.anhos_experiencia} años",
                        "industry": cv.industria.nombre if cv.industria else "No especificado",
                        "score": cv.overall_score,
                        "skills_count": len(cv.habilidades),
                        "languages_count": len(cv.lenguajes),
                        "filename": cv.filename,
                        "nombre": cv.nombre_completo or "No especificado"
                    }
                    
                    # Eliminar el embedding anterior si existe
                    try:
                        collection.delete(ids=[str(cv.id)])
                    except:
                        pass  # No existe, continuar
                    
                    # Agregar nuevo embedding
                    collection.add(
                        documents=[embedding_text],
                        embeddings=[embedding],
                        metadatas=[metadata],
                        ids=[str(cv.id)]
                    )
                    
                    updated_count += 1
                    
            except Exception as e:
                errors.append(f"CV {cv.id}: {str(e)}")
        
        return {
            "status": "completed",
            "total_cvs": len(cvs),
            "updated_count": updated_count,
            "errors": errors
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error regenerando embeddings: {str(e)}")
    
#========== Endpoints de estadisticas ==========
@app.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """Obtiene estadísticas generales del sistema"""
    total_cvs = db.query(CV).count()
    avg_score = db.query(CV).filter(CV.overall_score.isnot(None)).all()
    avg_score_value = sum(cv.overall_score for cv in avg_score) / len(avg_score) if avg_score else 0
    
    return {
        "total_cvs": total_cvs,
        "average_score": round(avg_score_value, 2),
        "collection_count": collection.count() if hasattr(collection, 'count') else "N/A"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
    