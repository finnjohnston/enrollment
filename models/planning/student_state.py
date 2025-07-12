from typing import List, Optional
from models.courses.course import Course
from models.planning.plan_config import PlanConfig
from models.planning.semester import Semester


class StudentState:
    """
    Manages the current state of a student's academic progress and planning.
    Tracks completed courses, current semester, and enrolled courses for eligibility calculations.
    """
    
    def __init__(self, plan_config: PlanConfig, current_semester: Optional[Semester] = None):
        """
        Initialize student state from PlanConfig and optional current semester.
        
        Args:
            plan_config: Configuration containing completed courses and program info
            current_semester: Current semester being planned (optional)
        """
        self.plan_config = plan_config
        self.completed_courses: List[Course] = list(plan_config.completed_courses)
        self.current_semester = current_semester
        self.enrolled_courses: List[Course] = []
        
    def get_completed_courses(self) -> List[Course]:
        """Get all completed courses (from PlanConfig + previous semesters)."""
        return self.completed_courses.copy()
    
    def get_enrolled_courses(self) -> List[Course]:
        """Get courses currently enrolled/planned for current semester."""
        return self.enrolled_courses.copy()
    
    def get_current_semester(self) -> Optional[Semester]:
        """Get the current semester being planned."""
        return self.current_semester
    
    def set_current_semester(self, semester: Semester):
        """Set the current semester being planned."""
        self.current_semester = semester
        self.enrolled_courses = []
    

    
    def get_eligibility_context(self) -> tuple[List[Course], List[Course]]:
        """
        Get completed and enrolled courses for eligibility calculations.
        
        Returns:
            Tuple of (completed_courses, enrolled_courses) for recommendation functions
        """
        return (self.get_completed_courses(), self.get_enrolled_courses())
    
    def __repr__(self):
        return (f"<StudentState completed={len(self.completed_courses)} "
                f"enrolled={len(self.enrolled_courses)} "
                f"current_semester={self.current_semester}>") 