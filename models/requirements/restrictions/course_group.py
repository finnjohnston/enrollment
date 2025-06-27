from typing import List, Optional
from .restriction import Restriction
from models.courses.course import Course

class CourseGroupRestriction(Restriction):
    """
    Enforces a maximum number of credits a student can count from a specific group of courses.
    """

    def __init__(self, courses: List[str], max_credits: int):
        self.courses = courses
        self.max_credits = max_credits

    def is_satisfied_by(self, completed_courses: List[Course]) -> bool:
        total = 0
        for course in completed_courses:
            if course.get_course_code() in self.courses:
                total += course.get_credit_hours()
        return total <= self.max_credits

    def describe(self) -> str:
        return f"No more than {self.max_credits} credits may be counted from: {', '.join(self.courses)}"