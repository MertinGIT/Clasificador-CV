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
    
    def __init__(self, ollama_client, model: str = "llama3", db_session: Session = None):
        self.ollama_client = ollama_client
        self.model = model
        self.session = db_session
        
    def create_analysis_prompt(self, cv_text: str) -> str:
        prompt = f"""
        Eres un reclutador senior especializado en análisis de talento con más de 15 años de experiencia en múltiples industrias.

        TAREA CRÍTICA:
        Analiza este CV y extrae TODA la información relevante, priorizando la EXPERIENCIA LABORAL sobre la educación para determinar el perfil profesional del candidato.

        TEXTO DEL CV:
        {cv_text}

        INSTRUCCIONES ESPECÍFICAS:

        🎯 ROL PROFESIONAL (LÓGICA GENERAL):
        1. PRIORIZA experiencia laboral reciente y contenido de trabajo actual
        2. Identifica el área principal basándote en la experiencia práctica:
        
        **TECNOLOGÍA E IT:**
        - Desarrollo: Frontend, Backend, Full Stack, Mobile
        - DevOps: Infrastructure, Cloud, CI/CD
        - QA: Testing, Automation, Quality Assurance
        - Data: Data Science, Analytics, Business Intelligence
        - Soporte: Help Desk, IT Support, System Administration
        - Ciberseguridad: Security Analyst, Pentesting
        
        **NEGOCIOS Y ADMINISTRACIÓN:**
        - Marketing: Digital, Tradicional, Content, SEO/SEM, Social Media
        - Ventas: B2B, B2C, Account Management, Business Development
        - Recursos Humanos: Reclutamiento, Capacitación, Compensaciones, Relaciones Laborales
        - Finanzas: Contabilidad, Análisis Financiero, Auditoría, Tesorería, Control de Gestión
        - Operaciones: Logística, Supply Chain, Producción, Calidad, Mejora Continua
        - Consultoría: Management, Estrategia, Procesos, Especializada
        - Administración: Gestión General, Coordinación, Supervisión
        
        **CREATIVIDAD Y COMUNICACIÓN:**
        - Diseño: Gráfico, UX/UI, Industrial, Arquitectura, Interiorismo
        - Marketing Creativo: Publicidad, Branding, Campañas
        - Comunicación: Relaciones Públicas, Comunicación Interna, Periodismo
        - Contenido: Redacción, Content Management, Copywriting
        
        **SERVICIOS ESPECIALIZADOS:**
        - Educación: Docencia, Capacitación, Desarrollo Curricular, Investigación
        - Salud: Medicina, Enfermería, Psicología, Terapias, Administración Hospitalaria
        - Legal: Abogacía, Compliance, Contratos, Propiedad Intelectual
        - Ingeniería: Civil, Industrial, Mecánica, Eléctrica, Química
        - Arquitectura: Diseño Arquitectónico, Urbanismo, Construcción
        
        **SECTORES ESPECÍFICOS:**
        - Agro: Agronomía, Veterinaria, Producción Agrícola
        - Turismo: Hotelería, Gastronomía, Gestión Turística
        - Retail: Comercio, Merchandising, Customer Experience
        - Manufactura: Producción, Mantenimiento, Supervisión Industrial
        - Logística: Transporte, Almacenamiento, Distribución
        
        3. Combina áreas si aplica: "Marketing Digital y Ventas", "Finanzas y Operaciones", etc.
        4. Solo usar títulos educativos si NO hay experiencia laboral relevante

        💼 EXTRACCIÓN DE HABILIDADES Y COMPETENCIAS:
        Busca MINUCIOSAMENTE todas estas competencias en TODO el CV según el área:

        **TECNOLOGÍA:**
        - Lenguajes: Python, Java, JavaScript, C#, PHP, etc.
        - Frameworks: React, Angular, Laravel, Spring, Django, etc.
        - Bases de Datos: MySQL, PostgreSQL, MongoDB, Oracle, etc.
        - Cloud: AWS, Azure, Google Cloud, Heroku
        - DevOps: Docker, Kubernetes, Jenkins, Git
        - Metodologías: Scrum, Kanban, Agile

        **MARKETING Y VENTAS:**
        - Plataformas: Google Ads, Facebook Ads, LinkedIn Ads
        - Analytics: Google Analytics, Facebook Insights, SEMrush
        - CRM: Salesforce, HubSpot, Pipedrive, Zoho
        - Email Marketing: Mailchimp, Constant Contact
        - SEO/SEM: Keyword research, Link building, PPC
        - Social Media: Content planning, Community management

        **FINANZAS Y CONTABILIDAD:**
        - Software: SAP, ERP, Tango, ContaPlus, QuickBooks
        - Análisis: Excel avanzado, Power BI, Tableau, SQL
        - Normativas: NIIF, PCGA, SOX, Basel
        - Áreas: Presupuestos, Tesorería, Auditoría, Impuestos

        **RECURSOS HUMANOS:**
        - HRIS: Workday, BambooHR, SAP SuccessFactors
        - Reclutamiento: LinkedIn Recruiter, Bumeran, ZonaJobs
        - Evaluación: 360°, Assessment centers, OKRs
        - Capacitación: LMS, e-learning, coaching

        **DISEÑO Y CREATIVIDAD:**
        - Software: Adobe Suite (Photoshop, Illustrator, InDesign)
        - UI/UX: Figma, Sketch, Adobe XD, InVision
        - 3D: AutoCAD, 3ds Max, SketchUp, Blender
        - Video: Premiere, After Effects, Final Cut

        **OPERACIONES Y LOGÍSTICA:**
        - ERP: SAP, Oracle, Microsoft Dynamics
        - WMS: Warehouse Management Systems
        - Metodologías: Lean, Six Sigma, Kaizen
        - Supply Chain: Planificación, Procurement

        **SALUD:**
        - Software: HIS, EMR, PACS
        - Especialidades: Cardiología, Pediatría, etc.
        - Certificaciones: CPR, BLS, especialidades médicas

        **LEGAL:**
        - Áreas: Derecho civil, penal, laboral, corporativo
        - Software: LexisNexis, Westlaw, sistemas legales locales

        **HERRAMIENTAS GENERALES:**
        Microsoft Office, Google Workspace, Slack, Trello, Jira, Notion, Zoom, Teams

        EXTRACCIÓN DE FECHAS DE EXPERIENCIA:
        - Busca fechas explícitas: "2020-2023", "Enero 2022 - Presente", etc.
        - Si solo hay duración: "2 años de experiencia" → estima fecha_inicio desde hoy hacia atrás
        - Si es trabajo actual: fecha_fin = null
        - Si no hay fechas: usa fecha_inicio = "2020-01-01" (estimación conservadora)
        - Formato requerido: "YYYY-MM-DD"

        🔍 SENIORITY BASADO EN EXPERIENCIA LABORAL REAL:
        - Analizar fechas de experiencia laboral, NO educación
        - Contar SOLO experiencia profesional relevante en el área
        - 0 meses profesional: "Estudiante/Sin experiencia" 
        - 0-6 meses: "Trainee/Practicante"
        - 6 meses - 2 años: "Junior"
        - 2-5 años: "Semi-Senior" 
        - 5-8 años: "Senior"
        - 8+ años: "Expert/Líder"

        📊 SCORING MEJORADO (UNIVERSAL):
        - Experiencia laboral relevante actual: +30 puntos
        - Diversidad de competencias en su área: +20 puntos
        - Logros y resultados cuantificables: +20 puntos
        - Certificaciones y especializaciones: +15 puntos
        - Educación relevante al área: +10 puntos
        - CV bien estructurado y claro: +5 puntos

        🏢 IDENTIFICACIÓN DE SECTOR:
        Determina el sector principal basándote en la experiencia:
        - Tecnología, Finanzas, Salud, Educación, Retail, Manufactura, 
        - Consultoría, Marketing, Telecomunicaciones, Energía, Agro,
        - Turismo, Legal, Ingeniería, Arquitectura, Arte, etc.

        FORMATO DE RESPUESTA EXACTO:
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
            "habilidades_tecnicas": [
                "SOLO incluir habilidades EXPLÍCITAMENTE mencionadas en el CV - pueden ser técnicas, software, metodologías, certificaciones, según el área profesional"
            ],
            "soft_skills": [...],
            "idiomas": [
                {{"idioma": "...", "nivel": "..."}}
            ]
        }},
        "formacion": {{
            "educacion": [
                {{"titulo": "...", "institucion": "...", "en_curso": true/false}}
            ],
            "certificaciones": [...]
        }},
        "experiencia": {{
            "experiencias": [
                {{
                    "empresa": "...",
                    "puesto": "...",
                    "fecha_inicio": "YYYY-MM-DD o null si no se encuentra",
                    "fecha_fin": "YYYY-MM-DD o null para trabajos actuales",
                    "descripcion": "INCLUIR todas las herramientas, metodologías, tecnologías o competencias mencionadas en la descripción",
                    "duracion": "X años Y meses o período aproximado",
                    "actual": true/false
                }}
            ],
            "proyectos_destacados": [
                {{
                    "nombre": "...",
                    "descripcion": "...",
                    "tecnologias": ["extraer", "todas", "las", "herramientas", "metodologías", "o", "competencias", "mencionadas"]
                }}
            ]
        }},
        "insights": {{
            "fortalezas": [
                "SOLO mencionar fortalezas basadas en información REAL del CV"
            ],
            "areas_mejora": [...],
            "industrias_relacionadas": ["Basadas en la experiencia real del candidato"]
        }},
        "evaluacion": {{
            "overall_score": ...,
            "calidad_cv": "...",
            "comentarios": "..."
        }},
        "embedding_optimizado": {{
        
        "texto_embedding": "Genera un resumen profesional optimizado para motores de búsqueda semántica, basado únicamente en la información contenida en el CV. El texto debe ser claro, completo y sin omitir ningún detalle, incluso si parece menor o secundario. Incluir de forma concisa y precisa:

            1) Formación académica: carrera actual (con semestre, institución y situación actual) y estudios previos (bachilleratos, técnicos, etc. con institución y fechas si están).
            2) Experiencia laboral: listar empresas, cargos, períodos, tareas realizadas y herramientas/metodologías utilizadas en cada experiencia.
            3) Proyectos personales o freelance: si están mencionados, incluir nombre, herramientas/metodologías y objetivos.
            4) Competencias profesionales: herramientas de software, metodologías, certificaciones, lenguajes de programación, plataformas, sistemas, según el área profesional.
            5) Habilidades blandas: incluir solo las explícitamente mencionadas en el CV (ej: liderazgo, resolución de conflictos, trabajo en equipo, etc.).
            6) Idiomas: mencionar todos los idiomas presentes en el CV con el nivel de dominio indicado (ej: nativo, intermedio, alto).
            7) Otra información relevante: participación en concursos, ferias, certificaciones, áreas de especialización técnica o académica, etc.
            8) Informacion personal como ubicacion, numero de telefono, etc.

    ⚠️ No inventar, no asumir, no generalizar. Incluir solo información explícita en el CV. El objetivo es que este texto represente de forma precisa y completa el perfil profesional"
        }}
        }}

        REGLAS CRÍTICAS:
        1. Responde SOLO con el JSON, sin texto adicional
        2. NO uses ```json ni markdown
        3. Reemplaza todos los [placeholders] con información real del CV
        4. Si no encuentras información, usa "" para strings y [] para arrays
        5. Para seniority usa: Junior (0-2 años), Semi-Senior (2-5 años), Senior (5+ años)
        6. Extrae TODAS las herramientas, metodologías, software y competencias mencionadas según el área profesional
        7. ⚠️ CRÍTICO: NO inventes ni supongas habilidades que no estén explícitamente mencionadas en el CV
        8. ⚠️ CRÍTICO: NO menciones tecnologías avanzadas (ML, IA, LLM) a menos que estén EXPLÍCITAMENTE en el CV
        9. ⚠️ CRÍTICO: Las fortalezas deben basarse ÚNICAMENTE en información real del CV
        10. ⚠️ CRÍTICO: El texto de embedding debe incluir SOLO información verificable del CV
        11. ⚠️ CRÍTICO: Las habilidades técnicas incluyen cualquier competencia profesional específica del área (no solo programación)

        JSON RESPONSE:

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
                    "num_ctx": 8192,
                    "num_predict": 4096,
                    "repeat_penalty": 1.1,  
                    "stop": ["Human:", "Assistant:"]
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
        try:
            print(f"[INFO] Guardando CV con lógica corregida: {analysis.nombre}")

            industria = self.determine_main_industry(analysis)
            rol = self.get_or_create_role(analysis.rol_sugerido)
            puesto = self.get_or_create_seniority_level(analysis.seniority, analysis.anos_experiencia)

            cv = CV(
                filename=filename,
                contenido=analysis.embedding_text or "Contenido procesado con Ollama",
                nombre_completo=analysis.nombre if analysis.nombre != "N/A" else None,
                email=analysis.email if analysis.email and analysis.email != "N/A" else None,
                telefono=analysis.telefono if analysis.telefono and analysis.telefono not in ["N/A", "No disponible"] else None,
                ubicacion=None,
                linkedin_url=analysis.linkedin if analysis.linkedin and analysis.linkedin != "N/A" else None,
                github_url=analysis.github if analysis.github and analysis.github != "N/A" else None,
                portafolio_url=analysis.portafolio if analysis.portafolio and analysis.portafolio != "N/A" else None,
                id_rol=rol.id if rol else None,
                id_puesto=puesto.id if puesto else None,
                id_industria=industria.id if industria else None,
                overall_score=analysis.overall_score,
                anhos_experiencia=analysis.anos_experiencia,
                processed_status="completed"
            )

            self.session.add(cv)
            self.session.flush()

            for exp in analysis.experiencias:
                if isinstance(exp, dict):
                    exp_industria = self.determine_company_industry(exp.get('empresa', ''), exp.get('descripcion', ''))
                    experiencia = Experiencia(
                        id_cv=cv.id,
                        empresa=exp.get('empresa', 'N/A'),
                        posicion=exp.get('puesto', 'N/A'),
                        descripcion=exp.get('descripcion', None),
                        fecha_inicio=exp.get('fecha_inicio'),
                        fecha_fin=exp.get('fecha_fin'),
                        id_industria=exp_industria.id if exp_industria else industria.id,
                        es_actual=exp.get('actual', False)
                    )
                    self.session.add(experiencia)

            def safe_habilidad_nombre(nombre):
                return nombre[:100] if nombre and len(nombre) > 100 else nombre

            for habilidad_nombre in analysis.habilidades_tecnicas:
                if habilidad_nombre.lower() not in ['n/a', '']:
                    nombre_seguro = safe_habilidad_nombre(habilidad_nombre)
                    habilidad = self.get_or_create_skill(nombre_seguro, industria)
                    if habilidad and habilidad not in cv.habilidades:
                        cv.habilidades.append(habilidad)

            for idioma_info in analysis.idiomas:
                if isinstance(idioma_info, dict) and 'idioma' in idioma_info:
                    idioma_nombre = idioma_info['idioma']
                else:
                    idioma_nombre = str(idioma_info)

                if idioma_nombre.lower() not in ['n/a', 'español', 'spanish']:
                    idioma = self.get_or_create_language(idioma_nombre)
                    if idioma and idioma not in cv.lenguajes:
                        cv.lenguajes.append(idioma)

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

            for proyecto in analysis.proyectos_destacados:
                if isinstance(proyecto, dict):
                    proyecto_obj = Proyecto(
                        id_cv=cv.id,
                        nombre=proyecto.get('nombre', 'Proyecto'),
                        descripcion=proyecto.get('descripcion', ''),
                        tecnologias_usadas=', '.join(proyecto.get('tecnologias', []))
                    )
                    self.session.add(proyecto_obj)

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

    def determine_company_industry(self, empresa_nombre, descripcion=""):
        """
        Determina la industria específica de una empresa
        Versión expandida para todos los sectores
        """
        texto = f"{empresa_nombre} {descripcion}".lower()
        
        # Empresas específicas conocidas (expandido)
        known_companies = {
            # Tecnología
            'google': 'Tecnología', 'microsoft': 'Tecnología', 'amazon': 'Tecnología',
            'meta': 'Tecnología', 'facebook': 'Tecnología', 'netflix': 'Tecnología',
            'uber': 'Tecnología', 'airbnb': 'Tecnología', 'merit': 'Tecnología',
            'oracle': 'Tecnología', 'salesforce': 'Tecnología', 'ibm': 'Tecnología',
            
            # Salud
            'hospital': 'Salud', 'clínica': 'Salud', 'sanatorio': 'Salud',
            'pfizer': 'Salud', 'johnson': 'Salud', 'roche': 'Salud',
            
            # Finanzas
            'banco': 'Finanzas', 'itaú': 'Finanzas', 'santander': 'Finanzas',
            'bbva': 'Finanzas', 'continental': 'Finanzas', 'hsbc': 'Finanzas',
            
            # Educación
            'universidad': 'Educación', 'uca': 'Educación', 'uct': 'Educación',
            'uninorte': 'Educación', 'colegio': 'Educación',
            
            # Retail
            'walmart': 'Retail', 'carrefour': 'Retail', 'stock': 'Retail',
            'superseis': 'Retail', 'biggie': 'Retail',
            
            # Telecomunicaciones
            'tigo': 'Telecomunicaciones', 'personal': 'Telecomunicaciones',
            'claro': 'Telecomunicaciones', 'copaco': 'Telecomunicaciones',
            
            # Agropecuario
            'cargill': 'Agropecuario', 'adr': 'Agropecuario', 'agrotec': 'Agropecuario',
            
            # Construcción
            'constructora': 'Construcción', 'inmobiliaria': 'Construcción'
        }
        
        for company, industry in known_companies.items():
            if company in texto:
                return self.get_or_create_industry(industry)
        
        # Palabras clave por industria (expandido)
        industry_keywords = {
            'Tecnología': ['software', 'desarrollo', 'programación', 'sistemas', 'it', 'tech', 'digital', 'app', 'web'],
            
            'Salud': ['salud', 'médico', 'hospital', 'clínica', 'farmacia', 'medicina', 'enfermería', 'odontología', 'psicología'],
            
            'Finanzas': ['banco', 'financiero', 'seguros', 'inversión', 'crédito', 'fintech', 'contabilidad', 'auditoría'],
            
            'Educación': ['educación', 'universidad', 'colegio', 'instituto', 'enseñanza', 'académico', 'capacitación', 'curso'],
            
            'Manufactura': ['manufactura', 'fábrica', 'producción', 'industrial', 'planta', 'operaciones', 'lean', 'calidad'],
            
            'Retail': ['retail', 'ventas', 'comercio', 'tienda', 'supermercado', 'comercial', 'customer', 'cliente'],
            
            'Servicios': ['consultoría', 'servicios', 'asesoría', 'consultores', 'gestión', 'administración'],
            
            'Marketing': ['marketing', 'publicidad', 'comunicación', 'branding', 'social media', 'seo', 'sem', 'campaña'],
            
            'Recursos Humanos': ['recursos humanos', 'rrhh', 'reclutamiento', 'talento', 'personal', 'hr'],
            
            'Legal': ['legal', 'abogado', 'derecho', 'jurídico', 'compliance', 'contratos', 'litigation'],
            
            'Ingeniería': ['ingeniería', 'ingeniero', 'civil', 'mecánica', 'eléctrica', 'química', 'proyecto'],
            
            'Arquitectura': ['arquitectura', 'arquitecto', 'diseño arquitectónico', 'planos', 'construcción'],
            
            'Construcción': ['construcción', 'obra', 'inmobiliario', 'contractor', 'builder'],
            
            'Diseño': ['diseño', 'gráfico', 'creativo', 'arte', 'multimedia', 'ux', 'ui', 'visual'],
            
            'Logística': ['logística', 'transporte', 'supply chain', 'almacén', 'distribución', 'warehouse'],
            
            'Agropecuario': ['agro', 'agronomía', 'veterinaria', 'ganadería', 'agricultura', 'campo', 'rural'],
            
            'Turismo': ['turismo', 'hotel', 'hotelería', 'gastronomía', 'restaurante', 'travel', 'hospitality'],
            
            'Energía': ['energía', 'petróleo', 'gas', 'electricidad', 'utilities', 'power', 'oil'],
            
            'Telecomunicaciones': ['telecomunicaciones', 'telecom', 'comunicaciones', 'telefónica', 'móvil']
        }
        
        for industry, keywords in industry_keywords.items():
            for keyword in keywords:
                if keyword in texto:
                    return self.get_or_create_industry(industry)
        
        # Si no se puede determinar, retornar None para usar la industria principal
        return None

    def get_or_create_skill(self, nombre: str, industria=None):
        """Obtener o crear habilidad (expandido para todas las competencias profesionales)"""
        habilidad = self.session.query(Habilidad).filter(
            Habilidad.nombre.ilike(f"%{nombre}%")
        ).first()
        
        if not habilidad:
            # Determinar categoría basada en el tipo de habilidad y industria
            categoria_nombre = self._determine_skill_category(nombre, industria)
            
            categoria = self.session.query(CategoriaHabilidad).filter(
                CategoriaHabilidad.nombre == categoria_nombre
            ).first()
            
            if not categoria:
                categoria = CategoriaHabilidad(
                    nombre=categoria_nombre,
                    descripcion=f"Habilidades de {categoria_nombre.lower()}"
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


    def _determine_skill_category(self, skill_name: str, industria=None):
        """Determina la categoría de una habilidad basada en su nombre e industria"""
        skill_lower = skill_name.lower()
        
        # Categorías técnicas por industria
        technical_keywords = {
            'Programación': ['python', 'java', 'javascript', 'c#', 'php', 'ruby', 'go', 'swift', 'kotlin'],
            'Frameworks': ['react', 'angular', 'vue', 'django', 'spring', 'laravel', 'express', 'flask'],
            'Bases de Datos': ['mysql', 'postgresql', 'mongodb', 'oracle', 'sql server', 'redis', 'cassandra'],
            'Cloud y DevOps': ['aws', 'azure', 'google cloud', 'docker', 'kubernetes', 'jenkins', 'terraform'],
            'Marketing Digital': ['google ads', 'facebook ads', 'seo', 'sem', 'google analytics', 'mailchimp'],
            'CRM y Ventas': ['salesforce', 'hubspot', 'pipedrive', 'zoho', 'dynamics'],
            'Finanzas': ['sap', 'erp', 'excel avanzado', 'power bi', 'tableau', 'quickbooks', 'tango'],
            'Diseño': ['photoshop', 'illustrator', 'figma', 'sketch', 'indesign', 'autocad', 'solidworks'],
            'Salud': ['his', 'emr', 'pacs', 'epic', 'meditech'],
            'Legal': ['lexisnexis', 'westlaw', 'thomson reuters'],
            'Recursos Humanos': ['workday', 'bamboohr', 'sap successfactors', 'adp'],
            'Operaciones': ['lean', 'six sigma', 'kaizen', 'wms', 'mes'],
            'Agropecuario': ['gis', 'precision agriculture', 'farm management'],
            'Office Suite': ['microsoft office', 'excel', 'word', 'powerpoint', 'google workspace', 'sheets'],
            'Gestión de Proyectos': ['pmp', 'scrum', 'agile', 'kanban', 'jira', 'trello', 'asana'],
            'Idiomas': ['inglés', 'portugués', 'alemán', 'francés', 'italiano', 'chino', 'japonés'],
            'Certificaciones': ['certified', 'certification', 'certificado', 'certificación'],
            'Metodologías': ['agile', 'scrum', 'kanban', 'waterfall', 'lean', 'six sigma', 'itil']
        }
        
        # Buscar categoría específica
        for category, keywords in technical_keywords.items():
            for keyword in keywords:
                if keyword in skill_lower:
                    return category
        
        # Categorías por industria si no hay match específico
        industry_categories = {
            'Tecnología': 'Técnica',
            'Marketing': 'Marketing Digital',
            'Finanzas': 'Finanzas',
            'Salud': 'Salud',
            'Legal': 'Legal',
            'Diseño': 'Diseño',
            'Recursos Humanos': 'Recursos Humanos',
            'Agropecuario': 'Agropecuario'
        }
        
        if industria and industria.nombre in industry_categories:
            return industry_categories[industria.nombre]
        
        # Determinar si es soft skill
        soft_skills = [
            'liderazgo', 'comunicación', 'trabajo en equipo', 'resolución de problemas',
            'pensamiento crítico', 'creatividad', 'adaptabilidad', 'gestión del tiempo',
            'negociación', 'presentaciones', 'atención al cliente', 'organización'
        ]
        
        for soft_skill in soft_skills:
            if soft_skill in skill_lower:
                return 'Soft Skills'
        
        # Por defecto
        return 'Técnica' 

    def determine_main_industry(self, analysis):
        """
        Determina la industria principal basada en el sector mencionado y experiencias
        Versión mejorada para todos los campos profesionales
        """
        # Mapeo expandido de términos a industrias
        industry_mapping = {
            # Tecnología
            'tecnología': 'Tecnología',
            'software': 'Tecnología', 
            'informática': 'Tecnología',
            'it': 'Tecnología',
            'desarrollo': 'Tecnología',
            'programación': 'Tecnología',
            'sistemas': 'Tecnología',
            
            # Salud
            'salud': 'Salud',
            'medicina': 'Salud',
            'médico': 'Salud',
            'hospital': 'Salud',
            'clínica': 'Salud',
            'enfermería': 'Salud',
            'farmacia': 'Salud',
            'psicología': 'Salud',
            'odontología': 'Salud',
            'fisioterapia': 'Salud',
            
            # Finanzas
            'finanzas': 'Finanzas',
            'banco': 'Finanzas',
            'financiero': 'Finanzas',
            'contabilidad': 'Finanzas',
            'auditoría': 'Finanzas',
            'seguros': 'Finanzas',
            'inversiones': 'Finanzas',
            'tesorería': 'Finanzas',
            
            # Educación
            'educación': 'Educación',
            'universidad': 'Educación',
            'enseñanza': 'Educación',
            'docencia': 'Educación',
            'colegio': 'Educación',
            'instituto': 'Educación',
            'capacitación': 'Educación',
            'académico': 'Educación',
            
            # Manufactura e Industria
            'manufactura': 'Manufactura',
            'producción': 'Manufactura',
            'fábrica': 'Manufactura',
            'industrial': 'Manufactura',
            'planta': 'Manufactura',
            'operaciones': 'Manufactura',
            
            # Marketing y Publicidad
            'marketing': 'Marketing',
            'publicidad': 'Marketing',
            'comunicación': 'Marketing',
            'branding': 'Marketing',
            'digital': 'Marketing',
            'social media': 'Marketing',
            
            # Ventas y Retail
            'ventas': 'Retail',
            'retail': 'Retail',
            'comercio': 'Retail',
            'tienda': 'Retail',
            'supermercado': 'Retail',
            'comercial': 'Retail',
            
            # Consultoría y Servicios
            'consultoría': 'Servicios',
            'servicios': 'Servicios',
            'asesoría': 'Servicios',
            'consultores': 'Servicios',
            
            # Recursos Humanos
            'recursos humanos': 'Recursos Humanos',
            'rrhh': 'Recursos Humanos',
            'reclutamiento': 'Recursos Humanos',
            'talento': 'Recursos Humanos',
            'personal': 'Recursos Humanos',
            
            # Legal
            'legal': 'Legal',
            'abogado': 'Legal',
            'derecho': 'Legal',
            'jurídico': 'Legal',
            'compliance': 'Legal',
            
            # Ingeniería
            'ingeniería': 'Ingeniería',
            'ingeniero': 'Ingeniería',
            'civil': 'Ingeniería',
            'mecánica': 'Ingeniería',
            'eléctrica': 'Ingeniería',
            'química': 'Ingeniería',
            
            # Arquitectura y Construcción
            'arquitectura': 'Arquitectura',
            'construcción': 'Construcción',
            'obra': 'Construcción',
            'inmobiliario': 'Construcción',
            
            # Diseño y Creatividad
            'diseño': 'Diseño',
            'gráfico': 'Diseño',
            'creativo': 'Diseño',
            'arte': 'Diseño',
            'multimedia': 'Diseño',
            
            # Logística y Transporte
            'logística': 'Logística',
            'transporte': 'Logística',
            'supply chain': 'Logística',
            'almacén': 'Logística',
            'distribución': 'Logística',
            
            # Agro y Veterinaria
            'agro': 'Agropecuario',
            'agronomía': 'Agropecuario',
            'veterinaria': 'Agropecuario',
            'ganadería': 'Agropecuario',
            'agricultura': 'Agropecuario',
            
            # Turismo y Hotelería
            'turismo': 'Turismo',
            'hotel': 'Turismo',
            'hotelería': 'Turismo',
            'gastronomía': 'Turismo',
            'restaurante': 'Turismo',
            
            # Energía y Utilities
            'energía': 'Energía',
            'petróleo': 'Energía',
            'gas': 'Energía',
            'electricidad': 'Energía',
            'utilities': 'Energía',
            
            # Telecomunicaciones
            'telecomunicaciones': 'Telecomunicaciones',
            'telecom': 'Telecomunicaciones',
            'comunicaciones': 'Telecomunicaciones'
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
                puesto = exp.get('puesto', '').lower()
                descripcion = exp.get('descripcion', '').lower()
                texto_completo = f"{empresa} {puesto} {descripcion}"
                
                for key, industry in industry_mapping.items():
                    if key in texto_completo:
                        industry_votes[industry] = industry_votes.get(industry, 0) + 1
        
        # Usar la industria con más votos
        if industry_votes:
            main_industry = max(industry_votes, key=industry_votes.get)
            return self.get_or_create_industry(main_industry)
        
        # Por defecto, usar "General"
        return self.get_or_create_industry("General")
    
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
        """Obtener o crear rol (expandido para todas las profesiones)"""
        if not rol_nombre or rol_nombre.lower() in ['n/a', '']:
            return None
            
        rol = self.session.query(Rol).filter(
            Rol.nombre.ilike(f"%{rol_nombre}%")
        ).first()
        
        if not rol:
            # Mapeo expandido de roles por industria
            role_mapping = {
                # Tecnología
                'pasante': 'Pasante', 'intern': 'Pasante', 'trainee': 'Trainee',
                'desarrollador backend': 'Desarrollador Backend', 'backend developer': 'Desarrollador Backend',
                'desarrollador frontend': 'Desarrollador Frontend', 'frontend developer': 'Desarrollador Frontend',
                'full stack': 'Desarrollador Full Stack', 'fullstack': 'Desarrollador Full Stack',
                'analista': 'Analista de Sistemas', 'systems analyst': 'Analista de Sistemas',
                'qa': 'QA Tester', 'tester': 'QA Tester', 'quality assurance': 'QA Tester',
                'devops': 'DevOps Engineer', 'sysadmin': 'Administrador de Sistemas',
                'data analyst': 'Data Analyst', 'data scientist': 'Data Scientist',
                'project manager': 'Project Manager', 'product manager': 'Product Manager',
                
                # Marketing y Ventas
                'marketing digital': 'Marketing Digital', 'digital marketing': 'Marketing Digital',
                'community manager': 'Community Manager', 'social media': 'Social Media Manager',
                'seo specialist': 'SEO Specialist', 'sem specialist': 'SEM Specialist',
                'vendedor': 'Representante de Ventas', 'sales rep': 'Representante de Ventas',
                'account manager': 'Account Manager', 'business development': 'Business Development',
                'brand manager': 'Brand Manager', 'marketing manager': 'Marketing Manager',
                
                # Finanzas y Contabilidad
                'contador': 'Contador', 'accountant': 'Contador',
                'analista financiero': 'Analista Financiero', 'financial analyst': 'Analista Financiero',
                'auditor': 'Auditor', 'tesorero': 'Tesorero', 'treasurer': 'Tesorero',
                'controller': 'Controller Financiero', 'credit analyst': 'Analista de Crédito',
                
                # Recursos Humanos
                'reclutador': 'Especialista en Reclutamiento', 'recruiter': 'Especialista en Reclutamiento',
                'hr generalist': 'Generalista de RRHH', 'hr specialist': 'Especialista de RRHH',
                'compensation analyst': 'Analista de Compensaciones',
                'training coordinator': 'Coordinador de Capacitación',
                
                # Operaciones y Logística
                'operations manager': 'Gerente de Operaciones', 'supply chain': 'Supply Chain Analyst',
                'warehouse manager': 'Gerente de Almacén', 'logistics coordinator': 'Coordinador Logístico',
                'production manager': 'Gerente de Producción', 'quality manager': 'Gerente de Calidad',
                
                # Salud
                'médico': 'Médico', 'doctor': 'Médico', 'enfermero': 'Enfermero', 'nurse': 'Enfermero',
                'psicólogo': 'Psicólogo', 'psychologist': 'Psicólogo',
                'farmacéutico': 'Farmacéutico', 'pharmacist': 'Farmacéutico',
                'fisioterapeuta': 'Fisioterapeuta', 'therapist': 'Terapeuta',
                'odontólogo': 'Odontólogo', 'dentist': 'Odontólogo',
                
                # Legal
                'abogado': 'Abogado', 'lawyer': 'Abogado', 'attorney': 'Abogado',
                'paralegal': 'Paralegal', 'legal assistant': 'Asistente Legal',
                'compliance officer': 'Oficial de Cumplimiento',
                
                # Educación
                'profesor': 'Profesor', 'teacher': 'Profesor', 'docente': 'Docente',
                'instructor': 'Instructor', 'coordinator': 'Coordinador Académico',
                'director académico': 'Director Académico', 'academic director': 'Director Académico',
                
                # Ingeniería
                'ingeniero civil': 'Ingeniero Civil', 'civil engineer': 'Ingeniero Civil',
                'ingeniero industrial': 'Ingeniero Industrial', 'industrial engineer': 'Ingeniero Industrial',
                'ingeniero mecánico': 'Ingeniero Mecánico', 'mechanical engineer': 'Ingeniero Mecánico',
                'ingeniero eléctrico': 'Ingeniero Eléctrico', 'electrical engineer': 'Ingeniero Eléctrico',
                'ingeniero químico': 'Ingeniero Químico', 'chemical engineer': 'Ingeniero Químico',
                
                # Arquitectura y Construcción
                'arquitecto': 'Arquitecto', 'architect': 'Arquitecto',
                'project manager construcción': 'Project Manager - Construcción',
                'supervisor de obra': 'Supervisor de Obra', 'construction supervisor': 'Supervisor de Obra',
                'maestro mayor de obras': 'Maestro Mayor de Obras',
                
                # Diseño y Creatividad
                'diseñador gráfico': 'Diseñador Gráfico', 'graphic designer': 'Diseñador Gráfico',
                'diseñador ux': 'Diseñador UX', 'ux designer': 'Diseñador UX',
                'diseñador ui': 'Diseñador UI', 'ui designer': 'Diseñador UI',
                'director de arte': 'Director de Arte', 'art director': 'Director de Arte',
                'fotógrafo': 'Fotógrafo', 'photographer': 'Fotógrafo',
                
                # Agropecuario
                'ingeniero agrónomo': 'Ingeniero Agrónomo', 'agronomist': 'Ingeniero Agrónomo',
                'veterinario': 'Veterinario', 'veterinarian': 'Veterinario',
                'técnico agropecuario': 'Técnico Agropecuario',
                
                # Turismo y Hotelería
                'chef': 'Chef', 'cook': 'Cocinero',
                'gerente de hotel': 'Gerente Hotelero', 'hotel manager': 'Gerente Hotelero',
                'recepcionista': 'Recepcionista', 'receptionist': 'Recepcionista',
                'guía turístico': 'Guía Turístico', 'tour guide': 'Guía Turístico',
                
                # Roles Generales
                'gerente': 'Gerente', 'manager': 'Gerente',
                'supervisor': 'Supervisor', 'coordinator': 'Coordinador',
                'assistant': 'Asistente', 'asistente': 'Asistente',
                'specialist': 'Especialista', 'especialista': 'Especialista',
                'consultor': 'Consultor', 'consultant': 'Consultor',
                'director': 'Director', 'jefe': 'Jefe de Área'
            }
            
            # Buscar mapeo exacto primero
            rol_lower = rol_nombre.lower().strip()
            if rol_lower in role_mapping:
                rol_normalizado = role_mapping[rol_lower]
            else:
                # Buscar coincidencias parciales
                rol_normalizado = None
                for key, value in role_mapping.items():
                    if key in rol_lower or rol_lower in key:
                        rol_normalizado = value
                        break
                
                # Si no hay coincidencia, usar el título original formateado
                if not rol_normalizado:
                    rol_normalizado = rol_nombre.title()
            
            rol = Rol(
                nombre=rol_normalizado,
                descripcion=f"Rol de {rol_normalizado.lower()}"
            )
            self.session.add(rol)
            self.session.flush()
            
        return rol


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
        nombre_normalizado, iso_code = language_mapping.get(
            nombre_lower, (nombre.title(), nombre.lower()[:2])
        )

        # Buscar por nombre o iso_code exactamente
        idioma = self.session.query(Lenguaje).filter(
            (Lenguaje.nombre.ilike(nombre_normalizado)) |
            (Lenguaje.iso_code == iso_code)
        ).first()

        # Crear si no existe
        if not idioma:
            idioma = Lenguaje(
                nombre=nombre_normalizado,
                iso_code=iso_code
            )
            self.session.add(idioma)
            self.session.flush()  # Asegura que tenga un ID generado
        
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
    """
    Embedding SÚPER optimizado que prioriza experiencia laboral actual y tecnologías
    """
    embedding_parts = []
    
    # 1. INFORMACIÓN BÁSICA
    if analysis.nombre:
        embedding_parts.append(f"Candidato: {analysis.nombre}")
    
    # 2. ROL Y SENIORITY (MÁXIMA PRIORIDAD)
    if analysis.rol_sugerido:
        embedding_parts.append(f"Rol principal: {analysis.rol_sugerido}")
        embedding_parts.append(f"Perfil: {analysis.rol_sugerido}")  # Duplicar para mayor peso
    
    if analysis.seniority:
        embedding_parts.append(f"Nivel de experiencia: {analysis.seniority}")
        
    if analysis.anos_experiencia > 0:
        embedding_parts.append(f"Años de experiencia: {analysis.anos_experiencia}")
    
    # 3. HABILIDADES TÉCNICAS (MÁXIMA PRIORIDAD - TRIPLICAR PESO)
    if analysis.habilidades_tecnicas:
        # Agregar 3 veces las skills para mayor peso en búsqueda
        skills_text = " ".join(analysis.habilidades_tecnicas)
        embedding_parts.append(f"Tecnologías dominadas: {skills_text}")
        embedding_parts.append(f"Habilidades técnicas: {skills_text}")
        embedding_parts.append(f"Stack tecnológico: {skills_text}")
        
        # Skills individuales para matching exacto
        for skill in analysis.habilidades_tecnicas:
            embedding_parts.append(f"Tecnología: {skill}")
            
        # Categorizar skills para mejor búsqueda
        ml_skills = [s for s in analysis.habilidades_tecnicas if any(ml_term in s.lower() for ml_term in ['machine learning', 'ml', 'langchain', 'llm', 'ai', 'tensorflow', 'pytorch'])]
        if ml_skills:
            embedding_parts.append(f"Especialista en Machine Learning e IA: {' '.join(ml_skills)}")
            embedding_parts.append("Perfil Data Science y Machine Learning")
            
        backend_skills = [s for s in analysis.habilidades_tecnicas if any(be_term in s.lower() for be_term in ['python', 'java', 'sql', 'aws', 'oracle', 'spring', 'node', 'php'])]
        if backend_skills:
            embedding_parts.append(f"Desarrollador Backend: {' '.join(backend_skills)}")
            
        frontend_skills = [s for s in analysis.habilidades_tecnicas if any(fe_term in s.lower() for fe_term in ['react', 'angular', 'javascript', 'html', 'css', 'vue'])]
        if frontend_skills:
            embedding_parts.append(f"Desarrollador Frontend: {' '.join(frontend_skills)}")
    
    # 4. EXPERIENCIA LABORAL ACTUAL (PRIORIDAD ALTA)
    if analysis.experiencias:
        # Priorizar experiencia actual
        for i, exp in enumerate(analysis.experiencias, 1):
            if isinstance(exp, dict):
                empresa = exp.get('empresa', '')
                puesto = exp.get('puesto', '')
                descripcion = exp.get('descripcion', '')
                actual = exp.get('actual', False)
                
                exp_text = f"Trabajo {'actual' if actual else f'anterior {i}'}: {puesto} en {empresa}"
                if descripcion:
                    exp_text += f". Responsabilidades: {descripcion}"
                
                embedding_parts.append(exp_text)
                
                # Si es trabajo actual, darle más peso
                if actual:
                    embedding_parts.append(f"Posición actual: {puesto} - {descripcion}")
                    embedding_parts.append(f"Empresa actual: {empresa}")
    
    # 5. PROYECTOS CON TECNOLOGÍAS (ALTA PRIORIDAD)
    if analysis.proyectos_destacados:
        for proyecto in analysis.proyectos_destacados:
            if isinstance(proyecto, dict):
                nombre = proyecto.get('nombre', '')
                desc = proyecto.get('descripcion', '')
                techs = proyecto.get('tecnologias', [])
                
                proyecto_text = f"Proyecto desarrollado: {nombre}"
                if desc:
                    proyecto_text += f". Descripción: {desc}"
                if techs:
                    proyecto_text += f". Tecnologías utilizadas: {', '.join(techs)}"
                    # Agregar techs individuales
                    for tech in techs:
                        embedding_parts.append(f"Experiencia práctica en: {tech}")
                
                embedding_parts.append(proyecto_text)
    
    # 6. FORMACIÓN TÉCNICA RELEVANTE
    if analysis.educacion:
        for edu in analysis.educacion:
            if isinstance(edu, dict):
                titulo = edu.get('titulo', '')
                institucion = edu.get('institucion', '')
                if titulo and ('técnico' in titulo.lower() or 'ingeniería' in titulo.lower() or 'informática' in titulo.lower()):
                    embedding_parts.append(f"Formación técnica: {titulo} - {institucion}")
    
    # 7. ESPECIALIDADES Y SECTORES
    especialidades = []
    if analysis.habilidades_tecnicas:
        for skill in analysis.habilidades_tecnicas:
            skill_lower = skill.lower()
            if 'electrónica' in skill_lower or 'industrial' in skill_lower:
                especialidades.append('Electrónica Industrial')
            if 'machine learning' in skill_lower or 'ml' in skill_lower:
                especialidades.append('Machine Learning')
            if 'langchain' in skill_lower or 'llm' in skill_lower:
                especialidades.append('Inteligencia Artificial')
            if 'aws' in skill_lower:
                especialidades.append('Cloud Computing')
            if 'oracle' in skill_lower:
                especialidades.append('Bases de Datos Enterprise')
    
    if especialidades:
        embedding_parts.append(f"Especialidades técnicas: {', '.join(set(especialidades))}")
    
    # 8. KEYWORDS EXPANDIDOS PARA MATCHING
    keywords = set()
    if analysis.habilidades_tecnicas:
        for skill in analysis.habilidades_tecnicas:
            skill_lower = skill.lower()
            
            # ML/IA keywords
            if any(ml_term in skill_lower for ml_term in ['machine learning', 'ml', 'langchain', 'llm']):
                keywords.update(['machine learning', 'ml', 'ai', 'artificial intelligence', 'data science', 'deep learning', 'llm', 'langchain', 'nlp'])
            
            # Backend keywords  
            if 'python' in skill_lower:
                keywords.update(['python', 'backend', 'data science', 'ml', 'django', 'flask'])
            if 'java' in skill_lower:
                keywords.update(['java', 'backend', 'spring', 'enterprise', 'jvm'])
            if 'aws' in skill_lower:
                keywords.update(['aws', 'cloud', 'amazon', 'devops', 'serverless'])
            if 'oracle' in skill_lower:
                keywords.update(['oracle', 'database', 'sql', 'enterprise', 'apex'])
            
            # Frontend keywords
            if 'react' in skill_lower:
                keywords.update(['react', 'frontend', 'javascript', 'jsx', 'ui'])
            if 'angular' in skill_lower:
                keywords.update(['angular', 'frontend', 'typescript', 'spa'])
            
            # Especialidades
            if 'electrónica' in skill_lower:
                keywords.update(['electronica', 'industrial', 'tecnico', 'hardware', 'sistemas'])
    
    if keywords:
        embedding_parts.append(f"Términos de búsqueda: {' '.join(keywords)}")
    
    # 9. RESUMEN PROFESIONAL EXPANDIDO
    if analysis.resumen_profesional:
        embedding_parts.append(f"Perfil profesional: {analysis.resumen_profesional}")
    
    # 10. SECTORES E INDUSTRIAS
    if analysis.sector:
        embedding_parts.append(f"Sector principal: {analysis.sector}")
    
    if analysis.industrias_relacionadas:
        embedding_parts.append(f"Industrias objetivo: {', '.join(analysis.industrias_relacionadas)}")
    
    # 11. FORTALEZAS CLAVE
    if analysis.fortalezas:
        embedding_parts.append(f"Puntos fuertes: {', '.join(analysis.fortalezas)}")
    
    # Combinar todo y optimizar longitud
    full_text = "\n".join(embedding_parts)
    
    # Asegurar que las tecnologías más importantes estén al principio
    priority_text = ""
    if analysis.habilidades_tecnicas:
        priority_text = f"PERFIL TÉCNICO: {analysis.rol_sugerido or 'Desarrollador'} con {analysis.anos_experiencia} años de experiencia. "
        priority_text += f"TECNOLOGÍAS PRINCIPALES: {', '.join(analysis.habilidades_tecnicas[:10])}. "
    
    final_text = priority_text + full_text
    
    # Limitar longitud manteniendo lo más importante
    if len(final_text) > 2500:
        final_text = final_text[:2500] + "..."
    
    return final_text

