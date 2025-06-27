from typing import List, Optional
from .restriction import Restriction
from models.courses.course import Course

class TagQuotaRestriction(Restriction):
    """
    Requires credits from courses with a specific tag.
    """

    def __init__(self, tag: str, min_credits: int):
        self.tag = tag
        self.min_credits = min_credits

    def is_satisfied_by(self, courses: List[Course]) -> bool:
        total = 0
        for course in courses:
            if self.tag in (course.get_axle_requirements() or []):
                total += course.get_credit_hours()
        return total >= self.min_credits


    def describe(self) -> str:
        return f"At least {self.min_credits} credits with tag '{self.tag}'"
