from typing import List, Optional
from .restriction import Restriction
from models.courses.course import Course

class CreditLimitRestriction(Restriction):
    """
    Limits the number of credits that can come from a specific course.
    """

    def __init__(self, courses: List[str], max_credits: int):
        self.courses = courses
        self.max_credits = max_credits

    def is_satisfied_by(self, courses: List[Course]) -> bool:
        total = 0
        for course in courses:
            if course.get_course_code() in self.courses:
                total += course.get_credit_hours()
        return total <= self.max_credits

    def describe(self) -> str:
        return f"No more than {self.max_credits} credits from: {', '.join(self.courses)}"
