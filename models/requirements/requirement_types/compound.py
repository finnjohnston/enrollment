from models.courses.course import Course
from typing import List, Optional, cast
from .requirement import Requirement
from .course_list import CourseListRequirement
from .course_options import CourseOptionsRequirement
from .course_filter import CourseFilterRequirement

class CompoundRequirement(Requirement):
    """
    Supports OR (default) or AND between groups of courses, depending on 'op'.
    """

    def __init__(self, options: List[Requirement], restrictions=None, op: str = "OR"):
        super().__init__(restrictions=restrictions)
        self.options = options
        self.op = op.upper()  # 'AND' or 'OR'

    def describe(self):
        joiner = "AND" if self.op == "AND" else "OR"
        return f"Choose {'all of' if self.op == 'AND' else 'one of'} the following sequences ({joiner}):\n" + "\n".join(
            f"  - {opt.describe()}" for opt in self.options
        )

    def satisfied_credits(self, completed_courses: List[Course]) -> int:
        if self.op == "AND":
            # Sum credits from all options
            total_credits = 0
            for opt in self.options:
                total_credits += opt.satisfied_credits(completed_courses)
            return total_credits
        else:  # OR logic (default, backward compatible)
            max_credits = 0
            for opt in self.options:
                earned_credits = opt.satisfied_credits(completed_courses)
                max_credits = max(max_credits, earned_credits)
            return max_credits

    def get_completed_courses(self, completed_courses: List[Course]) -> List[Course]:
        if self.op == "AND":
            # Union of all completed courses for all options
            all_courses = []
            seen = set()
            for opt in self.options:
                for course in opt.get_completed_courses(completed_courses):
                    code = course.get_course_code()
                    if code not in seen:
                        all_courses.append(course)
                        seen.add(code)
            return all_courses
        else:  # OR logic (default, backward compatible)
            best_option_courses = []
            max_credits = 0
            for opt in self.options:
                option_courses = opt.get_completed_courses(completed_courses)
                option_credits = sum(course.get_credit_hours() for course in option_courses)
                if option_credits > max_credits:
                    max_credits = option_credits
                    best_option_courses = option_courses
            return best_option_courses

    def get_possible_courses(self, courses: List[Course]) -> List[Course]:
        # Return all courses that could satisfy any option in the compound requirement
        all_codes = set()
        for opt in self.options:
            possible = opt.get_possible_courses(courses)
            all_codes.update([c.get_course_code() for c in possible])
        return [c for c in courses if c.get_course_code() in all_codes]