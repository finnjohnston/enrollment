from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class RequirementCategory(Base):
    __tablename__ = 'requirement_categories'
    id = Column(Integer, primary_key=True)
    program_id = Column(Integer, ForeignKey('programs.id'), nullable=False)
    category = Column(String, nullable=False)
    min_credits = Column(Integer, nullable=False)
    notes = Column(Text)

    program = relationship('Program', back_populates='categories')
    requirements = relationship('Requirement', back_populates='category', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<RequirementCategory(category={self.category}, program_id={self.program_id})>" 