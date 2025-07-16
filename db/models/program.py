from sqlalchemy import Column, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from .base import Base

class Program(Base):
    __tablename__ = 'programs'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # 'major' or 'minor'
    total_credits = Column(Integer, nullable=False)
    notes = Column(Text)
    school = Column(String)

    categories = relationship('RequirementCategory', back_populates='program', cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint('name', 'type', name='_program_name_type_uc'),)

    def __repr__(self):
        return f"<Program(name={self.name}, type={self.type})>" 