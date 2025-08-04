import json
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from model import (
    CV, Experiencia, Educacion, Proyecto, Habilidad, CategoriaHabilidad,
    Lenguaje, Industria, Rol, Puesto
)

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
    
    def __init__(self, ollama_client, model: str = "llama2", db_session: Session = None):
        self.ollama_client = ollama_client
        self.model = model
        self.session = db_session
        
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



    def save_cv_from_analysis_corrected(self, analysis, filename: str):
        """
        Guarda CV desde análisis de Ollama con lógica corregida:
        - Industria: Sector de las empresas (Tecnología, Salud, etc.)
        - Rol: Cargo específico (Pasante, Desarrollador Backend, etc.)
        - Puesto: Nivel seniority (Junior, Senior, etc.)
        """
        try:
            print(f"[INFO] Guardando CV con lógica corregida: {analysis.nombre}")
            
            # 1. INDUSTRIA: Determinar el sector principal
            industria = self.determine_main_industry(analysis)
            
            # 2. ROL: Obtener o crear el rol específico
            rol = self.get_or_create_role(analysis.rol_sugerido)
            
            # 3. PUESTO: Determinar el nivel de seniority
            puesto = self.get_or_create_seniority_level(analysis.seniority, analysis.anos_experiencia)
            
            # 4. Crear CV principal
            cv = CV(
                filename=filename,
                contenido=analysis.embedding_text or "Contenido procesado con Ollama",
                
                # Información personal
                nombre_completo=analysis.nombre if analysis.nombre != "N/A" else None,
                email=analysis.email if analysis.email and analysis.email != "N/A" else None,
                telefono=analysis.telefono if analysis.telefono and analysis.telefono not in ["N/A", "No disponible"] else None,
                ubicacion=None,
                linkedin_url=analysis.linkedin if analysis.linkedin and analysis.linkedin != "N/A" else None,
                github_url=analysis.github if analysis.github and analysis.github != "N/A" else None,
                portafolio_url=analysis.portafolio if analysis.portafolio and analysis.portafolio != "N/A" else None,
                
                # Clasificación PRINCIPAL del candidato
                id_rol=rol.id if rol else None,                    # ROL que busca/tiene
                id_puesto=puesto.id if puesto else None,           # SENIORITY 
                id_industria=industria.id if industria else None,  # INDUSTRIA objetivo/principal
                
                # Métricas
                overall_score=analysis.overall_score,
                anhos_experiencia=analysis.anos_experiencia,
                processed_status="completed"
            )
            
            self.session.add(cv)
            self.session.flush()  # Para obtener el ID del CV
            
            # 5. EXPERIENCIAS: Cada una con su industria específica
            for exp in analysis.experiencias:
                if isinstance(exp, dict):
                    # Determinar industria específica de esta empresa
                    exp_industria = self.determine_company_industry(exp.get('empresa', ''), exp.get('descripcion', ''))
                    
                    experiencia = Experiencia(
                        id_cv=cv.id,
                        empresa=exp.get('empresa', 'N/A'),
                        posicion=exp.get('puesto', 'N/A'),  # El ROL en esa empresa específica
                        descripcion=exp.get('descripcion', None),
                        id_industria=exp_industria.id if exp_industria else industria.id,  # Industria específica o principal
                        es_actual=exp.get('actual', False)
                    )
                    self.session.add(experiencia)
            
            # 6. Procesar habilidades técnicas
            for habilidad_nombre in analysis.habilidades_tecnicas:
                if habilidad_nombre.lower() not in ['n/a', '']:
                    habilidad = self.get_or_create_skill(habilidad_nombre, industria)
                    if habilidad and habilidad not in cv.habilidades:
                        cv.habilidades.append(habilidad)
            
            # 7. Procesar idiomas
            for idioma_info in analysis.idiomas:
                if isinstance(idioma_info, dict) and 'idioma' in idioma_info:
                    idioma_nombre = idioma_info['idioma']
                else:
                    idioma_nombre = str(idioma_info)
                    
                if idioma_nombre.lower() not in ['n/a', 'español', 'spanish']:
                    idioma = self.get_or_create_language(idioma_nombre)
                    if idioma and idioma not in cv.lenguajes:
                        cv.lenguajes.append(idioma)
            
            # 8. Procesar educación
            for edu in analysis.educacion:
                if isinstance(edu, dict):
                    educacion = Educacion(
                        id_cv=cv.id,
                        grado=edu.get('titulo', 'N/A'),
                        institucion=edu.get('institucion', 'N/A'),
                        campo_estudio=edu.get('campo', None),
                        esta_cursando=edu.get('en_curso', False)
                    )
                    self.session.add(educacion)
            
            # 9. Procesar proyectos
            for proyecto in analysis.proyectos_destacados:
                if isinstance(proyecto, dict):
                    proyecto_obj = Proyecto(
                        id_cv=cv.id,
                        nombre=proyecto.get('nombre', 'Proyecto'),
                        descripcion=proyecto.get('descripcion', ''),
                        tecnologias_usadas=', '.join(proyecto.get('tecnologias', []))
                    )
                    self.session.add(proyecto_obj)
            
            # 10. Confirmar cambios
            self.session.commit()
            
            print(f"[SUCCESS] CV guardado con nueva lógica:")
            print(f"  - ID: {cv.id}")
            print(f"  - Nombre: {cv.nombre_completo}")
            print(f"  - Rol: {rol.nombre if rol else 'N/A'}")
            print(f"  - Seniority: {puesto.nombre if puesto else 'N/A'}")
            print(f"  - Industria principal: {industria.nombre if industria else 'N/A'}")
            print(f"  - Score: {cv.overall_score}")
            
            return cv
            
        except Exception as e:
            self.session.rollback()
            print(f"[ERROR] Error guardando CV: {e}")
            raise Exception(f"Error guardando CV: {e}")

    def determine_main_industry(self, analysis):
        """
        Determina la industria principal basada en el sector mencionado y experiencias
        """
        # Mapeo de términos a industrias
        industry_mapping = {
            'tecnología': 'Tecnología',
            'software': 'Tecnología', 
            'informática': 'Tecnología',
            'it': 'Tecnología',
            'desarrollo': 'Tecnología',
            'salud': 'Salud',
            'medicina': 'Salud',
            'hospital': 'Salud',
            'finanzas': 'Finanzas',
            'banco': 'Finanzas',
            'financiero': 'Finanzas',
            'educación': 'Educación',
            'universidad': 'Educación',
            'enseñanza': 'Educación',
            'manufactura': 'Manufactura',
            'producción': 'Manufactura',
            'fábrica': 'Manufactura',
            'consultoría': 'Servicios',
            'servicios': 'Servicios',
            'retail': 'Retail',
            'ventas': 'Retail',
            'comercio': 'Retail'
        }
        
        # Primero intentar con el sector del análisis
        if analysis.sector and analysis.sector.lower() not in ['n/a', 'general', '']:
            sector_lower = analysis.sector.lower()
            for key, industry in industry_mapping.items():
                if key in sector_lower:
                    return self.get_or_create_industry(industry)
        
        # Si no, analizar las experiencias para inferir industria
        industry_votes = {}
        for exp in analysis.experiencias:
            if isinstance(exp, dict):
                empresa = exp.get('empresa', '').lower()
                descripcion = exp.get('descripcion', '').lower()
                texto_completo = f"{empresa} {descripcion}"
                
                for key, industry in industry_mapping.items():
                    if key in texto_completo:
                        industry_votes[industry] = industry_votes.get(industry, 0) + 1
        
        # Usar la industria con más votos
        if industry_votes:
            main_industry = max(industry_votes, key=industry_votes.get)
            return self.get_or_create_industry(main_industry)
        
        # Por defecto, usar "General"
        return self.get_or_create_industry("General")

    def determine_company_industry(self, empresa_nombre, descripcion=""):
        """
        Determina la industria específica de una empresa
        """
        texto = f"{empresa_nombre} {descripcion}".lower()
        
        # Empresas específicas conocidas
        known_companies = {
            'google': 'Tecnología',
            'microsoft': 'Tecnología',
            'amazon': 'Tecnología',
            'meta': 'Tecnología',
            'facebook': 'Tecnología',
            'netflix': 'Tecnología',
            'uber': 'Tecnología',
            'airbnb': 'Tecnología',
            'merit': 'Tecnología',  # Del ejemplo del CV
            'hospital': 'Salud',
            'clínica': 'Salud',
            'banco': 'Finanzas',
            'universidad': 'Educación'
        }
        
        for company, industry in known_companies.items():
            if company in texto:
                return self.get_or_create_industry(industry)
        
        # Palabras clave por industria
        industry_keywords = {
            'Tecnología': ['software', 'desarrollo', 'programación', 'sistemas', 'it', 'tech', 'digital'],
            'Salud': ['salud', 'médico', 'hospital', 'clínica', 'farmacia', 'medicina'],
            'Finanzas': ['banco', 'financiero', 'seguros', 'inversión', 'crédito', 'fintech'],
            'Educación': ['educación', 'universidad', 'colegio', 'instituto', 'enseñanza', 'académico'],
            'Manufactura': ['manufactura', 'fábrica', 'producción', 'industrial', 'planta'],
            'Retail': ['retail', 'ventas', 'comercio', 'tienda', 'supermercado'],
            'Servicios': ['consultoría', 'servicios', 'asesoría', 'consultores']
        }
        
        for industry, keywords in industry_keywords.items():
            for keyword in keywords:
                if keyword in texto:
                    return self.get_or_create_industry(industry)
        
        # Si no se puede determinar, retornar None para usar la industria principal
        return None
    
    def get_or_create_industry(self, nombre: str):
        """Obtener o crear industria"""
        industria = self.session.query(Industria).filter(
            Industria.nombre.ilike(f"%{nombre}%")
        ).first()
        
        if not industria:
            industria = Industria(
                nombre=nombre.title(),
                descripcion=f"Industria de {nombre.lower()}"
            )
            self.session.add(industria)
            self.session.flush()
            
        return industria

    def get_or_create_role(self, rol_nombre: str):
        """Obtener o crear rol (independiente de industria)"""
        if not rol_nombre or rol_nombre.lower() in ['n/a', '']:
            return None
            
        rol = self.session.query(Rol).filter(
            Rol.nombre.ilike(f"%{rol_nombre}%")
        ).first()
        
        if not rol:
            # Mapeo de roles comunes
            role_mapping = {
                'pasante': 'Pasante',
                'intern': 'Pasante',
                'desarrollador backend': 'Desarrollador Backend',
                'backend developer': 'Desarrollador Backend',
                'desarrollador frontend': 'Desarrollador Frontend',
                'frontend developer': 'Desarrollador Frontend',
                'full stack': 'Desarrollador Full Stack',
                'fullstack': 'Desarrollador Full Stack',
                'analista': 'Analista de Sistemas',
                'qa': 'QA Tester',
                'tester': 'QA Tester',
                'devops': 'DevOps Engineer',
                'data analyst': 'Data Analyst',
                'project manager': 'Project Manager',
                'product manager': 'Product Manager',
                'designer': 'Designer',
                'consultor': 'Consultor',
                'gerente': 'Gerente'
            }
            
            # Buscar mapeo
            rol_normalizado = role_mapping.get(rol_nombre.lower(), rol_nombre.title())
            
            rol = Rol(
                nombre=rol_normalizado,
                descripcion=f"Rol de {rol_normalizado.lower()}"
            )
            self.session.add(rol)
            self.session.flush()
            
        return rol

    def get_or_create_seniority_level(self, seniority: str, anos_experiencia: int = 0):
        """Obtener o crear nivel de seniority"""
        if not seniority or seniority.lower() in ['n/a', '']:
            # Inferir seniority por años de experiencia
            if anos_experiencia == 0:
                seniority = "Estudiante"
            elif anos_experiencia <= 1:
                seniority = "Trainee"
            elif anos_experiencia <= 2:
                seniority = "Junior"
            elif anos_experiencia <= 4:
                seniority = "Semi-Senior"
            elif anos_experiencia <= 8:
                seniority = "Senior"
            else:
                seniority = "Lead"
        
        # Mapeo de seniority
        seniority_mapping = {
            'estudiante': 'Estudiante',
            'student': 'Estudiante',
            'trainee': 'Trainee',
            'junior': 'Junior',
            'jr': 'Junior',
            'semi senior': 'Semi-Senior',
            'semi-senior': 'Semi-Senior',
            'middle': 'Semi-Senior',
            'mid': 'Semi-Senior',
            'senior': 'Senior',
            'sr': 'Senior',
            'lead': 'Lead',
            'líder': 'Lead',
            'manager': 'Manager',
            'gerente': 'Manager',
            'director': 'Director'
        }
        
        seniority_normalizado = seniority_mapping.get(seniority.lower(), seniority.title())
        
        puesto = self.session.query(Puesto).filter(
            Puesto.nombre.ilike(f"%{seniority_normalizado}%")
        ).first()
        
        if not puesto:
            # Definir rangos de años por defecto
            year_ranges = {
                'Estudiante': (0, 0),
                'Trainee': (0, 1),
                'Junior': (0, 2),
                'Semi-Senior': (2, 4),
                'Senior': (4, 8),
                'Lead': (6, 12),
                'Manager': (8, None),
                'Director': (10, None)
            }
            
            min_years, max_years = year_ranges.get(seniority_normalizado, (anos_experiencia, None))
            
            puesto = Puesto(
                nombre=seniority_normalizado,
                min_anhos=min_years,
                max_anhos=max_years
            )
            self.session.add(puesto)
            self.session.flush()
            
        return puesto

    def get_or_create_skill(self, nombre: str, industria=None):
        """Obtener o crear habilidad"""
        habilidad = self.session.query(Habilidad).filter(
            Habilidad.nombre.ilike(f"%{nombre}%")
        ).first()
        
        if not habilidad:
            # Obtener o crear categoría técnica
            categoria = self.session.query(CategoriaHabilidad).filter(
                CategoriaHabilidad.nombre == "Técnica"
            ).first()
            
            if not categoria:
                categoria = CategoriaHabilidad(
                    nombre="Técnica",
                    descripcion="Habilidades técnicas y programación"
                )
                self.session.add(categoria)
                self.session.flush()
            
            habilidad = Habilidad(
                nombre=nombre,
                id_categoria=categoria.id,
                id_industria=industria.id if industria else None
            )
            self.session.add(habilidad)
            self.session.flush()
            
        return habilidad

    def get_or_create_language(self, nombre: str):
        """Obtener o crear idioma"""
        # Mapear nombres a códigos ISO
        language_mapping = {
            'español': ('Español', 'es'),
            'spanish': ('Español', 'es'),
            'english': ('Inglés', 'en'),
            'inglés': ('Inglés', 'en'),
            'portuguese': ('Portugués', 'pt'),
            'portugués': ('Portugués', 'pt'),
            'french': ('Francés', 'fr'),
            'francés': ('Francés', 'fr'),
            'german': ('Alemán', 'de'),
            'alemán': ('Alemán', 'de'),
            'italian': ('Italiano', 'it'),
            'italiano': ('Italiano', 'it'),
            'japanese': ('Japonés', 'ja'),
            'japonés': ('Japonés', 'ja'),
            'chinese': ('Chino', 'zh'),
            'chino': ('Chino', 'zh')
        }
        
        nombre_lower = nombre.lower()
        nombre_normalizado, iso_code = language_mapping.get(nombre_lower, (nombre.title(), nombre.lower()[:2]))
        
        idioma = self.session.query(Lenguaje).filter(
            Lenguaje.nombre.ilike(f"%{nombre_normalizado}%")
        ).first()
        
        if not idioma:
            idioma = Lenguaje(
                nombre=nombre_normalizado,
                iso_code=iso_code
            )
            self.session.add(idioma)
            self.session.flush()
            
        return idioma

    # MÉTODO PARA DEBUGGING - Ver cómo se clasificó un CV
    def debug_cv_classification(self, cv_id: int):
        """
        Método de debugging para ver cómo se clasificó un CV
        """
        cv = self.session.query(CV).filter(CV.id == cv_id).first()
        if not cv:
            return {"error": "CV no encontrado"}
        
        return {
            "cv_info": {
                "id": cv.id,
                "nombre": cv.nombre_completo,
                "filename": cv.filename,
                "score": cv.overall_score,
                "años_experiencia": cv.anhos_experiencia
            },
            "clasificacion": {
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
                }
            },
            "experiencias": [
                {
                    "empresa": exp.empresa,
                    "posicion": exp.posicion,
                    "industria": exp.industria.nombre if exp.industria else None,
                    "actual": exp.es_actual
                }
                for exp in cv.experiencias
            ],
            "habilidades": [h.nombre for h in cv.habilidades],
            "idiomas": [l.nombre for l in cv.lenguajes],
            "educacion_count": len(cv.educacion),
            "proyectos_count": len(cv.proyectos)
        }
def create_cv_embedding_text_enhanced(analysis: CVAnalysis) -> str:

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