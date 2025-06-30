from models.courses.course import Course
from typing import List, Optional, cast
from .requirement import Requirement
from .course_list import CourseListRequirement
from .course_options import CourseOptionsRequirement
from .course_filter import CourseFilterRequirement

class CompoundRequirement(Requirement):
    """
    Supports OR between groups of courses
    """

    def __init__(self, options: List[Requirement], restrictions=None):
        super().__init__(restrictions=restrictions)
        self.options = options

    def describe(self):
        return "Choose one of the following sequences:\n" + "\n".join(
            f"  - {opt.describe()}" for opt in self.options
        )

    def satisfied_credits(self, completed_courses: List[Course]) -> int:
        max_credits = 0
        for opt in self.options:
            if isinstance(opt, CourseListRequirement):
                earned_credits = sum(
                    course.get_credit_hours()
                    for course in completed_courses
                    if course.get_course_code() in opt.courses
                )
                max_credits = max(max_credits, earned_credits)
            elif isinstance(opt, CourseOptionsRequirement):
                codes = {c.get_course_code() for c in completed_courses}
                matching_courses = [c for c in completed_courses if c.get_course_code() in opt.options]
                if len(matching_courses) >= opt.min_required:
                    earned_credits = opt.satisfied_credits(completed_courses)
                    max_credits = max(max_credits, earned_credits)
            elif isinstance(opt, CourseFilterRequirement):
                earned_credits = opt.satisfied_credits(completed_courses)
                if earned_credits >= (opt.min_credits or 0):
                    max_credits = max(max_credits, earned_credits)
            else:
                earned_credits = opt.satisfied_credits(completed_courses)
                max_credits = max(max_credits, earned_credits)
        return max_credits

    def get_possible_courses(self, courses: List[Course]) -> List[Course]:
        """
        Returns the union of possible courses from all options, deduplicated by course code.
        """
        all_courses = []
        seen_codes = set()
        for opt in self.options:
            if isinstance(opt, (CourseListRequirement, CourseOptionsRequirement, CourseFilterRequirement)):
                opt_courses = opt.get_possible_courses(courses)
            else:
                opt_courses = courses
            # Defensive check and debug print
            if not isinstance(opt_courses, list):
                print(f"Warning: opt_courses is not a list for option {opt}. Value: {opt_courses}")
                opt_courses = []
            for c in opt_courses:
                code = c.get_course_code()
                if code not in seen_codes:
                    all_courses.append(c)
                    seen_codes.add(code)
        # Apply per-requirement restrictions if present
        if self.restrictions:
            from models.requirements.restrictions.group import RestrictionGroup
            if isinstance(self.restrictions, RestrictionGroup):
                restrictions = list(self.restrictions)  # type: ignore
            else:
                restrictions = [self.restrictions]
            for r in restrictions:
                filter_func = getattr(r, 'filter_courses', None)
                if callable(filter_func):
                    all_courses = cast(List[Course], filter_func(all_courses))
        return all_courses