from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class CV(Base):
    __tablename__ = 'cvs'

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    role = Column(String, nullable=True)
    experience = Column(String, nullable=True)
