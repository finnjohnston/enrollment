from .requirement import Requirement

class CourseOptionsRequirement(Requirement):
    """
    A list of course options where a student picks one or more.
    """

    def __init__(self, options, min_required = 1, restrictions=None):
        super().__init__(restrictions=restrictions)
        self.options = options
        self.min_required = min_required

    def describe(self):
        return f"Choose at least {self.min_required} from {', '.join(self.options)}"
    
    def satisfied_credits(self, completed_courses):
        matching = [
            course.get_credit_hours()
            for course in completed_courses
            if course.get_course_code() in self.options
        ]
        return sum(matching[:self.min_required])

    def get_completed_courses(self, completed_courses):
        """Returns the subset of completed_courses that satisfy this requirement."""
        matching_courses = [course for course in completed_courses if course.get_course_code() in self.options]
        # Return up to min_required courses
        return matching_courses[:self.min_required]

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