from typing import Dict, List, Tuple
from models.courses.course import Course
from models.requirements.requirement_types.requirement import Requirement
from models.requirements.program import Program


class RequirementAssigner:
    """
    Manages assignment of courses to specific requirement categories.
    Allows manual assignment of courses to requirements with validation.
    Now supports assigning a course to multiple categories, but only if those categories are from different programs.
    """
    
    def __init__(self, programs: List[Program]):
        self.programs = programs
        # assignments: Dict[course_code, List[Tuple[program_name, category_name]]]
        self.assignments: Dict[str, List[Tuple[str, str]]] = {}
    
    def assign_course_to_requirement(self, course: Course, category_name: str) -> bool:
        course_code = course.get_course_code()
        if not course_code:
            return False
        # Find which program this category belongs to
        program_name = None
        for program in self.programs:
            for category in program.categories:
                if category.category == category_name:
                    program_name = program.name
                    break
            if program_name:
                break
        if not program_name:
            return False  # Category not found in any program
        # Check if already assigned to this program
        existing_assignments = self.assignments.get(course_code, [])
        for assigned_program, _ in existing_assignments:
            if assigned_program == program_name:
                return False  # Already assigned to a category in this program
        # Validate assignment
        if not self._validate_assignment(course, category_name):
            return False
        # Assign
        self.assignments.setdefault(course_code, []).append((program_name, category_name))
        return True

    def get_assignment_summary(self) -> Dict[str, List[Tuple[str, str]]]:
        # Returns {course_code: [(program_name, category_name), ...]}
        return self.assignments

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
        return f"<RequirementAssigner assignments={sum(len(v) for v in self.assignments.values())}>" 