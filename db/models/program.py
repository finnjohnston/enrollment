from sqlalchemy import Column, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship, validates
from .base import Base
from core.exceptions import InvalidProgramError

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

    @validates('name', 'type')
    def validate_non_empty_string(self, key, value):
        if not isinstance(value, str) or not value.strip():
            raise InvalidProgramError(f"{key} must be a non-empty string")
        return value

    @validates('total_credits')
    def validate_total_credits(self, key, value):
        if not isinstance(value, int) or value <= 0:
            raise InvalidProgramError("total_credits must be a positive integer")
        return value

    @validates('school')
    def validate_school(self, key, value):
        if value is not None and (not isinstance(value, str) or not value.strip()):
            raise InvalidProgramError("school must be a non-empty string if provided")
        return value 