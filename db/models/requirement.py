from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, validates
from .base import Base
from core.exceptions import InvalidRequirementError, InvalidCreditsError

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

    @validates('type')
    def validate_type(self, key, value):
        if not isinstance(value, str) or not value.strip():
            raise InvalidRequirementError("type must be a non-empty string")
        return value

    @validates('data')
    def validate_data(self, key, value):
        if not isinstance(value, dict):
            raise InvalidRequirementError("data must be a dictionary")
        return value

    @validates('min_credits')
    def validate_min_credits(self, key, value):
        if value is not None and (not isinstance(value, int) or value < 0):
            raise InvalidCreditsError("min_credits must be a non-negative integer")
        return value 