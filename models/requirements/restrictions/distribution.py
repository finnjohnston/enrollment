from typing import List, Optional
from .restriction import Restriction
from models.courses.course import Course

class DistributionRestriction(Restriction):
    """
    Enforces minimum credits from a specific list of courses.
    """

    def __init__(self, courses: List[str], min_credits: int):
        self.courses = courses
        self.min_credits = min_credits

    def is_satisfied_by(self, courses: List[Course]) -> bool:
        total = 0
        for course in courses:
            if course.get_course_code() in self.courses:
                total += course.get_credit_hours()
        return total >= self.min_credits

    def describe(self) -> str:
        return f"At least {self.min_credits} credits from {', '.join(self.courses)}"

