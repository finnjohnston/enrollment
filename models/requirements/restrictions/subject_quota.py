from typing import List, Optional
from .restriction import Restriction
from models.courses.course import Course

class SubjectQuotaRestriction(Restriction):
    """
    Enforces minimum or maximum credits from a subject.
    """

    def __init__(self, subject: str, min_credits: Optional[int] = None, max_credits: Optional[int] = None):
        self.subject = subject
        self.min_credits = min_credits
        self.max_credits = max_credits

    def is_satisfied_by(self, courses: List[Course]) -> bool:
        total = 0
        for course in courses:
            if course.subject_code == self.subject:
                total += course.get_credit_hours()
        if self.min_credits is not None and total < self.min_credits:
            return False
        if self.max_credits is not None and total > self.max_credits:
            return False
        return True

    def describe(self) -> str:
        parts = []
        if self.min_credits is not None:
            parts.append(f"at least {self.min_credits}")
        if self.max_credits is not None:
            parts.append(f"no more than {self.max_credits}")
        return f"{' and '.join(parts)} credits in subject '{self.subject}'"
