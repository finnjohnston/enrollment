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
        return self.axle if self.axle else []
    
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