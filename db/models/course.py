from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from .base import Base

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