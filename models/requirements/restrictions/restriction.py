from typing import List, Optional
from models.courses.course import Course

class Restriction:
    """
    Abstract base class for all restriction types.
    """
    
    def describe(self) -> str:
        raise NotImplementedError("Subclasses must implement describe()")
    
    def is_satisfied_by(self, completed_courses: List[Course]) -> bool:
        raise NotImplementedError("Subclasses must implement is_satisfied_by()")