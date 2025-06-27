from typing import List, Optional, Union
from .course import Course
from .catalog import Catalog
from .filter import Filter

class Query:
    """
    Chains filter operations to enable narrowing of course lists based on criteria.
    """

    def __init__(self, catalog: Catalog):
        self.catalog = catalog
        self.filter = Filter(catalog)
        self.courses: List[Course] = catalog.courses.copy()

    def reset(self) -> 'Query':
        self.courses = self.catalog.courses.copy()
        return self
    
    def by_subject(self, subjects: Union[str, List[str]]) -> 'Query':
        self.courses = self.filter.get_courses_by_subject(subjects, self.courses)
        return self
    
    def by_axle(self, axles: Union[str, List[str]], match_all: bool = False) -> 'Query':
        self.courses = self.filter.get_courses_by_axle(axles, match_all, self.courses)
        return self
    
    def by_level(self, level: int) -> 'Query':
        self.courses = self.filter.get_courses_by_level(level, self.courses)
        return self
    
    def by_level_range(self, min_level: Optional[int] = None, max_level: Optional[int] = None) -> 'Query':
        self.courses = self.filter.get_courses_by_level_range(min_level, max_level, self.courses)
        return self
    
    def by_credits(self, credits: Union[int, List[int]]) -> 'Query':
        self.courses = self.filter.get_courses_by_credits(credits, self.courses)
        return self

    def exclude_numbers(self, numbers: List[str]) -> 'Query':
        self.courses = self.filter.exclude_course_numbers(numbers, self.courses)
        return self

    def results(self) -> List[Course]:
        return self.courses.copy()

    def count(self) -> int:
        return len(self.courses)
    
