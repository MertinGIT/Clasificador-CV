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
import requests
from sentence_transformers import SentenceTransformer
# Importar el nuevo procesador con Ollama
from ollama_cv_processor import OllamaCVProcessor, create_cv_embedding_text_enhanced

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


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


import ollama
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Funciones embedding
def generate_embedding(text: str) -> list[float]:
    if not text or not text.strip():
        print("⚠️ Texto vacío para embedding")
        return None

    # Limpiar y truncar si es necesario
    text = text.strip()
    if len(text) > 8000:
        text = text[:8000]
        print("⚠️ Texto truncado a 8000 caracteres")

    # Generar el embedding
    embedding = model.encode(text).tolist()

    # Validar
    if embedding and len(embedding) > 0:
        print(f"✅ Embedding generado exitosamente: {len(embedding)} dimensiones")
        return embedding
    else:
        print("❌ Embedding vacío generado")
        return None
    
# ========== CHROMA DB ==========
settings = Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory="./chroma_storage"
)
chroma_client = chromadb.PersistentClient(path="./chroma_storage")
collection_name = "cv_embeddings"
embedding_dimension_esperada = 384  

existing_collections = chroma_client.list_collections()
existing = next((c for c in existing_collections if c.name == collection_name), None)

if existing:
    collection = chroma_client.get_collection(name=collection_name)
    
    sample = collection.peek(1)
    if sample and 'embeddings' in sample and len(sample['embeddings']) > 0:
        actual_dim = len(sample['embeddings'][0])
        if actual_dim != embedding_dimension_esperada:
            print(f"⚠️ Dimensión incompatible ({actual_dim} != {embedding_dimension_esperada}), eliminando colección")
            chroma_client.delete_collection(name=collection_name)
            collection = chroma_client.create_collection(name=collection_name)
        else:
            print("Colección existente con dimensión válida")
    else:
        print("ℹColección vacía o sin embeddings")
else:
    collection = chroma_client.create_collection(name=collection_name)
    print(" Colección creada")


# ========== UTILIDAD PARA EXTRAER TEXTO DE PDF ==========
def extract_text_from_pdf(file) -> str:
    for doc in collection.get(include=["documents"])["documents"]:
        print(doc)
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
def search_cvs_enhanced_fixed(
    query: str,
    n_results: int = 10,
    min_score: Optional[float] = None,
    industry_filter: Optional[str] = None,
    role_filter: Optional[str] = None,
    seniority_filter: Optional[str] = None,
    use_embeddings: bool = True
):
    """
    Búsqueda con filtros corregidos para ChromaDB
    """
    import traceback
    
    try:
        print(f"🔍 BÚSQUEDA INICIADA: {query}")
        print(f"🎯 Filtros recibidos: industry={industry_filter}, min_score={min_score}")
        
        # 1. VERIFICAR COLECCIÓN
        collection_count = collection.count()
        print(f"📊 Documentos en colección: {collection_count}")
        
        if collection_count == 0:
            return {
                "query": query,
                "total_matches": 0,
                "matches": [],
                "error": "No hay CVs en la base de datos"
            }

        # 2. CONSTRUIR FILTROS CORRECTAMENTE PARA CHROMADB
        where_conditions = None  # Inicializar como None
        
        # IMPORTANTE: ChromaDB requiere formato específico para filtros
        filters_list = []
        
        if min_score is not None:
            try:
                min_score_float = float(min_score)
                filters_list.append({"score": {"$gte": min_score_float}})
                print(f"✅ Filtro score agregado: >= {min_score_float}")
            except (ValueError, TypeError) as e:
                print(f"⚠️ Error en min_score: {e}")
        
        if industry_filter and industry_filter.strip():
            # Usar $eq en lugar de valor directo para mayor compatibilidad
            filters_list.append({"industry": {"$eq": industry_filter.strip()}})
            print(f"✅ Filtro industry agregado: {industry_filter}")
        
        if role_filter and role_filter.strip():
            # Para búsqueda de texto dentro del campo, usar $contains si está soportado
            filters_list.append({"role": {"$contains": role_filter.strip()}})
            print(f"✅ Filtro role agregado: contains '{role_filter}'")
        
        if seniority_filter and seniority_filter.strip():
            filters_list.append({"seniority": {"$eq": seniority_filter.strip()}})
            print(f"✅ Filtro seniority agregado: {seniority_filter}")
        
        # Combinar filtros usando $and si hay múltiples
        if len(filters_list) == 1:
            where_conditions = filters_list[0]
        elif len(filters_list) > 1:
            where_conditions = {"$and": filters_list}
        
        print(f"🔧 Filtros finales para ChromaDB: {where_conditions}")

        # 3. GENERAR EMBEDDING SI ESTÁ HABILITADO
        query_embedding = None
        if use_embeddings:
            print("🧠 Generando embedding...")
            query_embedding = generate_embedding(query)
            if query_embedding:
                print("✅ Embedding generado exitosamente")
            else:
                print("⚠️ Fallback a búsqueda por texto")

        # 4. EJECUTAR BÚSQUEDA CON MANEJO DE ERRORES MEJORADO
        try:
            print("🔍 Ejecutando consulta a ChromaDB...")
            
            # Preparar parámetros base
            query_params = {
                "n_results": n_results,
                "include": ["documents", "metadatas", "distances"]
            }
            
            # Agregar query (embedding o texto)
            if query_embedding:
                query_params["query_embeddings"] = [query_embedding]
                search_method = "embeddings"
            else:
                query_params["query_texts"] = [query]
                search_method = "text"
            
            # Agregar filtros solo si existen
            if where_conditions:
                query_params["where"] = where_conditions
                print(f"🔧 Aplicando filtros: {where_conditions}")
            else:
                print("🔧 Sin filtros aplicados")
            
            print(f"📋 Parámetros de consulta: {query_params}")
            
            # EJECUTAR CONSULTA
            results = collection.query(**query_params)
            print("✅ Consulta ejecutada exitosamente")
            
        except Exception as query_error:
            print(f"❌ Error en consulta ChromaDB: {query_error}")
            traceback.print_exc()
            
            # FALLBACK 1: Intentar sin filtros
            try:
                print("🔄 FALLBACK 1: Intentando sin filtros...")
                fallback_params = {
                    "n_results": n_results,
                    "include": ["documents", "metadatas", "distances"]
                }
                
                if query_embedding:
                    fallback_params["query_embeddings"] = [query_embedding]
                else:
                    fallback_params["query_texts"] = [query]
                
                results = collection.query(**fallback_params)
                search_method += "_no_filters"
                print("✅ Fallback 1 exitoso")
                
            except Exception as fallback_error:
                print(f"❌ Error en fallback 1: {fallback_error}")
                
                # FALLBACK 2: Solo búsqueda por texto sin filtros
                try:
                    print("🔄 FALLBACK 2: Solo texto, sin filtros...")
                    results = collection.query(
                        query_texts=[query],
                        n_results=n_results,
                        include=["documents", "metadatas", "distances"]
                    )
                    search_method = "text_simple"
                    print("✅ Fallback 2 exitoso")
                    
                except Exception as final_error:
                    print(f"❌ Error en fallback final: {final_error}")
                    raise HTTPException(
                        status_code=500, 
                        detail=f"Error en todas las búsquedas: {str(final_error)}"
                    )

        # 5. PROCESAR RESULTADOS
        try:
            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]
            
            print(f"📊 Resultados procesados: {len(documents)} documentos")
            
            matches = []
            
            for i, (doc, meta, distance) in enumerate(zip(documents, metadatas, distances)):
                try:
                    # Calcular similitud de manera segura
                    similarity_score = None
                    if distance is not None:
                        similarity_score = max(0, min(1, 1 - float(distance)))
                    
                    # Determinar match strength
                    if similarity_score is not None:
                        if similarity_score > 0.8:
                            match_strength = "Excelente"
                        elif similarity_score > 0.6:
                            match_strength = "Bueno"
                        elif similarity_score > 0.4:
                            match_strength = "Regular"
                        else:
                            match_strength = "Bajo"
                    else:
                        match_strength = "N/A"
                    
                    # Construir match con valores por defecto seguros
                    match = {
                        "cv_id": meta.get("cv_id", f"unknown_{i}"),
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
                        "similarity": f"{similarity_score * 100:.1f}%" if similarity_score is not None else "N/A",
                        "match_strength": match_strength,
                        "preview": str(doc)[:300] + "..." if len(str(doc)) > 300 else str(doc),
                        "distance": distance
                    }
                    
                    matches.append(match)
                    
                except Exception as match_error:
                    print(f"⚠️ Error procesando match {i}: {match_error}")
                    continue
            
            # Ordenar por distancia (menor = mejor)
            if matches and any(m.get("distance") is not None for m in matches):
                matches.sort(key=lambda x: x.get("distance", float('inf')))
            
            print(f"✅ Procesamiento completado: {len(matches)} matches válidos")
            
            return {
                "query": query,
                "search_method": f"ollama_{search_method}",
                "filters_applied": {
                    "min_score": min_score,
                    "industry": industry_filter,
                    "role": role_filter,
                    "seniority": seniority_filter
                },
                "total_matches": len(matches),
                "matches": matches,
                "debug_info": {
                    "collection_count": collection_count,
                    "embedding_used": query_embedding is not None,
                    "filters_used": where_conditions is not None,
                    "original_results": len(documents)
                }
            }
            
        except Exception as processing_error:
            print(f"❌ Error procesando resultados: {processing_error}")
            traceback.print_exc()
            raise HTTPException(
                status_code=500, 
                detail=f"Error procesando resultados: {str(processing_error)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ ERROR GENERAL: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500, 
            detail=f"Error interno del servidor: {str(e)}"
        )
    
# ========== CONSULTA CON LLM MEJORADA ==========

import traceback
import time
def query_with_llm_enhanced(question: str, context_filter: Optional[Dict] = None):
    """
    Consulta mejorada con diagnóstico completo para debugging
    """
    try:
        logger.info(f"🔍 INICIANDO CONSULTA: {question}")
        logger.info(f"🔧 Filtros aplicados: {context_filter}")
        
        # 1. VERIFICAR ESTADO DE LA COLECCIÓN
        try:
            collection_count = collection.count()
            logger.info(f"📊 Documentos en colección ChromaDB: {collection_count}")
            
            if collection_count == 0:
                logger.error("❌ LA COLECCIÓN ESTÁ VACÍA - No hay CVs indexados")
                return """
                *COLECCIÓN VACÍA**

                """
        except Exception as e:
            logger.error(f"❌ Error verificando colección: {e}")
            return f"❌ Error accediendo a la base de datos de CVs: {str(e)}"
        
        # 2. GENERAR EMBEDDING PARA LA PREGUNTA
        logger.info("🧠 Generando embedding para la pregunta...")
        question_embedding = generate_embedding(question)
        
        if not question_embedding:
            logger.error("❌ No se pudo generar embedding para la pregunta")
            # Fallback a búsqueda por texto
            logger.info("🔄 Fallback: usando búsqueda por texto")
        
        # 3. CONFIGURAR PARÁMETROS DE BÚSQUEDA
        search_params = {
            "n_results": 5, 
            "include": ["metadatas", "documents", "distances"]
        }
        
        if context_filter:
            search_params["where"] = context_filter
        
        # Usar embedding si está disponible, sino usar texto
        if question_embedding:
            search_params["query_embeddings"] = [question_embedding]
            search_method = "embeddings"
        else:
            search_params["query_texts"] = [question]
            search_method = "text"
            
        logger.info(f"🔍 Método de búsqueda: {search_method}")
        logger.info(f"📋 Parámetros de búsqueda: {search_params}")
        
        # 4. EJECUTAR BÚSQUEDA CON DIAGNÓSTICO
        try:
            logger.info("🔍 Ejecutando consulta en ChromaDB...")
            results = collection.query(**search_params)
            logger.info(f"✅ Consulta ejecutada. Estructura de respuesta: {list(results.keys())}")
            
        except Exception as e:
            logger.error(f"❌ Error en consulta ChromaDB: {e}")
            
            # Intentar consulta básica para diagnóstico
            try:
                logger.info("🔄 Intentando consulta básica para diagnóstico...")
                basic_results = collection.query(
                    query_texts=[question],
                    n_results=3,
                    include=["documents", "metadatas"]
                )
                logger.info(f"✅ Consulta básica exitosa: {len(basic_results.get('documents', [[]])[0])} resultados")
                results = basic_results
                
            except Exception as basic_error:
                logger.error(f"❌ Error en consulta básica: {basic_error}")
                return f"❌ Error ejecutando búsqueda: {str(e)}"
        
        # 5. PROCESAR Y ANALIZAR RESULTADOS
        docs = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        
        logger.info(f"📊 RESULTADOS OBTENIDOS:")
        logger.info(f"   - Documentos: {len(docs)}")
        logger.info(f"   - Metadatos: {len(metadatas)}")
        logger.info(f"   - Distancias: {len(distances)}")
        
        # DIAGNÓSTICO DETALLADO
        if not docs:
            # Intentar obtener algunos documentos para ver qué hay en la colección
            try:
                sample_results = collection.get(limit=3, include=["metadatas", "documents"])
                sample_docs = sample_results.get("documents", [])
                sample_metas = sample_results.get("metadatas", [])
                
                logger.info(f"📋 MUESTRA DE DOCUMENTOS EN COLECCIÓN ({len(sample_docs)} ejemplos):")
                for i, (doc, meta) in enumerate(zip(sample_docs[:3], sample_metas[:3])):
                    logger.info(f"   Doc {i+1}: {doc[:100]}...")
                    logger.info(f"   Meta {i+1}: {meta}")
                
                diagnosis = f"""
SIN MATCHES PARA TU CONSULTA**

**Tu consulta:** "{question}"
**Documentos en colección:** {collection_count}
**Método de búsqueda:** {search_method}

**ANÁLISIS:**
- La colección tiene {len(sample_docs)} documentos indexados
- Pero ninguno coincide semánticamente con tu búsqueda
- Esto puede deberse a:
  1. **Vocabulario diferente**: Los CVs usan términos diferentes
  2. **Falta de contexto**: Los CVs no tienen información sobre estudios actuales
  3. **Embeddings no optimizados**: El modelo no captura la semántica correctamente

**MUESTRA DE CONTENIDO DISPONIBLE:**
{chr(10).join([f"• {meta.get('nombre', 'N/A')} - {meta.get('role', 'N/A')} ({doc[:80]}...)" for doc, meta in zip(sample_docs[:3], sample_metas[:3])])}

**RECOMENDACIONES:**
1. **Prueba términos más específicos**: "desarrollador python", "asistente de administracion"
2. **Busca por habilidades concretas**: "tensorflow", "scikit-learn", "pandas"
3. **Usa filtros**: agrega industry_filter o role_filter
4. **Revisa los CVs disponibles**: usa `/cvs` para ver qué perfiles tienes

                """
                
                return diagnosis
                
            except Exception as sample_error:
                logger.error(f"❌ Error obteniendo muestra: {sample_error}")
                return f"❌ No se encontraron CVs relevantes y no se pudo obtener diagnóstico: {str(sample_error)}"

        # 6. Si hay resultados, continuar con el análisis normal
        context_parts = []
        for i, (doc, meta, distance) in enumerate(zip(docs, metadatas, distances), 1):
            similarity = round(1 - distance, 3) if distance is not None else "N/A"
            
            logger.info(f"   Resultado {i}: Similitud={similarity}, ID={meta.get('cv_id', 'N/A')}")
            
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

        # Prompt optimizado para el análisis
        prompt = f"""
Eres un reclutador senior experto con más de 15 años de experiencia en selección de personal tecnológico y empresarial. 

CONTEXTO - CANDIDATOS MÁS RELEVANTES:
{context}

CONSULTA DEL RECLUTADOR:
{question}

INSTRUCCIONES:
Analiza los candidatos encontrados y proporciona una recomendación estructurada.
Si la relevancia semántica es baja (<0.4), menciona que los matches no son ideales.

RESPUESTA (máximo 400 palabras):
        """
        logger.info("🤖 Enviando contexto a LLM para análisis...")
        
        try:
            response = ollama_client.chat(
                model="llama3",
                messages=[{"role": "user", "content": prompt}],
                options={
                    "temperature": 0.2,
                    "top_p": 0.9,
                    "num_ctx": 4096,
                    "num_predict": 600,
                },
                stream=False
            )
            
            if response and 'message' in response and 'content' in response['message']:
                content = response['message']['content'].strip()
                logger.info(f"✅ Análisis LLM completado: {len(content)} caracteres")
                return content
            else:
                logger.error("❌ Respuesta inválida del LLM")
                return f"✅ Encontrados {len(docs)} candidatos, pero error en análisis LLM."
                
        except Exception as llm_error:
            logger.error(f"❌ Error en LLM: {llm_error}")
            # Retornar análisis básico
            basic_analysis = f"""
✅ **CANDIDATOS ENCONTRADOS: {len(docs)}**

**RESULTADOS:**
{chr(10).join([f"• {meta.get('nombre', 'N/A')} - {meta.get('role', 'N/A')} (ID: {meta.get('cv_id', 'N/A')})" for meta in metadatas[:3]])}

**NOTA:** Error en análisis avanzado, pero los candidatos están disponibles para revisión manual.
            """
            return basic_analysis
        
    except Exception as e:
        logger.error(f"❌ Error general en query_with_llm_enhanced_debug: {e}")
        traceback.print_exc()
        return f"Error al procesar consulta: {str(e)}"

@app.get("/ask")
def ask_llm_enhanced(
    query: str,
    industry_filter: Optional[str] = None,
    min_score: Optional[float] = None,
    role_filter: Optional[str] = None,
    seniority_filter: Optional[str] = None
):
    """
    Consulta inteligente mejorada con datos de Ollama - ERROR JSON CORREGIDO
    """
    try:
        logger.info(f"🔍 Procesando consulta: {query}")
        logger.info(f"🎯 Filtros: industry={industry_filter}, min_score={min_score}, role={role_filter}, seniority={seniority_filter}")
        
        # Construir filtros opcionales
        context_filter = {}
        if industry_filter:
            context_filter["industry"] = {"$eq": industry_filter}
        if min_score is not None:
            context_filter["score"] = {"$gte": min_score}
        if role_filter:
            context_filter["role"] = {"$contains": role_filter}
        if seniority_filter:
            context_filter["seniority"] = {"$eq": seniority_filter}
        
        # Combinar filtros si hay múltiples
        if len(context_filter) > 1:
            context_filter = {"$and": list(context_filter.values())}
        elif len(context_filter) == 1:
            context_filter = list(context_filter.values())[0]
        else:
            context_filter = None
        
        logger.info(f"🔧 Filtros procesados: {context_filter}")
        
        answer = query_with_llm_enhanced(query, context_filter)
        
        return {
            "query": query,
            "filters_applied": {
                "industry": industry_filter,
                "min_score": min_score,
                "role": role_filter,
                "seniority": seniority_filter
            },
            "answer": answer,
            "processing_method": "ollama_enhanced_fixed",
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"❌ Error en ask_llm_enhanced: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error procesando consulta: {str(e)}")

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
    try:
        cvs = db.query(CV).all()
        updated_count = 0
        errors = []
        
        for cv in cvs:
            try:
                print(f"[INFO] Regenerando embedding para CV {cv.id}: {cv.filename}")
                
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
                    try:
                        collection.delete(ids=[str(cv.id)])
                    except Exception:
                        pass
                    
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
            "method": "sentence_transformers"
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)