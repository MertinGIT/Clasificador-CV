from pydantic import BaseModel
from typing import Optional

# Esquema para recibir datos de un CV cargado
class CVCreate(BaseModel):
    filename: str
    content: str  
    role: Optional[str] = None
    experience: Optional[str] = None

# Esquema para retornar un CV desde la base de datos
class CVOut(BaseModel):
    id: int
    filename: str
    role: Optional[str]
    experience: Optional[str]

    class Config:
        orm_mode = True
