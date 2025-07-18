from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship, validates
from .base import Base
from core.exceptions import InvalidCategoryError, InvalidCreditsError

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

    @validates('category')
    def validate_category(self, key, value):
        if not isinstance(value, str) or not value.strip():
            raise InvalidCategoryError("category must be a non-empty string")
        return value

    @validates('min_credits')
    def validate_min_credits(self, key, value):
        if not isinstance(value, int) or value < 0:
            raise InvalidCreditsError("min_credits must be a non-negative integer")
        return value 