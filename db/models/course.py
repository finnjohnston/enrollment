from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import validates
from .base import Base
from core.exceptions import InvalidCourseError, InvalidCreditsError, InvalidLevelError

class Course(Base):
    __tablename__ = 'courses'
    id = Column(Integer, primary_key=True)
    course_code = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    subject_name = Column(String)
    subject_code = Column(String)
    course_number = Column(String)
    level = Column(Integer)
    axle = Column(ARRAY(String))
    credits = Column(Integer)
    prerequisites = Column(JSONB)
    corequisites = Column(JSONB)
    description = Column(Text)

    def __repr__(self):
        return f"<Course(code={self.course_code}, title={self.title})>"

    @validates('course_code', 'title')
    def validate_non_empty_string(self, key, value):
        if not isinstance(value, str) or not value.strip():
            raise InvalidCourseError(f"{key} must be a non-empty string")
        return value

    @validates('credits')
    def validate_credits(self, key, value):
        if value is not None and (not isinstance(value, int) or value < 0):
            raise InvalidCreditsError("credits must be a non-negative integer")
        return value

    @validates('level')
    def validate_level(self, key, value):
        if value is not None and (not isinstance(value, int) or value < 0):
            raise InvalidLevelError("level must be a non-negative integer")
        return value 