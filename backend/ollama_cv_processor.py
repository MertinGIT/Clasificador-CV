import json
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class CVAnalysis:
    """Estructura para almacenar el análisis completo del CV"""
    # Información básica
    nombre: str
    email: str
    telefono: str
    linkedin: str
    github: str
    portafolio: str
    
    # Perfil profesional
    rol_sugerido: str
    seniority: str
    sector: str
    anos_experiencia: int
    resumen_profesional: str
    
    # Habilidades y competencias
    habilidades_tecnicas: List[str]
    soft_skills: List[str]
    idiomas: List[Dict[str, str]]  # [{"idioma": "Inglés", "nivel": "Intermedio"}]
    
    # Educación y certificaciones
    educacion: List[Dict[str, str]]
    certificaciones: List[str]
    
    # Experiencia y proyectos
    experiencias: List[Dict[str, Any]]
    proyectos_destacados: List[Dict[str, str]]
    
    # Insights adicionales
    fortalezas: List[str]
    areas_mejora: List[str]
    industrias_relacionadas: List[str]
    
    # Puntuación y calidad
    overall_score: float
    calidad_cv: str  # "Excelente", "Buena", "Regular", "Deficiente"
    
    # Texto para embedding
    embedding_text: str


class OllamaCVProcessor:
    """Procesador de CVs usando Ollama para análisis inteligente"""
    
    def __init__(self, ollama_client, model: str = "llama2"):
        """
        ollama_client: Cliente de Ollama
        model: Modelo a usar (llama2, mixtral, codellama, etc.)
        """
        self.ollama_client = ollama_client
        self.model = model
        
    def create_analysis_prompt(self, cv_text: str) -> str:
        """Crea el prompt para que Ollama analice el CV"""
        
        prompt = f"""
        Eres un reclutador técnico senior con más de 15 años de experiencia en selección de talentos tecnológicos, incluyendo perfiles junior, estudiantes y pasantes.

        TAREA:
        Analiza el siguiente CV en español y extrae toda la información posible en formato JSON **válido** y **completo**, aunque el candidato tenga poca experiencia laboral.

        TEXTO DEL CV:
        {cv_text}

        INSTRUCCIONES:
        1. Si el CV tiene poca experiencia, deduce habilidades técnicas y blandas desde la formación, herramientas o intereses.
        2. Extrae nombre completo, email, teléfono, y redes si están presentes.
        3. Clasifica el rol profesional sugerido (ej:pasante, Backend Junior, backend senior, asistente administrativo, etc.).
        4. Determina la seniority: "Estudiante", "Junior", "Semi-Senior", "Senior".
        5. Deduce el sector/industria (ej: Tecnología, Educación, Electrónica).
        6. Extrae herramientas, lenguajes de programación, conocimientos relevantes.
        7. Lista soft skills incluso si no están explícitas (deduce de descripciones: ganas de aprender, mente abierta, etc.).
        8. Idiomas con nivel estimado si no se especifica claro.
        9. Educación (nivel, institución, estado: "En curso", "Finalizado", etc.).
        10. Experiencia profesional y pasantías si existen.
        11. Proyectos propios o académicos si están descritos.
        12. Fortalezas percibidas y posibles áreas de mejora.
        13. Score de CV (0-100) basado en claridad, completitud, proyección.
        14. Embedding de texto profesional para búsqueda semántica.

        IMPORTANTE:
        - Responde con JSON válido (sin comentarios, sin markdown, sin explicaciones).
        - Si falta información, usar null o []
        - Usa español excepto nombres de tecnologías
        - Rol sugerido debe ser acorde al nivel (evita "Senior" si es estudiante)
        - Usa lenguaje limpio y profesional

        ESQUEMA DEL JSON:

        {{
        "informacion_personal": {{
            "nombre": "...",
            "email": "...",
            "telefono": "...",
            "linkedin": "...",
            "github": "...",
            "portafolio": "..."
        }},
        "perfil_profesional": {{
            "rol_sugerido": "...",
            "seniority": "...",
            "sector": "...",
            "anos_experiencia": ...,
            "resumen_profesional": "..."
        }},
        "competencias": {{
            "habilidades_tecnicas": [...],
            "soft_skills": [...],
            "idiomas": [
            {{"idioma": "...", "nivel": "..."}}
            ]
        }},
        "formacion": {{
            "educacion": [...],
            "certificaciones": [...]
        }},
        "experiencia": {{
            "experiencias": [...],
            "proyectos_destacados": [...]
        }},
        "insights": {{
            "fortalezas": [...],
            "areas_mejora": [...],
            "industrias_relacionadas": [...]
        }},
        "evaluacion": {{
            "overall_score": ...,
            "calidad_cv": "...",
            "comentarios": "..."
        }},
        "embedding_optimizado": {{
            "texto_embedding": "..."
        }}
        }}
        """
        
        return prompt
    
    def process_cv_with_ollama(self, cv_text: str) -> CVAnalysis:
        """Procesa un CV usando Ollama y retorna análisis estructurado"""
        
        try:
            print(f"[INFO] Procesando CV con Ollama modelo: {self.model}")
            
            # Crear prompt
            prompt = self.create_analysis_prompt(cv_text)
            
            # Llamar a Ollama
            response = self.ollama_client.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                options={
                    "temperature": 0.1,  # Más determinístico
                    "top_p": 0.9,
                    "top_k": 40,
                    "num_ctx": 4096,  # Contexto suficiente para CVs largos
                }
            )
            
            response_content = response['message']['content']
            print(f"[DEBUG] Respuesta de Ollama recibida: {len(response_content)} caracteres")
            
            # Parsear respuesta JSON
            analysis_data = self._parse_ollama_response(response_content)
            
            # Convertir a objeto CVAnalysis
            cv_analysis = self._create_cv_analysis_object(analysis_data)
            
            print(f"[SUCCESS] Análisis completado para: {cv_analysis.nombre}")
            
            return cv_analysis
            
        except Exception as e:
            print(f"[ERROR] Error procesando CV con Ollama: {str(e)}")
            # Retornar análisis básico como fallback
            return self._create_fallback_analysis(cv_text)
    
    def _parse_ollama_response(self, response: str) -> Dict:
        """Parsea la respuesta JSON de Ollama"""
        try:
            # Limpiar respuesta si tiene texto extra
            response = response.strip()
            
            # Buscar JSON válido en la respuesta
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = response
            
            # Parsear JSON
            return json.loads(json_str)
            
        except json.JSONDecodeError as e:
            print(f"[ERROR] Error parseando JSON de Ollama: {e}")
            print(f"[DEBUG] Respuesta problemática: {response[:300]}...")
            
            # Intentar parsear línea por línea para encontrar JSON válido
            lines = response.split('\n')
            for i, line in enumerate(lines):
                if line.strip().startswith('{'):
                    try:
                        remaining_text = '\n'.join(lines[i:])
                        return json.loads(remaining_text)
                    except:
                        continue
            
            raise Exception("No se pudo extraer JSON válido de la respuesta de Ollama")
    
    def _create_cv_analysis_object(self, data: Dict) -> CVAnalysis:
        """Convierte el diccionario de Ollama a objeto CVAnalysis"""
        
        info_personal = data.get("informacion_personal", {})
        perfil = data.get("perfil_profesional", {})
        competencias = data.get("competencias", {})
        formacion = data.get("formacion", {})
        experiencia = data.get("experiencia", {})
        insights = data.get("insights", {})
        evaluacion = data.get("evaluacion", {})
        embedding = data.get("embedding_optimizado", {})
        
        return CVAnalysis(
            # Información básica
            nombre=info_personal.get("nombre", "Nombre no detectado"),
            email=info_personal.get("email") or "",
            telefono=info_personal.get("telefono") or "",
            linkedin=info_personal.get("linkedin") or "",
            github=info_personal.get("github") or "",
            portafolio=info_personal.get("portafolio") or "",
            
            # Perfil profesional
            rol_sugerido=perfil.get("rol_sugerido", "Por definir"),
            seniority=perfil.get("seniority", "Junior"),
            sector=perfil.get("sector", "General"),
            anos_experiencia=perfil.get("anos_experiencia", 0),
            resumen_profesional=perfil.get("resumen_profesional", ""),
            
            # Habilidades y competencias
            habilidades_tecnicas=competencias.get("habilidades_tecnicas", []),
            soft_skills=competencias.get("soft_skills", []),
            idiomas=competencias.get("idiomas", []),
            
            # Educación
            educacion=formacion.get("educacion", []),
            certificaciones=formacion.get("certificaciones", []),
            
            # Experiencia
            experiencias=experiencia.get("experiencias", []),
            proyectos_destacados=experiencia.get("proyectos_destacados", []),
            
            # Insights
            fortalezas=insights.get("fortalezas", []),
            areas_mejora=insights.get("areas_mejora", []),
            industrias_relacionadas=insights.get("industrias_relacionadas", []),
            
            # Evaluación
            overall_score=float(evaluacion.get("overall_score", 50.0)),
            calidad_cv=evaluacion.get("calidad_cv", "Regular"),
            
            # Embedding
            embedding_text=embedding.get("texto_embedding", "")
        )
    
    def _create_fallback_analysis(self, cv_text: str) -> CVAnalysis:
        """Crea un análisis básico si falla Ollama"""
        print("[WARNING] Usando análisis de fallback")
        
        # Intentar extraer información básica con regex
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', cv_text)
        phone_match = re.search(r'(\+595|0)?\s?9\d{8}|\(\d{3}\)\s?\d{3}-?\d{4}', cv_text)
        
        return CVAnalysis(
            nombre="Nombre no detectado",
            email=email_match.group(0) if email_match else "",
            telefono=phone_match.group(0) if phone_match else "",
            linkedin="", github="", portafolio="",
            rol_sugerido="Por definir",
            seniority="Junior",
            sector="General",
            anos_experiencia=0,
            resumen_profesional="Análisis pendiente - Error en procesamiento",
            habilidades_tecnicas=[],
            soft_skills=[],
            idiomas=[],
            educacion=[],
            certificaciones=[],
            experiencias=[],
            proyectos_destacados=[],
            fortalezas=[],
            areas_mejora=["Requerir reprocesamiento"],
            industrias_relacionadas=[],
            overall_score=30.0,
            calidad_cv="Por evaluar",
            embedding_text=f"Información del candidato: {cv_text[:500]}..."
        )


def create_cv_embedding_text_enhanced(analysis: CVAnalysis) -> str:
    """
    Crea texto optimizado para embeddings usando el análisis de Ollama
    """
    embedding_parts = []
    
    # Usar el texto optimizado por Ollama si está disponible
    if analysis.embedding_text:
        return analysis.embedding_text
    
    # Fallback: construir manualmente
    if analysis.nombre:
        embedding_parts.append(f"Nombre: {analysis.nombre}")
    
    if analysis.rol_sugerido:
        embedding_parts.append(f"Rol: {analysis.rol_sugerido}")
    
    if analysis.seniority:
        embedding_parts.append(f"Nivel: {analysis.seniority}")
        
    if analysis.anos_experiencia > 0:
        embedding_parts.append(f"Experiencia: {analysis.anos_experiencia} años")
    
    if analysis.habilidades_tecnicas:
        embedding_parts.append("Habilidades técnicas: " + ", ".join(analysis.habilidades_tecnicas))
    
    if analysis.soft_skills:
        embedding_parts.append("Soft skills: " + ", ".join(analysis.soft_skills))
    
    if analysis.idiomas:
        idiomas_text = ", ".join([f"{lang['idioma']} ({lang.get('nivel', 'N/A')})" for lang in analysis.idiomas])
        embedding_parts.append(f"Idiomas: {idiomas_text}")
    
    if analysis.sector:
        embedding_parts.append(f"Sector: {analysis.sector}")
    
    if analysis.resumen_profesional:
        embedding_parts.append(f"Resumen: {analysis.resumen_profesional}")
    
    return "\n".join(embedding_parts)