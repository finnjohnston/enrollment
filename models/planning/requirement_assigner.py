from typing import Dict, List, Tuple, Optional
from models.courses.course import Course
from models.requirements.requirement_types.requirement import Requirement
from models.requirements.program import Program
from models.requirements.policy_engine import PolicyEngine


class RequirementAssigner:
    """
    Manages assignment of courses to specific requirement categories.
    Allows manual assignment of courses to requirements with validation.
    Now supports assigning a course to multiple categories, but only if those categories are from different programs.
    """
    
    def __init__(self, programs: List[Program], policy_engine: Optional[PolicyEngine] = None):
        self.programs = programs
        # assignments: Dict[course_code, List[Tuple[program_name, category_name]]]
        self.assignments: Dict[str, List[Tuple[str, str]]] = {}
        self.policy_engine = policy_engine or PolicyEngine()
    
    def assign_course_to_requirement(self, course: Course, category_name: str) -> bool:
        course_code = course.get_course_code()
        if not course_code:
            print(f"Cannot assign course - no course code available")
            return False
        
        # Find which program this category belongs to
        program_name = None
        target_program = None
        for program in self.programs:
            for category in program.categories:
                if category.category == category_name:
                    program_name = program.name
                    target_program = program
                    break
            if program_name:
                break
        
        if not program_name or not target_program:
            print(f"Cannot assign {course_code} to '{category_name}' - category not found in any program")
            return False
        
        # Check if already assigned to this program
        existing_assignments = self.assignments.get(course_code, [])
        for assigned_program, _ in existing_assignments:
            if assigned_program == program_name:
                print(f"Cannot assign {course_code} to {category_name} - already assigned to a category in {program_name}")
                return False
        
        # Validate assignment
        if not self._validate_assignment(course, category_name):
            print(f"Cannot assign {course_code} to {category_name} - course does not satisfy any requirement in this category")
            return False
        
        # Validate against overlap policies BEFORE assigning
        if not self._validate_overlap_policies(course, target_program):
            print(f"Cannot assign {course_code} to {category_name} - violates overlap policy")
            return False
        
        # Assign only if validation passes
        self.assignments.setdefault(course_code, []).append((program_name, category_name))
        return True

    def get_assignment_summary(self) -> Dict[str, List[Tuple[str, str]]]:
        # Returns {course_code: [(program_name, category_name), ...]}
        return self.assignments
    
    def validate_plan(self):
        """Validate the entire plan against all applicable overlap policies."""
        return self.policy_engine.validate_plan(self.programs, self.assignments)

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
    
    def _validate_overlap_policies(self, course: Course, target_program: Program) -> bool:
        """Validate course assignment against overlap policies in real-time."""
        # Check if this course is already assigned to other programs
        course_code = course.get_course_code()
        if not course_code:
            return True  # Can't validate if no course code
        
        existing_assignments = self.assignments.get(course_code, [])
        
        for assigned_program_name, _ in existing_assignments:
            # Find the assigned program
            assigned_program = None
            for program in self.programs:
                if program.name == assigned_program_name:
                    assigned_program = program
                    break
            
            if assigned_program and assigned_program != target_program:
                # Check if there's a policy for these two programs
                validation_result = self.policy_engine.validate_plan([target_program, assigned_program], self.assignments)
                if not validation_result['is_valid']:
                    return False
        
        return True
    
    def __repr__(self):
        return f"<RequirementAssigner assignments={sum(len(v) for v in self.assignments.values())}>" 