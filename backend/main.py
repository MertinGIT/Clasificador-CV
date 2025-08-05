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
import unidecode

# Importar el nuevo procesador con Ollama
from ollama_cv_processor import OllamaCVProcessor, create_cv_embedding_text_enhanced


load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# ========== CONFIGURACIÓN BÁSICA ==========
app = FastAPI(title="CV Analysis API with Ollama", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Base de datos con SQLAlchemy
Base.metadata.create_all(bind=engine)

# Cliente Ollama
ollama_client = OllamaClient(host='http://localhost:11434')

# Inyectamos las dependencias
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_classifier(db: Session = Depends(get_db)):
    return UniversalCVClassifier(db)

def get_ollama_processor(db: Session = Depends(get_db)):
    """Retorna el procesador de CVs con Ollama"""
    return OllamaCVProcessor(ollama_client, model="llama3", db_session=db)

# Funciones embedding (actualizadas)
def generate_embedding(text: str, model: str = "nomic-embed-text"):
    """
    Genera embeddings usando Ollama
    """
    try:
        response = ollama_client.embeddings(model=model, prompt=text)
        return response["embedding"]
    except Exception as e:
        print(f"Error generando embedding: {e}")
        return None

# ========== CHROMA DB ==========
settings = Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory="./chroma_storage"
)
chroma_client = chromadb.PersistentClient(path="./chroma_storage")
collection_name = "cv_embeddings"

# Eliminar colección existente si hay conflicto de dimensiones
existing_collections = chroma_client.list_collections()
if any(c.name == collection_name for c in existing_collections):
    chroma_client.delete_collection(name=collection_name)

# Crear o recrear colección
collection = chroma_client.get_or_create_collection(name=collection_name)

# ========== UTILIDAD PARA EXTRAER TEXTO DE PDF ==========
def extract_text_from_pdf(file) -> str:
    try:
        with pdfplumber.open(file) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
            print(f"[INFO] Texto extraído del PDF: {(text)}")
        return text.strip()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al procesar PDF: {str(e)}") 

# ========== ENDPOINT PRINCIPAL de subida ==========
@app.post("/upload")
async def upload_cv_with_ollama(
        file: UploadFile = File(...),
        ollama_processor: OllamaCVProcessor = Depends(get_ollama_processor)
    ):
        """
        Sube y procesa un CV PDF usando Ollama
        """
        if not file.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF")

        temp_file = f"temp_{uuid.uuid4()}.pdf"
        try:
            print(f"[INFO] Procesando archivo: {file.filename}")
            
            # Guardar archivo temporalmente
            with open(temp_file, "wb") as f:
                content = await file.read()
                f.write(content)

            # Extraer texto del PDF
            text_content = extract_text_from_pdf(temp_file)
            
            if not text_content.strip():
                raise HTTPException(status_code=400, detail="No se pudo extraer texto del PDF")

            print(f"[INFO] Iniciando análisis con Ollama...")
            
            # ===== Procesar con Ollama =====
            analysis = ollama_processor.process_cv_with_ollama(text_content)
            
            print(f"[SUCCESS] Análisis de Ollama completado:")
            print(f"  - Candidato: {analysis.nombre}")
            print(f"  - Rol sugerido: {analysis.rol_sugerido}")
            print(f"  - Seniority: {analysis.seniority}")
            print(f"  - Sector: {analysis.sector}")
            print(f"  - Score: {analysis.overall_score}")
            
            # ===== Guardar en base de datos =====
            try:
                cv = ollama_processor.save_cv_from_analysis_corrected(analysis, file.filename)
                processing_method = "ollama_enhanced"
                
            except Exception as e:
                print(f"[ERROR] Error guardando CV: {e}")
                raise HTTPException(status_code=500, detail=f"Error guardando CV: {str(e)}")
            
            # ===== CREAR EMBEDDING MEJORADO =====
            embedding_text = create_cv_embedding_text_enhanced(analysis)
            
            # Crear metadata enriquecida para ChromaDB
            metadata = {
                "cv_id": cv.id,
                "nombre": analysis.nombre,
                "filename": file.filename,
                "role": analysis.rol_sugerido,
                "seniority": analysis.seniority,
                "experience": f"{analysis.anos_experiencia} años",
                "industry": analysis.sector,
                "score": analysis.overall_score,
                "skills_count": len(analysis.habilidades_tecnicas),
                "languages_count": len(analysis.idiomas),
                "soft_skills_count": len(analysis.soft_skills),
                "calidad_cv": analysis.calidad_cv,
                "processing_method": processing_method
            }
            
            print(f"[INFO] Generando embedding...")
            embedding = generate_embedding(embedding_text)
            
            if embedding:
                collection.add(
                    documents=[embedding_text], 
                    embeddings=[embedding],      
                    metadatas=[metadata],
                    ids=[str(cv.id)]
                )
                print(f"[SUCCESS] Embedding guardado en ChromaDB")
            
            # ===== RESPUESTA ENRIQUECIDA =====
            response_data = {
                "status": "success",
                "cv_id": cv.id,
                "filename": file.filename,
                "processing_method": processing_method,
                
                # Análisis de Ollama
                "ollama_analysis": {
                    "nombre": analysis.nombre,
                    "email": analysis.email,
                    "telefono": analysis.telefono,
                    "linkedin": analysis.linkedin,
                    
                    "perfil_profesional": {
                        "rol_sugerido": analysis.rol_sugerido,
                        "seniority": analysis.seniority,
                        "sector": analysis.sector,
                        "anos_experiencia": analysis.anos_experiencia,
                        "resumen_profesional": analysis.resumen_profesional
                    },
                    
                    "competencias": {
                        "habilidades_tecnicas": analysis.habilidades_tecnicas,
                        "soft_skills": analysis.soft_skills,
                        "idiomas": analysis.idiomas
                    },
                    
                    "evaluacion": {
                        "overall_score": analysis.overall_score,
                        "calidad_cv": analysis.calidad_cv,
                        "fortalezas": analysis.fortalezas,
                        "areas_mejora": analysis.areas_mejora
                    }
                },
                
                # Clasificación final en BD
                "clasificacion_bd": {
                    "rol": {
                        "nombre": cv.rol.nombre if cv.rol else None,
                        "descripcion": cv.rol.descripcion if cv.rol else None
                    },
                    "seniority": {
                        "nombre": cv.puesto.nombre if cv.puesto else None,
                        "rango_años": f"{cv.puesto.min_anhos}-{cv.puesto.max_anhos or '+'}" if cv.puesto else None
                    },
                    "industria_principal": {
                        "nombre": cv.industria.nombre if cv.industria else None,
                        "descripcion": cv.industria.descripcion if cv.industria else None
                    },
                    "score_final": cv.overall_score,
                    "años_experiencia": cv.anhos_experiencia
                }
            }
            
            return response_data
            
        except Exception as e:
            print(f"[ERROR] Error procesando CV: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error procesando CV: {str(e)}")
        finally:
            # Limpiar archivo temporal
            if os.path.exists(temp_file):
                os.remove(temp_file)

# ========== ENDPOINT DE ANÁLISIS DETALLADO ==========
@app.get("/cv/{cv_id}/analisis-completo")
def get_complete_cv_analysis(
    cv_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene análisis completo del CV incluyendo datos de Ollama si están disponibles
    """
    cv = db.query(CV).filter(CV.id == cv_id).first()
    if not cv:
        raise HTTPException(status_code=404, detail="CV no encontrado")
    
    # Buscar en ChromaDB para obtener metadata enriquecida
    try:
        results = collection.get(ids=[str(cv_id)], include=["metadatas", "documents"])
        if results["ids"]:
            metadata = results["metadatas"][0]
            document = results["documents"][0]
            
            return {
                "cv_info": {
                    "id": cv.id,
                    "filename": cv.filename,
                    "created_at": cv.created_at if hasattr(cv, 'created_at') else None
                },
                "enhanced_metadata": metadata,
                "embedding_text": document,
                "classic_data": {
                    "nombre": cv.nombre_completo,
                    "email": cv.email,
                    "telefono": cv.telefono,
                    "industria": cv.industria.nombre if cv.industria else None,
                    "rol": cv.rol.nombre if cv.rol else None,
                    "score": cv.overall_score,
                    "habilidades": [h.nombre for h in cv.habilidades],
                    "idiomas": [l.nombre for l in cv.lenguajes]
                }
            }
    except Exception as e:
        print(f"[WARNING] Error obteniendo datos de ChromaDB: {e}")
    
    # Fallback a datos clásicos
    return {
        "cv_info": {
            "id": cv.id,
            "filename": cv.filename
        },
        "classic_data": {
            "nombre": cv.nombre_completo,
            "email": cv.email,
            "score": cv.overall_score,
            "habilidades": [h.nombre for h in cv.habilidades]
        }
    }

# ========== BÚSQUEDA MEJORADA ==========
@app.get("/search")
def search_cvs_enhanced(
    query: str,
    n_results: int = 10,
    min_score: Optional[float] = None,
    industry_filter: Optional[str] = None,
    role_filter: Optional[str] = None,
    seniority_filter: Optional[str] = None,
    use_embeddings: bool = True
):
    """
    Búsqueda avanzada con filtros de Ollama
    """
    try:
        # Construir filtros mejorados
        where_conditions = {}
        if min_score is not None:
            where_conditions["score"] = {"$gte": min_score}
        if industry_filter:
            where_conditions["industry"] = industry_filter
        if role_filter:
            where_conditions["role"] = {"$contains": role_filter}
        if seniority_filter:
            where_conditions["seniority"] = seniority_filter
        
        if use_embeddings:
            # Generar embedding para la consulta
            print("Usa embeddings")
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
        
        # Formatear resultados mejorados
        matches = []
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        
        for doc, meta, distance in zip(documents, metadatas, distances):
            # Calcular score de similitud
            similarity_score = round(1 - distance, 3) if distance is not None else None
            
            matches.append({
                "cv_id": meta.get("cv_id"),
                "nombre": meta.get("nombre", "N/A"),
                "filename": meta.get("filename", "N/A"),
                "score": meta.get("score", 0),
                "role": meta.get("role", "N/A"),
                "seniority": meta.get("seniority", "N/A"),
                "experience": meta.get("experience", "N/A"),
                "industry": meta.get("industry", "N/A"),
                "skills_count": meta.get("skills_count", 0),
                "soft_skills_count": meta.get("soft_skills_count", 0),
                "languages_count": meta.get("languages_count", 0),
                "calidad_cv": meta.get("calidad_cv", "N/A"),
                "similarity": similarity_score,
                "match_strength": "Excelente" if similarity_score and similarity_score > 0.8 
                                else "Bueno" if similarity_score and similarity_score > 0.6 
                                else "Regular" if similarity_score and similarity_score > 0.4 
                                else "Bajo",
                "preview": doc[:300] + "..." if len(doc) > 300 else doc
            })
        
        # Ordenar por similitud si está disponible
        if matches and matches[0]["similarity"] is not None:
            matches.sort(key=lambda x: x["similarity"], reverse=True)
        
        return {
            "query": query,
            "search_method": "ollama_enhanced_embeddings" if use_embeddings and query_embedding else "text",
            "filters_applied": {
                "min_score": min_score,
                "industry": industry_filter,
                "role": role_filter,
                "seniority": seniority_filter
            },
            "total_matches": len(matches),
            "matches": matches
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en búsqueda: {str(e)}")

# ========== CONSULTA CON LLM MEJORADA ==========
@app.get("/ask")
def ask_llm_enhanced(
    query: str,
    industry_filter: Optional[str] = None,
    min_score: Optional[float] = None,
    role_filter: Optional[str] = None,
    seniority_filter: Optional[str] = None
):
    """
    Consulta inteligente mejorada con datos de Ollama
    """
    try:
        # Construir filtros opcionales
        context_filter = {}
        if industry_filter:
            context_filter["industry"] = industry_filter
        if min_score is not None:
            context_filter["score"] = {"$gte": min_score}
        if role_filter:
            context_filter["role"] = {"$contains": role_filter}
        if seniority_filter:
            context_filter["seniority"] = seniority_filter
        
        answer = query_with_llm_enhanced(query, context_filter if context_filter else None)
        
        return {
            "query": query,
            "filters_applied": {
                "industry": industry_filter,
                "min_score": min_score,
                "role": role_filter,
                "seniority": seniority_filter
            },
            "answer": answer,
            "processing_method": "ollama_enhanced"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando consulta: {str(e)}")

def query_with_llm_enhanced(question: str, context_filter: Optional[Dict] = None):
    """
    Consulta mejorada usando LLM con contexto enriquecido de Ollama
    """
    try:
        # Generar embedding para la pregunta
        question_embedding = generate_embedding(question)
        
        # Configurar parámetros de búsqueda
        search_params = {"n_results": 5, "include": ["metadatas", "documents", "distances"]}
        
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

        # Construir contexto super enriquecido para la LLM
        context_parts = []
        for i, (doc, meta, distance) in enumerate(zip(docs, metadatas, distances), 1):
            similarity = round(1 - distance, 3) if distance is not None else "N/A"
            
            context_parts.append(f"""
CANDIDATO #{i} (Relevancia semántica: {similarity}):
═══════════════════════════════════════════════════════════════════════
• ID: {meta.get('cv_id', 'N/A')}
• Nombre: {meta.get('nombre', 'N/A')}
• Archivo: {meta.get('filename', 'N/A')}

PERFIL PROFESIONAL:
• Rol: {meta.get('role', 'N/A')}
• Seniority: {meta.get('seniority', 'N/A')}
• Experiencia: {meta.get('experience', 'N/A')}
• Industria: {meta.get('industry', 'N/A')}

MÉTRICAS DE CALIDAD:
• Score Global: {meta.get('score', 'N/A')}/100
• Calidad CV: {meta.get('calidad_cv', 'N/A')}
• Habilidades técnicas: {meta.get('skills_count', 'N/A')} detectadas
• Soft skills: {meta.get('soft_skills_count', 'N/A')} detectadas
• Idiomas: {meta.get('languages_count', 'N/A')} detectados

CONTENIDO RELEVANTE:
{doc[:500]}{'...' if len(doc) > 500 else ''}
═══════════════════════════════════════════════════════════════════════
""")

        context = "\n".join(context_parts)

        prompt = f"""
Eres un reclutador senior experto con más de 15 años de experiencia en selección de personal tecnológico y empresarial. 
Tienes acceso a un sistema avanzado de análisis de CVs con embeddings semánticos que te proporciona los candidatos más relevantes.

CONTEXTO - CANDIDATOS MÁS RELEVANTES (ordenados por relevancia semántica):
{context}

CONSULTA DEL RECLUTADOR:
{question}

INSTRUCCIONES ESPECÍFICAS PARA TU ANÁLISIS:

🎯 ANÁLISIS DE RELEVANCIA:
- Los valores de relevancia semántica (0-1) indican qué tan bien coincide cada CV con la consulta
- Valores >0.8 = Match excelente | 0.6-0.8 = Buen match | 0.4-0.6 = Match regular | <0.4 = Match bajo
- Prioriza candidatos con alta relevancia semántica Y score global alto

🧠 EVALUACIÓN INTEGRAL:
- Analiza no solo habilidades técnicas, sino también soft skills y calidad del CV
- Considera seniority vs experiencia (pueden no coincidir siempre)
- Evalúa la coherencia entre rol, industria y habilidades

💡 INSIGHTS AVANZADOS:
- Identifica patrones interesantes entre los candidatos
- Detecta fortalezas únicas o combinaciones raras de skills
- Sugiere candidatos "diamantes en bruto" (alta relevancia, score menor)

⚠️ GAPS Y LIMITACIONES:
- Si ningún candidato es perfecto, explica específicamente qué falta
- Sugiere búsquedas alternativas o filtros adicionales
- Recomienda si ampliar criterios o ser más específicos

FORMATO DE RESPUESTA ESTRUCTURADA:

🔥 RESUMEN EJECUTIVO (2-3 líneas clave)

⭐ TOP CANDIDATOS RECOMENDADOS:
[Para cada candidato menciona ID, nombre, por qué es ideal, fortalezas clave]

📊 ANÁLISIS COMPARATIVO:
[Patrones, tendencias, diferenciadores entre candidatos]

⚠️ GAPS IDENTIFICADOS:
[Qué no encuentras en los resultados actuales]

🎯 RECOMENDACIONES ESTRATÉGICAS:
[Próximos pasos, filtros adicionales, búsquedas complementarias]

INSTRUCCIONES ESPECÍFICAS:
- Analiza la relevancia semántica de cada CV (valores más altos = mejor match)
- Prioriza candidatos con mayor score global y relevancia
- Para cada recomendación, menciona el ID del CV para referencia
- Identifica patrones y tendencias en los candidatos encontrados
- Si recomiendas un candidato, explica específicamente por qué es ideal
- Menciona tanto fortalezas como posibles limitaciones
- Si ningún CV es perfecto, sugiere el mejor match disponible y qué buscar adicionalmente
- Sé conciso pero detallado, máximo 500 palabras

RESPUESTA (máximo 600 palabras, directo y actionable):
        """

        # Enviar a Ollama con configuración optimizada
        response = ollama_client.chat(
            model='llama3',  # Puedes usar 'mixtral', 'codellama', etc.
            messages=[{"role": "user", "content": prompt}],
            options={
                "temperature": 0.2,  # Más determinístico para análisis profesional
                "top_p": 0.9,
                "top_k": 40,
                "num_ctx": 4096  # Contexto amplio para análisis complejo
            }
        )

        return response['message']['content']
        
    except Exception as e:
        return f"Error al procesar consulta con LLM: {str(e)}"

# ========== ENDPOINTS ADICIONALES ==========

@app.get("/cvs")
def list_cvs_enhanced(
    skip: int = 0,
    limit: int = 20,
    min_score: Optional[float] = None,
    industry: Optional[str] = None,
    role: Optional[str] = None,
    seniority: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Lista CVs con filtros opcionales mejorados
    """
    query = db.query(CV)
    
    if min_score is not None:
        query = query.filter(CV.overall_score >= min_score)
    
    if industry:
        query = query.join(CV.industria).filter(CV.industria.has(nombre=industry))
    
    if role:
        query = query.join(CV.rol).filter(CV.rol.has(nombre=role))
    
    cvs = query.offset(skip).limit(limit).all()
    
    # Enriquecer con datos de ChromaDB si están disponibles
    enriched_cvs = []
    for cv in cvs:
        cv_data = {
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
        
        # Intentar obtener datos enriquecidos de ChromaDB
        try:
            results = collection.get(ids=[str(cv.id)], include=["metadatas"])
            if results["ids"]:
                metadata = results["metadatas"][0]
                cv_data.update({
                    "seniority": metadata.get("seniority"),
                    "calidad_cv": metadata.get("calidad_cv"),
                    "skills_count": metadata.get("skills_count"),
                    "soft_skills_count": metadata.get("soft_skills_count"),
                    "languages_count": metadata.get("languages_count")
                })
        except:
            pass  # Continuar con datos básicos
        
        enriched_cvs.append(cv_data)
    
    return {
        "cvs": enriched_cvs,
        "total": query.count(),
        "filters_applied": {
            "min_score": min_score,
            "industry": industry,
            "role": role,
            "seniority": seniority
        }
    }

@app.post("/regenerate-embeddings")
def regenerate_all_embeddings_enhanced(
    db: Session = Depends(get_db),
    ollama_processor: OllamaCVProcessor = Depends(get_ollama_processor)
):
    """
    Regenera embeddings mejorados para todos los CVs existentes usando Ollama
    """
    try:
        cvs = db.query(CV).all()
        updated_count = 0
        errors = []
        
        for cv in cvs:
            try:
                print(f"[INFO] Regenerando embedding para CV {cv.id}: {cv.filename}")
                
                # Si tenemos contenido original, reprocesar con Ollama
                contenido_original = getattr(cv, 'contenido', None)
                if contenido_original:
                    analysis = ollama_processor.process_cv_with_ollama(contenido_original)
                    embedding_text = create_cv_embedding_text_enhanced(analysis)
                    
                    metadata = {
                        "cv_id": cv.id,
                        "nombre": analysis.nombre,
                        "filename": cv.filename,
                        "role": analysis.rol_sugerido,
                        "seniority": analysis.seniority,
                        "experience": f"{analysis.anos_experiencia} años",
                        "industry": analysis.sector,
                        "score": analysis.overall_score,
                        "skills_count": len(analysis.habilidades_tecnicas),
                        "soft_skills_count": len(analysis.soft_skills),
                        "languages_count": len(analysis.idiomas),
                        "calidad_cv": analysis.calidad_cv,
                    }
                else:
                    # Fallback a datos existentes
                    embedding_text = f"""
Nombre: {cv.nombre_completo or 'N/A'}
Rol: {cv.rol.nombre if cv.rol else 'N/A'}
Industria: {cv.industria.nombre if cv.industria else 'N/A'}
Experiencia: {cv.anhos_experiencia} años
Habilidades: {', '.join([h.nombre for h in cv.habilidades])}
Idiomas: {', '.join([l.nombre for l in cv.lenguajes])}
                    """.strip()
                    
                    metadata = {
                        "cv_id": cv.id,
                        "nombre": cv.nombre_completo or "N/A",
                        "filename": cv.filename,
                        "role": cv.rol.nombre if cv.rol else "N/A",
                        "seniority": "N/A",
                        "experience": f"{cv.anhos_experiencia} años",
                        "industry": cv.industria.nombre if cv.industria else "N/A",
                        "score": cv.overall_score,
                        "skills_count": len(cv.habilidades),
                        "languages_count": len(cv.lenguajes),
                        "calidad_cv": "N/A",
                    }
                
                embedding = generate_embedding(embedding_text)
                
                if embedding:
                    # Eliminar el embedding anterior si existe
                    try:
                        collection.delete(ids=[str(cv.id)])
                    except:
                        pass
                    
                    # Agregar nuevo embedding
                    collection.add(
                        documents=[embedding_text],
                        embeddings=[embedding],
                        metadatas=[metadata],
                        ids=[str(cv.id)]
                    )
                    
                    updated_count += 1
                    print(f"[SUCCESS] CV {cv.id} actualizado exitosamente")
                    
            except Exception as e:
                error_msg = f"CV {cv.id}: {str(e)}"
                errors.append(error_msg)
                print(f"[ERROR] {error_msg}")
        
        return {
            "status": "completed",
            "total_cvs": len(cvs),
            "updated_count": updated_count,
            "errors": errors,
            "method": "ollama_enhanced"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error regenerando embeddings: {str(e)}")

@app.get("/stats")
def get_stats_enhanced(db: Session = Depends(get_db)):
    """Obtiene estadísticas generales del sistema mejoradas"""
    total_cvs = db.query(CV).count()
    avg_score = db.query(CV).filter(CV.overall_score.isnot(None)).all()
    avg_score_value = sum(cv.overall_score for cv in avg_score) / len(avg_score) if avg_score else 0
    
    # Estadísticas de ChromaDB
    try:
        collection_count = collection.count()
        
        # Obtener distribución de seniority desde ChromaDB
        all_results = collection.get(include=["metadatas"])
        seniority_stats = {}
        calidad_stats = {}
        
        for metadata in all_results.get("metadatas", []):
            seniority = metadata.get("seniority", "N/A")
            calidad = metadata.get("calidad_cv", "N/A")
            
            seniority_stats[seniority] = seniority_stats.get(seniority, 0) + 1
            calidad_stats[calidad] = calidad_stats.get(calidad, 0) + 1
            
    except Exception as e:
        print(f"[WARNING] Error obteniendo stats de ChromaDB: {e}")
        collection_count = "N/A"
        seniority_stats = {}
        calidad_stats = {}
    
    return {
        "total_cvs": total_cvs,
        "average_score": round(avg_score_value, 2),
        "collection_count": collection_count,
        "seniority_distribution": seniority_stats,
        "calidad_cv_distribution": calidad_stats,
        "processing_method": "ollama_enhanced"
    }

# ========== NUEVO ENDPOINT PARA TESTING OLLAMA ==========
@app.post("/test-ollama")
async def test_ollama_processing(
    text: str,
    ollama_processor: OllamaCVProcessor = Depends(get_ollama_processor)
):
    """
    Endpoint para testear el procesamiento de Ollama con texto directo
    """
    try:
        analysis = ollama_processor.process_cv_with_ollama(text)
        
        return {
            "status": "success",
            "analysis": {
                "nombre": analysis.nombre,
                "rol_sugerido": analysis.rol_sugerido,
                "seniority": analysis.seniority,
                "anos_experiencia": analysis.anos_experiencia,
                "overall_score": analysis.overall_score,
                "habilidades_tecnicas": analysis.habilidades_tecnicas,
                "soft_skills": analysis.soft_skills,
                "resumen_profesional": analysis.resumen_profesional,
                "embedding_text": analysis.embedding_text[:200] + "..." if len(analysis.embedding_text) > 200 else analysis.embedding_text
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error testing Ollama: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)