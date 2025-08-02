import re
import math
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from model import CV, Industria, Puesto, Habilidad, Lenguaje, Rol
from unidecode import unidecode
from datetime import datetime


class UniversalCVClassifier:
    def __init__(self, db: Session):
        self.db = db
        
        # Weights para el scoring
        self.scoring_weights = {
            'contact_completeness': 0.15,      # 15% - Info de contacto completa
            'experience_years': 0.20,          # 20% - Años de experiencia
            'skills_relevance': 0.25,          # 25% - Habilidades relevantes
            'education_level': 0.15,           # 15% - Nivel educativo
            'language_skills': 0.10,           # 10% - Idiomas
            'certifications': 0.10,            # 10% - Certificaciones
            'text_quality': 0.05               # 5% - Calidad del texto
        }

    def extract_contact_info(self, text: str) -> Dict[str, Optional[str]]:
        """Extrae información de contacto del CV - MEJORADO"""
        # Normalizar texto para mejor búsqueda
        text_clean = text.replace('\n', ' ').replace('\r', ' ')
        
        # Email mejorado
        email_match = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", text_clean)
        
        # Teléfono mejorado para Paraguay (+595)
        phone_patterns = [
            r"\+?595[\s\-]?\d{9}",  # Paraguay específico
            r"\+?\d{1,4}[\s\-]?\(?\d{1,4}\)?[\s\-]?\d{1,4}[\s\-]?\d{1,9}",
            r"\(\d{3}\)\s?\d{3}-?\d{4}",
            r"\d{3}[\s\-]?\d{3}[\s\-]?\d{3,4}",
            r"09\d{2}[\s\-]?\d{3}[\s\-]?\d{3}",  # Para números como 0992 820 631
        ]
        
        phone_match = None
        for pattern in phone_patterns:
            phone_match = re.search(pattern, text_clean)
            if phone_match:
                break
        
        # LinkedIn y GitHub mejorados
        linkedin_match = re.search(
            r"(?:https?://)?(?:www\.)?linkedin\.com/in/[a-zA-Z0-9\-_]+/?", 
            text_clean, re.IGNORECASE
        )
        
        github_match = re.search(
            r"(?:https?://)?(?:www\.)?github\.com/[a-zA-Z0-9\-_]+/?", 
            text_clean, re.IGNORECASE
        )
        
        # Portafolio/Website mejorado
        portfolio_patterns = [
            r"(?:https?://)?(?:www\.)?[a-zA-Z0-9\-]+\.(?:com|net|org|io|dev|py)/?[^\s]*",
            r"(?:portfolio|portafolio|website|sitio web):\s*(https?://[^\s]+)",
        ]
        
        portfolio_match = None
        for pattern in portfolio_patterns:
            portfolio_match = re.search(pattern, text_clean, re.IGNORECASE)
            if (portfolio_match and 
                'linkedin' not in portfolio_match.group().lower() and 
                'github' not in portfolio_match.group().lower() and
                'gmail' not in portfolio_match.group().lower()):
                break
        else:
            portfolio_match = None

        return {
            "email": email_match.group().strip() if email_match else None,
            "telefono": phone_match.group().strip() if phone_match else None,
            "linkedin_url": linkedin_match.group().strip() if linkedin_match else None,
            "github_url": github_match.group().strip() if github_match else None,
            "portafolio_url": portfolio_match.group().strip() if portfolio_match else None,
        }

    def extract_name(self, text: str) -> Optional[str]:
        """Extrae el nombre del candidato - MEJORADO"""
        lines = text.split('\n')
        
        # Buscar en las primeras 10 líneas
        for i, line in enumerate(lines[:10]):
            line = line.strip()
            
            # Saltar líneas vacías o muy cortas
            if len(line) < 3:
                continue
                
            # Buscar patrones de nombre
            words = line.split()
            if (2 <= len(words) <= 4 and 
                all(word.replace('.', '').replace(',', '').isalpha() for word in words) and
                5 <= len(line) <= 50 and
                not any(keyword in line.lower() for keyword in [
                    'cv', 'curriculum', 'resume', 'telefono', 'email', 'github',
                    'experiencia', 'formacion', 'educacion', 'habilidades',
                    'idiomas', 'contacto', 'perfil', 'estudiante'
                ])):
                
                # Si está en mayúsculas, probablemente sea el nombre
                if line.isupper() or any(word[0].isupper() for word in words):
                    return line.title()  # Capitalizar correctamente
        
        return None

    def classify_industry(self, text: str) -> Optional[Industria]:
        """Clasifica la industria basada en palabras clave - MEJORADO"""
        text_lower = unidecode(text.lower())
        
        try:
            industrias = self.db.query(Industria).all()
        except Exception as e:
            print(f"Error consultando industrias: {e}")
            return None
            
        best_match = None
        max_score = 0

        for industria in industrias:
            industry_name = unidecode(industria.nombre.lower())
            score = 0
            
            # Coincidencia exacta del nombre
            score += text_lower.count(industry_name) * 10
            
            # Palabras relacionadas según la industria
            if any(keyword in industry_name for keyword in ['tecnologia', 'software', 'it', 'informatica']):
                tech_keywords = [
                    'desarrollo', 'programacion', 'software', 'web', 'app', 'sistema', 
                    'tecnologia', 'informatica', 'programador', 'developer', 'python',
                    'java', 'javascript', 'php', 'html', 'css', 'react', 'angular'
                ]
                score += sum(text_lower.count(keyword) for keyword in tech_keywords)
                
            elif any(keyword in industry_name for keyword in ['salud', 'medicina', 'healthcare']):
                health_keywords = ['salud', 'medicina', 'hospital', 'clinica', 'medico', 'enfermeria']
                score += sum(text_lower.count(keyword) for keyword in health_keywords)
                
            elif any(keyword in industry_name for keyword in ['educacion', 'education']):
                edu_keywords = ['educacion', 'universidad', 'colegio', 'profesor', 'maestro', 'docente']
                score += sum(text_lower.count(keyword) for keyword in edu_keywords)
            
            if score > max_score:
                best_match = industria
                max_score = score

        return best_match

    def classify_role(self, text: str) -> Optional[Rol]:
        """Clasifica el rol profesional - MEJORADO"""
        text_lower = unidecode(text.lower())
        
        try:
            roles = self.db.query(Rol).all()
        except Exception as e:
            print(f"Error consultando roles: {e}")
            return None
            
        best_match = None
        max_score = 0

        for rol in roles:
            role_name = unidecode(rol.nombre.lower())
            score = text_lower.count(role_name) * 10
            
            # Palabras relacionadas específicas por rol
            if any(keyword in role_name for keyword in ['desarrollador', 'developer', 'programador']):
                dev_keywords = [
                    'programacion', 'codigo', 'desarrollo', 'framework', 'api', 
                    'base de datos', 'frontend', 'backend', 'fullstack', 'web'
                ]
                score += sum(text_lower.count(keyword) for keyword in dev_keywords)
                
            elif 'analista' in role_name:
                analyst_keywords = ['analisis', 'datos', 'reportes', 'metricas', 'dashboard']
                score += sum(text_lower.count(keyword) for keyword in analyst_keywords)
                
            elif any(keyword in role_name for keyword in ['tecnico', 'soporte']):
                tech_keywords = ['soporte', 'mantenimiento', 'reparacion', 'instalacion']
                score += sum(text_lower.count(keyword) for keyword in tech_keywords)
            
            if score > max_score:
                best_match = rol
                max_score = score

        return best_match

    def classify_seniority(self, text: str, years_experience: int) -> str:
        """Clasifica el nivel de seniority - MEJORADO"""
        text_lower = text.lower()
        
        # Patrones explícitos de seniority
        seniority_patterns = {
            'senior': ['senior', 'sr\.', 'principal', 'lead', 'tech lead', 'arquitecto', 'experto'],
            'semi-senior': ['semi.?senior', 'ssr', 'intermedio', 'mid.?level', 'semi.?experimentado'],
            'junior': ['junior', 'jr\.', 'trainee', 'practicante', 'recien graduado', 'entry.?level', 'estudiante', 'pasante'],
        }
        
        # Buscar patrones explícitos primero
        for nivel, patterns in seniority_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return nivel
        
        # Si no encuentra patrones, usar años de experiencia
        if years_experience >= 5:
            return 'senior'
        elif years_experience >= 2:
            return 'semi-senior'
        else:
            return 'junior'

    def extract_years_experience(self, text: str) -> int:
        """Extrae años de experiencia - MEJORADO"""
        text_lower = text.lower()
        
        # Patrones para años de experiencia
        experience_patterns = [
            r"(\d+)\s*(?:años?|anhos?|years?)\s*(?:de\s*)?(?:experiencia|experience)",
            r"(?:experiencia|experience)\s*(?:de\s*)?(\d+)\s*(?:años?|anhos?|years?)",
            r"(\d+)\+?\s*(?:años?|anhos?|years?)\s*(?:en|in|of)",
            r"mas de (\d+)\s*(?:años?|anhos?)",
            r"over (\d+)\s*years?",
        ]
        
        max_years = 0
        for pattern in experience_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                years_found = max(int(match) for match in matches)
                max_years = max(max_years, years_found)
        
        # Si encuentra años explícitos, devolverlos
        if max_years > 0:
            return max_years
        
        # Si no encuentra patrones explícitos, calcular por fechas
        current_year = datetime.now().year
        years = re.findall(r'\b(19|20)\d{2}\b', text)
        
        if years:
            years = [int(year) for year in years if 1990 <= int(year) <= current_year]
            if len(years) >= 2:
                # Calcular experiencia desde el año más antiguo mencionado
                return current_year - min(years)
        
        # Detectar si es estudiante
        if any(keyword in text_lower for keyword in ['estudiante', 'cursando', 'semestre']):
            return 0
        
        return 0

    def extract_skills(self, text: str) -> List[Habilidad]:
        """Extrae habilidades con mejor matching - MEJORADO"""
        try:
            habilidades = self.db.query(Habilidad).all()
        except Exception as e:
            print(f"Error consultando habilidades: {e}")
            return []
            
        found_skills = []
        text_lower = unidecode(text.lower())

        for habilidad in habilidades:
            skill_name = unidecode(habilidad.nombre.lower())
            
            # Buscar coincidencia exacta o como palabra completa
            if (skill_name in text_lower or 
                re.search(r'\b' + re.escape(skill_name) + r'\b', text_lower)):
                found_skills.append(habilidad)
        
        return found_skills

    def extract_languages(self, text: str) -> List[Lenguaje]:
        """Extrae idiomas con mejor detección - MEJORADO"""
        try:
            lenguajes = self.db.query(Lenguaje).all()
        except Exception as e:
            print(f"Error consultando lenguajes: {e}")
            return []
            
        found_languages = []
        text_lower = unidecode(text.lower())

        # Mapeo de idiomas comunes en español
        language_mapping = {
            'español': ['español', 'spanish', 'castellano'],
            'inglés': ['ingles', 'english', 'inglés'],
            'guaraní': ['guarani', 'guaraní'],
            'portugués': ['portugues', 'portuguese', 'português'],
            'francés': ['frances', 'french', 'français'],
            'alemán': ['aleman', 'german', 'deutsch'],
        }

        for lenguaje in lenguajes:
            lang_name = unidecode(lenguaje.nombre.lower())
            lang_iso = lenguaje.iso_code.lower() if lenguaje.iso_code else ""
            
            # Buscar por nombre completo, código ISO o variantes
            found = False
            if re.search(r'\b' + re.escape(lang_name) + r'\b', text_lower):
                found = True
            elif lang_iso and re.search(r'\b' + re.escape(lang_iso) + r'\b', text_lower):
                found = True
            else:
                # Buscar variantes
                for main_lang, variants in language_mapping.items():
                    if lang_name in variants:
                        for variant in variants:
                            if re.search(r'\b' + variant + r'\b', text_lower):
                                found = True
                                break
                        if found:
                            break
            
            if found:
                found_languages.append(lenguaje)
        
        return found_languages

    def map_seniority_to_puesto(self, years: int) -> Optional[Puesto]:
        """Mapea años de experiencia a puesto usando el nuevo modelo"""
        try:
            return self.db.query(Puesto).filter(
                Puesto.min_anhos <= years,
                (Puesto.max_anhos >= years) | (Puesto.max_anhos.is_(None))
            ).first()
        except Exception as e:
            print(f"Error consultando puestos: {e}")
            return None

    def score_cv(self, text: str, contact_info: Dict, years: int, 
                habilidades: List, lenguajes: List) -> float:
        """Sistema de scoring mejorado"""
        total_score = 0.0
        
        # 1. COMPLETITUD DE INFORMACIÓN DE CONTACTO (15%)
        contact_score = 0
        if contact_info.get('email'): contact_score += 30
        if contact_info.get('telefono'): contact_score += 25
        if contact_info.get('linkedin_url'): contact_score += 25
        if contact_info.get('github_url') or contact_info.get('portafolio_url'): contact_score += 20
        
        total_score += (contact_score / 100) * self.scoring_weights['contact_completeness'] * 100
        
        # 2. AÑOS DE EXPERIENCIA (20%)
        if years == 0:
            exp_score = 20  # Estudiante/Recién graduado
        elif years <= 1:
            exp_score = 40  # Junior
        elif years <= 3:
            exp_score = 60  # Semi-junior
        elif years <= 7:
            exp_score = 85  # Senior
        else:
            exp_score = 100  # Muy senior
        
        total_score += (exp_score / 100) * self.scoring_weights['experience_years'] * 100
        
        # 3. RELEVANCIA DE HABILIDADES (25%)
        skills_score = min(len(habilidades) * 8, 100)
        
        # Bonus por habilidades de alta demanda
        high_demand_skills = [
            'python', 'javascript', 'react', 'aws', 'docker', 'kubernetes', 
            'machine learning', 'data science', 'sql', 'postgresql', 'java',
            'php', 'html', 'css', 'angular', 'node.js', 'springboot'
        ]
        text_lower = text.lower()
        bonus_skills = sum(5 for skill in high_demand_skills if skill in text_lower)
        skills_score = min(skills_score + bonus_skills, 100)
        
        total_score += (skills_score / 100) * self.scoring_weights['skills_relevance'] * 100
        
        # 4. NIVEL EDUCATIVO (15%)
        education_keywords = {
            'doctorado': 100, 'phd': 100, 'doctor': 100,
            'maestria': 85, 'master': 85, 'mba': 85, 'magister': 85,
            'licenciatura': 70, 'ingenieria': 70, 'bachelor': 70, 'ingeniero': 70,
            'tecnico': 50, 'tecnologico': 50, 'bachiller': 45,
            'secundaria': 20, 'bachillerato': 20
        }
        
        education_score = 0
        text_lower = text.lower()
        for keyword, score in education_keywords.items():
            if keyword in text_lower:
                education_score = max(education_score, score)
        
        if education_score == 0:
            education_score = 30  # Score base
        
        total_score += (education_score / 100) * self.scoring_weights['education_level'] * 100
        
        # 5. HABILIDADES DE IDIOMA (10%)
        if len(lenguajes) == 0:
            lang_score = 30  # Solo idioma nativo asumido
        elif len(lenguajes) == 1:
            lang_score = 50
        elif len(lenguajes) == 2:
            lang_score = 75
        else:
            lang_score = 100
        
        total_score += (lang_score / 100) * self.scoring_weights['language_skills'] * 100
        
        # 6. CERTIFICACIONES (10%)
        cert_keywords = [
            'certificacion', 'certification', 'certified', 'diplomado', 
            'curso', 'bootcamp', 'nanodegree', 'pasantia', 'internship'
        ]
        cert_count = sum(text_lower.count(keyword) for keyword in cert_keywords)
        cert_score = min(cert_count * 20, 100)
        
        total_score += (cert_score / 100) * self.scoring_weights['certifications'] * 100
        
        # 7. CALIDAD DEL TEXTO (5%)
        text_quality = self._assess_text_quality(text)
        total_score += (text_quality / 100) * self.scoring_weights['text_quality'] * 100
        
        return round(min(total_score, 100), 2)
    
    def _assess_text_quality(self, text: str) -> float:
        """Evalúa la calidad del texto del CV"""
        score = 50  # Score base
        
        # Longitud apropiada
        text_length = len(text.strip())
        if 300 <= text_length <= 3000:
            score += 20
        elif text_length < 100:
            score -= 30
        
        # Estructura (presencia de secciones típicas)
        sections = [
            'experiencia', 'educacion', 'habilidades', 'experience', 'education', 
            'skills', 'formacion', 'idiomas', 'contacto', 'perfil'
        ]
        section_count = sum(1 for section in sections if section in text.lower())
        score += min(section_count * 3, 20)
        
        # Presencia de fechas (indica estructura temporal)
        date_patterns = r'\b(19|20)\d{2}\b|\b(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\b'
        date_count = len(re.findall(date_patterns, text.lower()))
        score += min(date_count, 10)
        
        return min(score, 100)

    def save_cv(self, text: str, filename: str) -> CV:
        """Guarda el CV procesado en la base de datos - CON MANEJO DE ERRORES"""
        try:
            contact_info = self.extract_contact_info(text)
            name = self.extract_name(text)
            years = self.extract_years_experience(text)
            industria = self.classify_industry(text)
            rol = self.classify_role(text)
            puesto = self.map_seniority_to_puesto(years)
            habilidades = self.extract_skills(text)
            lenguajes = self.extract_languages(text)
            
            # Calcular score
            overall_score = self.score_cv(text, contact_info, years, habilidades, lenguajes)

            nuevo_cv = CV(
                filename=filename,
                contenido=text,
                nombre_completo=name,
                email=contact_info["email"],
                telefono=contact_info["telefono"],
                linkedin_url=contact_info["linkedin_url"],
                github_url=contact_info["github_url"],
                portafolio_url=contact_info["portafolio_url"],
                anhos_experiencia=years,
                overall_score=overall_score,
                id_industria=industria.id if industria else None,
                id_rol=rol.id if rol else None,
                id_puesto=puesto.id if puesto else None,
                processed_status="completed"
            )
            
            # Asociar habilidades e idiomas (relaciones many-to-many)
            if habilidades:
                nuevo_cv.habilidades = habilidades
            if lenguajes:
                nuevo_cv.lenguajes = lenguajes

            self.db.add(nuevo_cv)
            self.db.commit()
            self.db.refresh(nuevo_cv)
            
            print(f"CV procesado exitosamente: {filename}")
            print(f"  - Nombre: {name}")
            print(f"  - Email: {contact_info['email']}")
            print(f"  - Teléfono: {contact_info['telefono']}")
            print(f"  - Años experiencia: {years}")
            print(f"  - Score: {overall_score}")
            print(f"  - Habilidades encontradas: {len(habilidades)}")
            print(f"  - Idiomas encontrados: {len(lenguajes)}")
            
            return nuevo_cv
            
        except Exception as e:
            print(f"Error procesando CV {filename}: {str(e)}")
            self.db.rollback()
            
            # Crear CV con status de error
            cv_error = CV(
                filename=filename,
                contenido=text,
                processed_status="error",
                overall_score=0.0
            )
            
            self.db.add(cv_error)
            self.db.commit()
            self.db.refresh(cv_error)
            
            return cv_error

    def get_cv_analysis(self, cv_id: int) -> Dict:
        """Obtiene análisis detallado de un CV"""
        try:
            cv = self.db.query(CV).filter(CV.id == cv_id).first()
            if not cv:
                return {"error": "CV no encontrado"}
            
            return {
                "cv_info": {
                    "id": cv.id,
                    "filename": cv.filename,
                    "overall_score": cv.overall_score,
                    "processed_status": cv.processed_status
                },
                "personal_info": {
                    "nombre": cv.nombre_completo,
                    "email": cv.email,
                    "telefono": cv.telefono,
                    "linkedin": cv.linkedin_url,
                    "github": cv.github_url,
                    "portafolio": cv.portafolio_url
                },
                "professional_info": {
                    "industria": cv.industria.nombre if cv.industria else None,
                    "rol": cv.rol.nombre if cv.rol else None,
                    "puesto": cv.puesto.nombre if cv.puesto else None,
                    "anhos_experiencia": cv.anhos_experiencia
                },
                "skills_and_languages": {
                    "habilidades": [h.nombre for h in cv.habilidades] if cv.habilidades else [],
                    "idiomas": [l.nombre for l in cv.lenguajes] if cv.lenguajes else []
                }
            }
        except Exception as e:
            return {"error": f"Error obteniendo análisis: {str(e)}"}
        
    def save_cv_from_analysis(self, analysis: 'CVAnalysis', filename: str) -> 'CV':
        """
        Guarda un CV en la base de datos usando el análisis de Ollama
        
        Args:
            analysis: Objeto CVAnalysis de Ollama
            filename: Nombre del archivo
        
        Returns:
            CV: Objeto CV guardado en la base de datos
        """
        try:
            print(f"[INFO] Guardando CV desde análisis de Ollama: {analysis.nombre}")
            
            # Crear o obtener industria
            industria = None
            if analysis.sector and analysis.sector != "General":
                industria = self.db.query(Industria).filter(
                    Industria.nombre.ilike(f"%{analysis.sector}%")
                ).first()
                
                if not industria:
                    industria = Industria(nombre=analysis.sector)
                    self.db.add(industria)
                    self.db.flush()
            
            # Crear o obtener rol
            rol = None
            if analysis.rol_sugerido and analysis.rol_sugerido != "Por definir":
                rol = self.db.query(Rol).filter(
                    Rol.nombre.ilike(f"%{analysis.rol_sugerido}%")
                ).first()
                
                if not rol:
                    rol = Rol(nombre=analysis.rol_sugerido)
                    self.db.add(rol)
                    self.db.flush()
            
            # Crear CV principal
            cv = CV(
                filename=filename,
                nombre_completo=analysis.nombre or "Nombre no detectado",
                email=analysis.email or None,
                telefono=analysis.telefono or None,
                linkedin_url=analysis.linkedin or None,
                github_url=analysis.github or None,
                portafolio_url=analysis.portafolio or None,
                anhos_experiencia=analysis.anos_experiencia,
                overall_score=analysis.overall_score,
                industria=industria,
                rol=rol,
                puesto=rol,  # Usar el mismo rol como puesto por ahora
            )
            
            self.db.add(cv)
            self.db.flush()  # Para obtener el ID
            
            print(f"[INFO] CV creado con ID: {cv.id}")
            
            # Agregar habilidades técnicas
            for skill_name in analysis.habilidades_tecnicas:
                if not skill_name or len(skill_name.strip()) == 0:
                    continue
                    
                skill = self.db.query(Habilidad).filter(
                    Habilidad.nombre.ilike(skill_name.strip())
                ).first()
                
                if not skill:
                    skill = Habilidad(nombre=skill_name.strip())
                    self.db.add(skill)
                    self.db.flush()
                
                if skill not in cv.habilidades:
                    cv.habilidades.append(skill)
            
            print(f"[INFO] Agregadas {len(analysis.habilidades_tecnicas)} habilidades técnicas")
            
            # Agregar idiomas
            for idioma_info in analysis.idiomas:
                if isinstance(idioma_info, dict):
                    idioma_nombre = idioma_info.get("idioma", "").strip()
                    nivel = idioma_info.get("nivel", "").strip()
                else:
                    idioma_nombre = str(idioma_info).strip()
                    nivel = "No especificado"
                
                if not idioma_nombre:
                    continue
                    
                idioma = self.db.query(Lenguaje).filter(
                    Lenguaje.nombre.ilike(idioma_nombre)
                ).first()
                
                if not idioma:
                    idioma = Lenguaje(nombre=idioma_nombre)
                    self.db.add(idioma)
                    self.db.flush()
                
                if idioma not in cv.lenguajes:
                    cv.lenguajes.append(idioma)
            
            print(f"[INFO] Agregados {len(analysis.idiomas)} idiomas")
            
            # Agregar soft skills como habilidades si no existen
            for soft_skill in analysis.soft_skills:
                if not soft_skill or len(soft_skill.strip()) == 0:
                    continue
                    
                skill = self.db.query(Habilidad).filter(
                    Habilidad.nombre.ilike(soft_skill.strip())
                ).first()
                
                if not skill:
                    skill = Habilidad(nombre=soft_skill.strip(), tipo="soft")
                    self.db.add(skill)
                    self.db.flush()
                
                if skill not in cv.habilidades:
                    cv.habilidades.append(skill)
            
            print(f"[INFO] Agregadas {len(analysis.soft_skills)} soft skills")
            
            # Commit final
            self.db.commit()
            self.db.refresh(cv)
            
            print(f"[SUCCESS] CV guardado exitosamente:")
            print(f"  - ID: {cv.id}")
            print(f"  - Nombre: {cv.nombre_completo}")
            print(f"  - Rol: {cv.rol.nombre if cv.rol else 'N/A'}")
            print(f"  - Score: {cv.overall_score}")
            print(f"  - Habilidades totales: {len(cv.habilidades)}")
            print(f"  - Idiomas: {len(cv.lenguajes)}")
            
            return cv
            
        except Exception as e:
            self.db.rollback()
            print(f"[ERROR] Error guardando CV desde análisis: {str(e)}")
            raise Exception(f"Error guardando CV: {str(e)}")

    def get_cv_analysis_enhanced(self, cv_id: int) -> Optional[Dict]:
        """
        Obtiene análisis mejorado de un CV específico combinando datos de DB y ChromaDB
        """
        try:
            cv = self.db.query(CV).filter(CV.id == cv_id).first()
            if not cv:
                return None
            
            # Datos básicos de la base de datos
            basic_analysis = {
                "cv_info": {
                    "id": cv.id,
                    "filename": cv.filename,
                    "created_at": cv.created_at if hasattr(cv, 'created_at') else None
                },
                "personal_info": {
                    "nombre": cv.nombre_completo,
                    "email": cv.email,
                    "telefono": cv.telefono,
                    "linkedin": cv.linkedin_url,
                    "github": cv.github_url,
                    "portafolio": cv.portafolio_url
                },
                "professional_profile": {
                    "industria": cv.industria.nombre if cv.industria else None,
                    "rol": cv.rol.nombre if cv.rol else None,
                    "puesto": cv.puesto.nombre if cv.puesto else None,
                    "experiencia": cv.anhos_experiencia,
                    "score": cv.overall_score
                },
                "skills": {
                    "habilidades": [h.nombre for h in cv.habilidades],
                    "total_habilidades": len(cv.habilidades),
                    "idiomas": [l.nombre for l in cv.lenguajes],
                    "total_idiomas": len(cv.lenguajes)
                }
            }
            
            return basic_analysis
            
        except Exception as e:
            print(f"[ERROR] Error obteniendo análisis de CV {cv_id}: {str(e)}")
            return None
