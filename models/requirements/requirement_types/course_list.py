from .requirement import Requirement

class CourseListRequirement(Requirement):
    """
    A list of fixed required courses.
    """
    def __init__(self, courses, restrictions=None):
        super().__init__(restrictions=restrictions)
        self.courses = courses

    def describe(self):
        return f"Must complete: {', '.join(self.courses)}"
    
    def satisfied_credits(self, completed_courses):
        return sum(
            course.get_credit_hours()
            for course in completed_courses
            if course.get_course_code() in self.courses
        )

    def get_possible_courses(self, courses):
        filtered = [course for course in courses if course.get_course_code() in self.courses]
        if self.restrictions:
            from models.requirements.restrictions.group import RestrictionGroup
            if isinstance(self.restrictions, RestrictionGroup):
                restrictions = self.restrictions.restrictions
            else:
                restrictions = [self.restrictions]
            for r in restrictions:
                filter_func = getattr(r, 'filter_courses', None)
                if callable(filter_func):
                    filtered = filter_func(filtered)
        return filtered