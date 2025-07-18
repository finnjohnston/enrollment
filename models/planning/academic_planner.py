from typing import Dict, List, Optional, Any, Tuple
from models.courses.catalog import Catalog
from models.courses.course import Course
from models.requirements.program import Program
from models.graph.dependency_graph import DependencyGraph
from models.planning.plan_config import PlanConfig
from models.planning.semester import Semester
from models.planning.student_state import StudentState
from models.planning.semester_planner import SemesterPlanner
from models.planning.requirement_assigner import RequirementAssigner
from models.requirements.policy_engine import PolicyEngine
from models.requirements.requirement_types.course_list import invalidate_requirement_cache
from models.graph.dependency_graph import invalidate_graph_cache
from core.exceptions import InvalidCourseError, InvalidAssignmentError, InvalidProgramError, InvalidCategoryError


class AcademicPlanner:
    """
    High-level orchestrator for academic planning.
    Manages student state, course assignments, semester progression, and recommendations.
    """
    
    def __init__(self, catalog: Catalog, programs: List[Program], start_semester: Semester, policy_engine: Optional[PolicyEngine] = None):
        """
        Initialize the academic planner with catalog, programs, and starting semester.
        
        Args:
            catalog: Course catalog containing all available courses
            programs: List of degree programs (majors/minors)
            start_semester: Starting semester for planning
            policy_engine: Policy engine for overlap policies (optional)
        """
        self.catalog = catalog
        self.graph = DependencyGraph(catalog)
        self.plan_config = PlanConfig(programs, [], start_semester.season, start_semester.year, 4)
        self.student_state = StudentState(self.plan_config, start_semester)
        self.policy_engine = policy_engine or PolicyEngine()
        self.assigner = RequirementAssigner(programs, self.policy_engine)
        self.planner = SemesterPlanner(catalog, self.graph)
    
    def add_completed_courses(self, course_assignments: Dict[str, List[Tuple[str, str]]]) -> None:
        """
        Add courses to student state and assign them to requirements.
        Args:
            course_assignments: Dict mapping course_code to list of (program_name, category_name) pairs
        """
        for course_code, assignments in course_assignments.items():
            if not isinstance(course_code, str) or not course_code.strip():
                raise InvalidCourseError(f"Invalid course code: {course_code}")
            # Accept both tuples and lists (from JSON) and convert all to tuples
            if not isinstance(assignments, list) or not all((isinstance(a, (list, tuple)) and len(a) == 2) for a in assignments):
                raise InvalidAssignmentError(f"Assignments for {course_code} must be a list of (program_name, category_name) tuples")
            assignments = [tuple(a) for a in assignments]
            course = self.catalog.get_by_course_code(course_code)
            if course:
                if course not in self.student_state.completed_courses:
                    self.student_state.completed_courses.append(course)
                for program_name, category in assignments:
                    if not isinstance(program_name, str) or not program_name.strip():
                        raise InvalidProgramError(f"Invalid program name: {program_name}")
                    if not isinstance(category, str) or not category.strip():
                        raise InvalidCategoryError(f"Invalid category name: {category}")
                    self.assigner.assign_course_to_requirement(course, category)
                    print(f"Added {course_code} for {program_name} - {category}")
            else:
                print(f"Course '{course_code}' not found in catalog")
        print(f"Completed courses: {[c.get_course_code() for c in self.student_state.get_completed_courses()]}")
        print(f"Assignments: {self.assigner.get_assignment_summary()}")
        invalidate_requirement_cache()
        invalidate_graph_cache()
    
    def advance_semester(self) -> None:
        """Move to the next semester."""
        current = self.student_state.get_current_semester()
        if not current:
            print("No current semester to advance from")
            return
        
        if current.season == "Fall":
            next_semester = Semester("Spring", current.year + 1)
        else:
            next_semester = Semester("Fall", current.year)
        
        self.student_state.set_current_semester(next_semester)
        print(f"Advanced to {next_semester.term_id}")
    
    def get_recommendations(self) -> Optional[Dict[str, List]]:
        """
        Get recommendations for the current semester.
        
        Returns:
            Dictionary mapping requirement categories to recommended courses/groups
        """
        current_sem = self.student_state.get_current_semester()
        if not current_sem:
            print("No current semester set")
            return None
        
        print(f"\n=== Recommendations for {current_sem.term_id} ===")
        
        # Get recommendations using SemesterPlanner
        recommendations = self.planner.get_semester_recommendations(
            self.student_state, current_sem, self.assigner.get_assignment_summary()
        )
        
        # Organize recommendations by program
        program_recommendations = {}
        for program in self.plan_config.programs:
            program_recommendations[program.name] = {}
            for category in program.categories:
                category_name = category.category
                if category_name in recommendations:
                    program_recommendations[program.name][category_name] = recommendations[category_name]
        
        # Display recommendations organized by program
        print("\nRecommendations by program:")
        for program_name, program_recs in program_recommendations.items():
            print(f"\n  {program_name}:")
            if not program_recs:
                print("    No recommendations for this program")
            else:
                for category, items in program_recs.items():
                    print(f"    {category}:")
                    
                    # Build the display list
                    display_list = []
                    for item in items:
                        if isinstance(item, list):
                            # This is a corequisite group - add as nested list
                            course_codes = [c.get_course_code() for c in item]
                            display_list.append(course_codes)
                        else:
                            # This is an individual course - add as string
                            display_list.append(item.get_course_code())
                    
                    print(f"      {display_list}")
        
        return recommendations
    
    def get_progress_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the student's progress across all programs.
        
        Returns:
            Dictionary containing progress information
        """
        completed_courses = self.student_state.get_completed_courses()
        progress_summary = {
            "current_semester": self.student_state.get_current_semester(),
            "completed_courses": [c.get_course_code() for c in completed_courses],
            "total_completed_credits": sum(c.get_credit_hours() for c in completed_courses),
            "programs": []
        }
        
        for program in self.plan_config.programs:
            program_progress = program.progress(completed_courses, self.assigner.assignments)
            progress_summary["programs"].append(program_progress)
        
        return progress_summary
    
    def plan_semester(self, chosen_courses: Dict[str, List[Tuple[str, str]]]) -> Dict[str, Any]:
        """
        Plan a specific semester by adding chosen courses with batch validation.
        Args:
            chosen_courses: Dict mapping course_code to list of (program_name, category_name) pairs
        Returns:
            Dictionary with assignment results and validation status
        """
        results = {}
        for course_code, assignments in chosen_courses.items():
            if not isinstance(course_code, str) or not course_code.strip():
                raise InvalidCourseError(f"Invalid course code: {course_code}")
            if not isinstance(assignments, list) or not all(isinstance(a, tuple) and len(a) == 2 for a in assignments):
                raise InvalidAssignmentError(f"Assignments for {course_code} must be a list of (program_name, category_name) tuples")
            course = self.catalog.get_by_course_code(course_code)
            if course:
                if course not in self.student_state.completed_courses:
                    self.student_state.completed_courses.append(course)
                for program_name, category in assignments:
                    if not isinstance(program_name, str) or not program_name.strip():
                        raise InvalidProgramError(f"Invalid program name: {program_name}")
                    if not isinstance(category, str) or not category.strip():
                        raise InvalidCategoryError(f"Invalid category name: {category}")
                    success = self.assigner.assign_course_to_requirement(course, category)
                    results[f"{course_code} -> {program_name} - {category}"] = success
                    if success:
                        print(f"Added {course_code} for {program_name} - {category}")
            else:
                print(f"Course '{course_code}' not found in catalog")
                results[f"{course_code}"] = False
        print(f"Completed courses: {[c.get_course_code() for c in self.student_state.get_completed_courses()]}")
        print(f"Assignments: {self.assigner.get_assignment_summary()}")
        invalidate_requirement_cache()
        invalidate_graph_cache()
        validation_result = self.validate_plan()
        return {
            "assignment_results": results,
            "validation_result": validation_result,
            "plan_valid": validation_result['is_valid']
        }
    
    def get_current_semester(self) -> Optional[Semester]:
        """Get the current semester being planned."""
        return self.student_state.get_current_semester()
    
    def get_completed_courses(self) -> List[Course]:
        """Get all completed courses."""
        return self.student_state.get_completed_courses()
    
    def get_assignments(self) -> Dict[str, List[Tuple[str, str]]]:
        """Get current course-to-requirement assignments."""
        return self.assigner.get_assignment_summary()
    
    def validate_plan(self) -> Dict[str, Any]:
        """Validate the current plan against all applicable overlap policies."""
        return self.assigner.validate_plan()
    
    def __repr__(self):
        current_sem = self.student_state.get_current_semester()
        return (f"<AcademicPlanner current_semester={current_sem} "
                f"completed_courses={len(self.student_state.completed_courses)} "
                f"programs={len(self.plan_config.programs)}>") 