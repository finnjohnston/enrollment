from .requirement import Requirement

class CourseOptionsRequirement(Requirement):
    """
    A list of course options where a student must earn at least min_credits from the options.
    """

    def __init__(self, options, min_credits=3, restrictions=None):
        super().__init__(restrictions=restrictions)
        self.options = options
        self.min_credits = min_credits

    def describe(self):
        return f"Take at least {self.min_credits} credits from {', '.join(self.options)}"
    
    def satisfied_credits(self, completed_courses):
        matching = [
            course for course in completed_courses
            if course.get_course_code() in self.options
        ]
        return sum(course.get_credit_hours() for course in matching)

    def get_possible_courses(self, courses):
        filtered = [course for course in courses if course.get_course_code() in self.options]
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