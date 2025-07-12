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

    def get_completed_courses(self, completed_courses: List[Course]) -> List[Course]:
        """Returns the subset of completed_courses that satisfy this requirement."""
        # For compound requirements, return courses from the option that gives the most credits
        best_option_courses = []
        max_credits = 0
        
        for opt in self.options:
            try:
                option_courses = opt.get_completed_courses(completed_courses)
                option_credits = sum(course.get_credit_hours() for course in option_courses)
                if option_credits > max_credits:
                    max_credits = option_credits
                    best_option_courses = option_courses
            except Exception as e:
                print(f"Warning: Error getting completed courses for compound option {opt}: {e}")
                continue
                
        return best_option_courses

    def get_possible_courses(self, courses: List[Course]) -> List[Course]:
        # Return all courses that could satisfy any option in the compound requirement
        all_codes = set()
        for opt in self.options:
            possible = opt.get_possible_courses(courses)
            all_codes.update([c.get_course_code() for c in possible])
        return [c for c in courses if c.get_course_code() in all_codes]