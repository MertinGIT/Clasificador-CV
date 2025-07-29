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
        """Extrae información de contacto del CV"""
        # Email mejorado
        email_match = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", text)
        
        # Teléfono mejorado (incluye formatos internacionales)
        phone_patterns = [
            r"\+?\d{1,4}[\s\-]?\(?\d{1,4}\)?[\s\-]?\d{1,4}[\s\-]?\d{1,9}",
            r"\(\d{3}\)\s?\d{3}-?\d{4}",
            r"\d{3}-?\d{3}-?\d{4}",
            r"\+\d{1,3}\s\d{1,4}\s\d{1,4}\s\d{1,9}"
        ]
        
        phone_match = None
        for pattern in phone_patterns:
            phone_match = re.search(pattern, text)
            if phone_match:
                break
        
        # LinkedIn mejorado
        linkedin_match = re.search(
            r"(?:https?://)(?:www\.)?linkedin\.com/in/[a-zA-Z0-9\-_]+/?", 
            text, re.IGNORECASE
        )
        
        # GitHub
        github_match = re.search(
            r"(?:https?://)(?:www\.)?github\.com/[a-zA-Z0-9\-_]+/?", 
            text, re.IGNORECASE
        )
        
        # Portafolio/Website
        portfolio_patterns = [
            r"(?:https?://)(?:www\.)?[a-zA-Z0-9\-]+\.(?:com|net|org|io|dev)/?[^\s]*",
            r"(?:portfolio|portafolio|website|sitio web):\s*(https?://[^\s]+)",
        ]
        
        portfolio_match = None
        for pattern in portfolio_patterns:
            portfolio_match = re.search(pattern, text, re.IGNORECASE)
            if portfolio_match and 'linkedin' not in portfolio_match.group().lower() and 'github' not in portfolio_match.group().lower():
                break

        return {
            "email": email_match.group() if email_match else None,
            "telefono": phone_match.group().strip() if phone_match else None,
            "linkedin_url": linkedin_match.group() if linkedin_match else None,
            "github_url": github_match.group() if github_match else None,
            "portafolio_url": portfolio_match.group() if portfolio_match else None,
        }

    def extract_name(self, text: str) -> Optional[str]:
        """Extrae el nombre del candidato (generalmente en las primeras líneas)"""
        lines = text.split('\n')[:5]
        for line in lines:
            line = line.strip()
            # Buscar líneas que parezcan nombres
            if (2 <= len(line.split()) <= 4 and 
                all(word.replace(' ', '').replace('.', '').isalpha() for word in line.split()) and
                5 < len(line) < 50 and
                not any(keyword in line.lower() for keyword in ['cv', 'curriculum', 'resume', 'telefono', 'email'])):
                return line
        return None

    def classify_industry(self, text: str) -> Optional[Industria]:
        """Clasifica la industria basada en palabras clave"""
        text_lower = unidecode(text.lower())
        industrias = self.db.query(Industria).all()
        best_match = None
        max_score = 0

        for industria in industrias:
            # Buscar nombre de industria y palabras relacionadas
            industry_name = unidecode(industria.nombre.lower())
            score = 0
            
            # Coincidencia exacta del nombre
            score += text_lower.count(industry_name) * 10
            
            # Palabras relacionadas según la industria
            if industry_name in ['tecnologia', 'software', 'it']:
                tech_keywords = ['desarrollo', 'programacion', 'software', 'web', 'app', 'sistema', 'tecnologia']
                score += sum(text_lower.count(keyword) for keyword in tech_keywords)
            elif industry_name in ['salud', 'medicina', 'healthcare']:
                health_keywords = ['salud', 'medicina', 'hospital', 'clinica', 'medico', 'enfermeria']
                score += sum(text_lower.count(keyword) for keyword in health_keywords)
            elif industry_name in ['educacion', 'education']:
                edu_keywords = ['educacion', 'universidad', 'colegio', 'profesor', 'maestro', 'docente']
                score += sum(text_lower.count(keyword) for keyword in edu_keywords)
            
            if score > max_score:
                best_match = industria
                max_score = score

        return best_match

    def classify_role(self, text: str) -> Optional[Rol]:
        """Clasifica el rol profesional"""
        text_lower = unidecode(text.lower())
        roles = self.db.query(Rol).all()
        best_match = None
        max_score = 0

        for rol in roles:
            role_name = unidecode(rol.nombre.lower())
            score = text_lower.count(role_name) * 10
            
            # Palabras relacionadas específicas por rol
            if 'desarrollador' in role_name or 'developer' in role_name:
                dev_keywords = ['programacion', 'codigo', 'desarrollo', 'framework', 'api', 'base de datos']
                score += sum(text_lower.count(keyword) for keyword in dev_keywords)
            elif 'analista' in role_name:
                analyst_keywords = ['analisis', 'datos', 'reportes', 'metricas', 'dashboard']
                score += sum(text_lower.count(keyword) for keyword in analyst_keywords)
            
            if score > max_score:
                best_match = rol
                max_score = score

        return best_match

    def classify_seniority(self, text: str, years_experience: int) -> str:
        """Clasifica el nivel de seniority mejorado"""
        text_lower = text.lower()
        
        # Patrones explícitos de seniority
        seniority_patterns = {
            'senior': ['senior', 'sr\.', 'principal', 'lead', 'tech lead', 'arquitecto', 'experto'],
            'semi-senior': ['semi.?senior', 'ssr', 'intermedio', 'mid.?level', 'semi.?experimentado'],
            'junior': ['junior', 'jr\.', 'trainee', 'practicante', 'recien graduado', 'entry.?level'],
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
        """Extrae años de experiencia con patrones mejorados"""
        text_lower = text.lower()
        
        # Patrones para años de experiencia
        experience_patterns = [
            r"(\d+)\s*(?:años?|anhos?|years?)\s*(?:de\s*)?(?:experiencia|experience)",
            r"(?:experiencia|experience)\s*(?:de\s*)?(\d+)\s*(?:años?|anhos?|years?)",
            r"(\d+)\+?\s*(?:años?|anhos?|years?)\s*(?:en|in|of)",
            r"mas de (\d+)\s*(?:años?|anhos?)",
            r"over (\d+)\s*years?",
        ]
        
        for pattern in experience_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                return max(int(match) for match in matches)  # Tomar el mayor si hay múltiples
        
        # Si no encuentra patrones explícitos, calcular por fechas
        current_year = datetime.now().year
        years = re.findall(r'\b(19|20)\d{2}\b', text)
        if years:
            years = [int(year) for year in years if 1990 <= int(year) <= current_year]
            if len(years) >= 2:
                return current_year - min(years)
        
        return 0

    def extract_skills(self, text: str) -> List[Habilidad]:
        """Extrae habilidades con mejor matching"""
        habilidades = self.db.query(Habilidad).all()
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
        """Extrae idiomas con mejor detección"""
        lenguajes = self.db.query(Lenguaje).all()
        found_languages = []
        text_lower = unidecode(text.lower())

        for lenguaje in lenguajes:
            lang_name = unidecode(lenguaje.nombre.lower())
            lang_iso = lenguaje.iso_code.lower()
            
            # Buscar por nombre completo o código ISO
            if (re.search(r'\b' + re.escape(lang_name) + r'\b', text_lower) or
                re.search(r'\b' + re.escape(lang_iso) + r'\b', text_lower)):
                found_languages.append(lenguaje)
        
        return found_languages

    def map_seniority_to_puesto(self, years: int) -> Optional[Puesto]:
        """Mapea años de experiencia a puesto usando el nuevo modelo"""
        return self.db.query(Puesto).filter(
            Puesto.min_anhos <= years,
            (Puesto.max_anhos >= years) | (Puesto.max_anhos.is_(None))
        ).first()

    def score_cv(self, text: str, contact_info: Dict, years: int, 
                habilidades: List, lenguajes: List) -> float:
        """
        Sistema de scoring avanzado y realista para CVs
        Rango: 0-100 puntos
        """
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
            exp_score = 10  # Recién graduado
        elif years <= 2:
            exp_score = 40  # Junior
        elif years <= 5:
            exp_score = 70  # Mid-level
        elif years <= 10:
            exp_score = 90  # Senior
        else:
            exp_score = 100  # Muy senior
        
        total_score += (exp_score / 100) * self.scoring_weights['experience_years'] * 100
        
        # 3. RELEVANCIA DE HABILIDADES (25%)
        skills_score = min(len(habilidades) * 8, 100)  # Máximo 100 puntos
        
        # Bonus por habilidades de alta demanda
        high_demand_skills = ['python', 'javascript', 'react', 'aws', 'docker', 'kubernetes', 
                             'machine learning', 'data science', 'sql', 'postgresql']
        text_lower = text.lower()
        bonus_skills = sum(10 for skill in high_demand_skills if skill in text_lower)
        skills_score = min(skills_score + bonus_skills, 100)
        
        total_score += (skills_score / 100) * self.scoring_weights['skills_relevance'] * 100
        
        # 4. NIVEL EDUCATIVO (15%)
        education_keywords = {
            'doctorado': 100, 'phd': 100, 'doctor': 100,
            'maestria': 85, 'master': 85, 'mba': 85, 'magister': 85,
            'licenciatura': 70, 'ingenieria': 70, 'bachelor': 70,
            'tecnico': 50, 'tecnologico': 50,
            'secundaria': 20, 'bachillerato': 20
        }
        
        education_score = 0
        text_lower = text.lower()
        for keyword, score in education_keywords.items():
            if keyword in text_lower:
                education_score = max(education_score, score)
                break
        
        if education_score == 0:
            education_score = 30  # Score base si no se detecta educación
        
        total_score += (education_score / 100) * self.scoring_weights['education_level'] * 100
        
        # 5. HABILIDADES DE IDIOMA (10%)
        if len(lenguajes) == 0:
            lang_score = 20  # Solo idioma nativo asumido
        elif len(lenguajes) == 1:
            lang_score = 50  # Bilingüe
        elif len(lenguajes) == 2:
            lang_score = 75  # Trilingüe
        else:
            lang_score = 100  # Políglota
        
        total_score += (lang_score / 100) * self.scoring_weights['language_skills'] * 100
        
        # 6. CERTIFICACIONES (10%)
        cert_keywords = ['certificacion', 'certification', 'certified', 'diplomado', 
                        'curso', 'bootcamp', 'nanodegree']
        cert_count = sum(text_lower.count(keyword) for keyword in cert_keywords)
        cert_score = min(cert_count * 25, 100)
        
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
        if 500 <= text_length <= 5000:
            score += 20
        elif text_length < 200:
            score -= 30
        
        # Estructura (presencia de secciones típicas)
        sections = ['experiencia', 'educacion', 'habilidades', 'experience', 'education', 'skills']
        section_count = sum(1 for section in sections if section in text.lower())
        score += min(section_count * 5, 20)
        
        # Presencia de fechas (indica estructura temporal)
        date_patterns = r'\b(19|20)\d{2}\b|\b(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\b'
        date_count = len(re.findall(date_patterns, text.lower()))
        score += min(date_count * 2, 10)
        
        return min(score, 100)

    def save_cv(self, text: str, filename: str) -> CV:
        """Guarda el CV procesado en la base de datos"""
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
        nuevo_cv.habilidades = habilidades
        nuevo_cv.lenguajes = lenguajes

        self.db.add(nuevo_cv)
        self.db.commit()
        self.db.refresh(nuevo_cv)
        return nuevo_cv

    def get_cv_analysis(self, cv_id: int) -> Dict:
        """Obtiene análisis detallado de un CV"""
        cv = self.db.query(CV).filter(CV.id == cv_id).first()
        if not cv:
            return None
        
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
                "habilidades": [h.nombre for h in cv.habilidades],
                "idiomas": [l.nombre for l in cv.lenguajes]
            }
        }