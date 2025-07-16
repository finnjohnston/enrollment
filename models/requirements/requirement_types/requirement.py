from typing import List, Optional, Union, Any
from models.courses.course import Course

class Requirement:
    """
    Abstract base class for all requirement types.
    """
    
    def __init__(self, restrictions: Optional[object] = None):
        self.restrictions = restrictions
        # Example: if restrictions is not None and not isinstance(restrictions, (RestrictionGroup, ...)):
        #     raise ValueError("restrictions must be a valid restriction group or None")
    
    def describe(self) -> str:
        raise NotImplementedError("Subclasses must implement describe()")
    
    def satisfied_credits(self, completed_courses: List[Course]) -> int:
        raise NotImplementedError("Subclasses must implement satisfied_credits()")
    
    def get_completed_courses(self, completed_courses: List[Course]) -> List[Course]:
        """Returns the subset of completed_courses that satisfy this requirement."""
        raise NotImplementedError("Subclasses must implement get_completed_courses()")
    
    def get_possible_courses(self, courses: List[Course]) -> List[Course]:
        """Returns all courses from the provided list that could satisfy this requirement."""
        raise NotImplementedError("Subclasses must implement get_possible_courses()")