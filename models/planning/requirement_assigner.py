from typing import Dict, List
from models.courses.course import Course
from models.requirements.requirement_types.requirement import Requirement
from models.requirements.program import Program


class RequirementAssigner:
    """
    Manages assignment of courses to specific requirement categories.
    Allows manual assignment of courses to requirements with validation.
    """
    
    def __init__(self, programs: List[Program]):
        self.programs = programs
        self.assignments: Dict[str, str] = {}
        

    
    def assign_course_to_requirement(self, course: Course, category_name: str) -> bool:
        course_code = course.get_course_code()
        if not course_code:
            return False
            
        if not self._validate_assignment(course, category_name):
            return False
            
        self.assignments[course_code] = category_name
        return True
    

    
    def get_assignment_summary(self) -> Dict[str, List[str]]:
        summary: Dict[str, List[str]] = {}
        for course_code, category in self.assignments.items():
            if category not in summary:
                summary[category] = []
            summary[category].append(course_code)
        return summary
    

    
    def _course_satisfies_requirement(self, course: Course, requirement: Requirement) -> bool:
        try:
            possible_courses = requirement.get_possible_courses([course])
            return course in possible_courses
        except:
            return False
    
    def _validate_assignment(self, course: Course, category_name: str) -> bool:
        for program in self.programs:
            for category in program.categories:
                if category.category == category_name:
                    for requirement in category.requirements:
                        if self._course_satisfies_requirement(course, requirement):
                            return True
        return False
    
    def __repr__(self):
        return f"<RequirementAssigner assignments={len(self.assignments)}>" 