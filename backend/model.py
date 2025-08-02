from sqlalchemy import Column, Integer, String, create_engine, Text, JSON, DateTime, Float, ForeignKey, Table, Boolean, Date
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship
from datetime import datetime


Base = declarative_base()
# ========== relaciones muchos a muchos ==========
cv_habilidades = Table(
    'cv_habilidades', Base.metadata,
    Column('id_cv', Integer, ForeignKey('cvs.id'), primary_key=True),
    Column('id_habilidad', Integer, ForeignKey('habilidades.id'), primary_key=True)
)

cv_lenguajes = Table(
    'cv_lenguajes', Base.metadata,
    Column('id_cv', Integer, ForeignKey('cvs.id'), primary_key=True),
    Column('id_lenguaje', Integer, ForeignKey('lenguajes.id'), primary_key=True)
)

# ========== MODELOS NORMALIZADOS ==========
class Industria(Base):
    """
    Representa el SECTOR de la empresa donde trabaja/trabajó
    Ejemplos: Tecnología, Salud, Finanzas, Educación, etc.
    """
    __tablename__ = "industrias"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), unique=True, index=True, nullable=False)
    descripcion = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class Rol(Base):
    """
    Representa el CARGO/POSICIÓN específica
    Ejemplos: Pasante, Desarrollador Backend, Analista, Gerente, etc.
    UN ROL PUEDE EXISTIR EN MÚLTIPLES INDUSTRIAS
    """
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), unique=True, index=True, nullable=False)  # Hacer único
    descripcion = Column(Text, nullable=True)
    # QUITAR la relación directa con industria - un rol puede estar en cualquier industria
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Rol(id={self.id}, nombre='{self.nombre}')>"




class Puesto(Base):
    """
    Representa el NIVEL de seniority
    Ejemplos: Junior, Semi-Senior, Senior, Lead, etc.
    """
    __tablename__ = "puestos"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), unique=True, nullable=False)
    min_anhos = Column(Integer, nullable=False, default=0)
    max_anhos = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Puesto(id={self.id}, nombre='{self.nombre}', {self.min_anhos}-{self.max_anhos or '+'} años)>"


class CategoriaHabilidad(Base):
    __tablename__ = "categorias_habilidades"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False)
    descripcion = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class Habilidad(Base):
    __tablename__ = "habilidades"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), index=True, nullable=False)
    id_categoria = Column(Integer, ForeignKey('categorias_habilidades.id'), nullable=False)
    # Una habilidad puede ser específica de una industria o general
    id_industria = Column(Integer, ForeignKey('industrias.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    categoria = relationship("CategoriaHabilidad", backref="habilidades")
    industria = relationship("Industria", backref="habilidades_especificas")



class Lenguaje(Base):
    __tablename__ = "lenguajes"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False)
    iso_code = Column(String(5), unique=True, nullable=False)  # ISO code like 'en', 'es', etc.
    created_at = Column(DateTime, default=datetime.utcnow)

class Educacion(Base):
    __tablename__ = "educacion"
    id = Column(Integer, primary_key=True, index=True)
    id_cv = Column(Integer, ForeignKey('cvs.id'), nullable=False)
    grado = Column(String(100), nullable=False)
    campo_estudio = Column(String(100))
    institucion = Column(String(200), nullable=False)
    fecha_inicio = Column(Date)
    fecha_fin = Column(Date, nullable=True)
    esta_cursando = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    cv = relationship("CV", back_populates="educacion")


class Experiencia(Base):
    """
    Cada experiencia tiene:
    - empresa: nombre de la empresa
    - posicion: el ROL que tuvo (ej: "Pasante", "Desarrollador")
    - industria: el SECTOR de esa empresa (ej: "Tecnología", "Salud")
    """
    __tablename__ = "experiencias"
    id = Column(Integer, primary_key=True, index=True)
    id_cv = Column(Integer, ForeignKey('cvs.id'), nullable=False)
    empresa = Column(String(200), nullable=False)
    posicion = Column(String(100), nullable=False)  # Esto es el ROL en esa empresa
    # La industria es específica de esta experiencia/empresa
    id_industria = Column(Integer, ForeignKey('industrias.id'), nullable=True)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=True)
    es_actual = Column(Boolean, default=False)
    descripcion = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    industria = relationship("Industria", backref="experiencias")
    cv = relationship("CV", back_populates="experiencias")

class Proyecto(Base):
    __tablename__ = "proyectos"
    id = Column(Integer, primary_key=True, index=True)
    id_cv = Column(Integer, ForeignKey('cvs.id'), nullable=False)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=False)
    tecnologias_usadas = Column(Text)
    url = Column(String(500), nullable=True)
    fecha_inicio = Column(Date, nullable=True)
    fecha_fin = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    cv = relationship("CV", back_populates="proyectos")


class Certificacion(Base):
    __tablename__ = "certificaciones"
    id = Column(Integer, primary_key=True, index=True)
    id_cv = Column(Integer, ForeignKey('cvs.id'), nullable=False)
    nombre = Column(String(200), nullable=False)
    organizacion = Column(String(200), nullable=False)
    fecha_emision = Column(Date, nullable=True)
    fecha_expiracion = Column(Date, nullable=True)
    id_credencial = Column(String(100), nullable=True)
    url_verificacion = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    cv = relationship("CV", back_populates="certificaciones")



class CV(Base):
    """
    El CV tiene:
    - id_rol: El ROL PRINCIPAL que busca/tiene (ej: "Desarrollador Backend")
    - id_puesto: Su NIVEL de seniority (ej: "Junior", "Senior") 
    - id_industria: La INDUSTRIA donde tiene más experiencia o busca trabajar
    """
    __tablename__ = "cvs"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), index=True, nullable=False)
    contenido = Column(Text, nullable=False)

    # Información personal
    nombre_completo = Column(String(200), nullable=True)
    email = Column(String(100), nullable=True, index=True)
    telefono = Column(String(20), nullable=True)
    ubicacion = Column(String(200), nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    portafolio_url = Column(String(500), nullable=True)
    github_url = Column(String(500), nullable=True)

    # Clasificación PRINCIPAL del candidato
    id_rol = Column(Integer, ForeignKey('roles.id'), nullable=True)           # ROL que busca/tiene
    id_puesto = Column(Integer, ForeignKey('puestos.id'), nullable=True)      # SENIORITY 
    id_industria = Column(Integer, ForeignKey('industrias.id'), nullable=True) # INDUSTRIA objetivo

    # Métricas
    overall_score = Column(Float, default=0.0)
    anhos_experiencia = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_status = Column(String(20), default="pending", nullable=False)  # pending, processing, completed, error

    # Relationships
    rol = relationship("Rol", backref="cvs")
    puesto = relationship("Puesto", backref="cvs")
    industria = relationship("Industria", backref="cvs")
    habilidades = relationship("Habilidad", secondary=cv_habilidades, backref="cvs")
    lenguajes = relationship("Lenguaje", secondary=cv_lenguajes, backref="cvs")
    educacion = relationship("Educacion", back_populates="cv", cascade="all, delete-orphan")
    experiencias = relationship("Experiencia", back_populates="cv", cascade="all, delete-orphan")
    proyectos = relationship("Proyecto", back_populates="cv", cascade="all, delete-orphan")
    certificaciones = relationship("Certificacion", back_populates="cv", cascade="all, delete-orphan")


