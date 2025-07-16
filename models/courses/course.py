from collections import defaultdict
from typing import List, Optional, Dict, Any

class Course:
    """
    Represents a course with all its attributes.
    """

    def __init__(self, course_data: Dict[str, Any]):
        self.subject_name = course_data.get('subject_name')
        self.title = course_data.get('title')

        self.course_code = course_data.get('course_code')
        self.subject_code = course_data.get('subject_code')
        self.course_number = course_data.get('course_number')
        self.level = course_data.get('level')

        self.axle = course_data.get('axle')
        self.credits = course_data.get('credits')

        self.prerequisites = course_data.get('prerequisites')
        self.corequisites = course_data.get('corequisites')
        # Add support for alternate field names
        self.prereqs = course_data.get('prereqs')
        self.coreqs = course_data.get('coreqs')

        self.description = course_data.get('description')

        # Validation
        if not isinstance(self.course_code, str) or not self.course_code.strip():
            raise ValueError("course_code must be a non-empty string")
        if not isinstance(self.title, str) or not self.title.strip():
            raise ValueError("title must be a non-empty string")
        if self.credits is not None and (not isinstance(self.credits, int) or self.credits < 0):
            raise ValueError("credits must be a non-negative integer")
        if self.level is not None and (not isinstance(self.level, int) or self.level < 0):
            raise ValueError("level must be a non-negative integer")

    @classmethod
    def from_orm(cls, orm_course):
        data = {
            'subject_name': orm_course.subject_name,
            'title': orm_course.title,
            'course_code': orm_course.course_code,
            'subject_code': orm_course.subject_code,
            'course_number': orm_course.course_number,
            'level': orm_course.level,
            'axle': orm_course.axle,
            'credits': orm_course.credits,
            'prerequisites': orm_course.prerequisites,
            'corequisites': orm_course.corequisites,
            'description': orm_course.description
        }
        # Validation
        if not isinstance(data['course_code'], str) or not data['course_code'].strip():
            raise ValueError("course_code must be a non-empty string")
        if not isinstance(data['title'], str) or not data['title'].strip():
            raise ValueError("title must be a non-empty string")
        if data['credits'] is not None and (not isinstance(data['credits'], int) or data['credits'] < 0):
            raise ValueError("credits must be a non-negative integer")
        if data['level'] is not None and (not isinstance(data['level'], int) or data['level'] < 0):
            raise ValueError("level must be a non-negative integer")
        return cls(data)

    def __str__(self):
        return f"{self.course_code}: {self.title}"
    
    def __repr__(self):
        return f"Course('{self.course_code}', '{self.title}')"
    
    def get_course_code(self):
        return self.course_code
    
    def get_subject_and_number(self):
        return (self.subject_code, self.course_number)
    
    def has_prerequisites(self):
        return self.prerequisites is not None and len(self.prerequisites) > 0
    
    def has_corequisites(self):
        return self.corequisites is not None and len(self.corequisites) > 0
    
    def get_credit_hours(self):
        try:
            if self.credits is None or self.credits == "None":
                return 0
            return int(self.credits)
        except (ValueError, TypeError):
            return 0
        
    def get_axle_requirements(self):
        if not self.axle:
            return []
        if isinstance(self.axle, list):
            return self.axle
        return [self.axle]
    
    def to_dict(self):
        return {
            'subject_name': self.subject_name,
            'title': self.title,
            'course_code': self.course_code,
            'subject_code': self.subject_code,
            'course_number': self.course_number,
            'level': self.level,
            'axle': self.axle,
            'credits': self.credits,
            'prerequisites': self.prerequisites,
            'corequisites': self.corequisites,
            'description': self.description
        }