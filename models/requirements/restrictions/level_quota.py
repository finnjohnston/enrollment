from typing import List, Optional
from .restriction import Restriction
from models.courses.course import Course

class LevelQuotaRestriction(Restriction):
    """
    Enforces a minimum number of credits from a given course level or above.
    """

    def __init__(self, min_level: int, max_level: int):
        self.min_level = min_level
        self.max_level = max_level

    def is_satisfied_by(self, courses: List[Course]) -> bool:
        total = 0
        for course in courses:
            if course.course_number >= self.min_level:
                total += course.get_credit_hours()
        return total >= self.min_credits
    
    def describe(self) -> str:
        return f"At least {self.min_credits} credits at {self.min_level}-level or higher"
    
    