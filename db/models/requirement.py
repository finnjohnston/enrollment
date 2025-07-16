from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from .base import Base

class Requirement(Base):
    __tablename__ = 'requirements'
    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey('requirement_categories.id'), nullable=False)
    type = Column(String, nullable=False)  # e.g., 'course_list', 'course_options', etc.
    data = Column(JSONB, nullable=False)   # requirement-specific data
    min_credits = Column(Integer)
    notes = Column(Text)

    category = relationship('RequirementCategory', back_populates='requirements')

    def __repr__(self):
        return f"<Requirement(type={self.type}, category_id={self.category_id})>" 