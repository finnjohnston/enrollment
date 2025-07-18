from typing import List, Optional, Union, Dict, Set
from .course import Course
from .catalog import Catalog
from core.exceptions import InvalidCourseError

class Filter:
    """
    Provides flexible filtering over a catalog of courses.
    """

    def __init__(self, catalog: Catalog):
        self.catalog = catalog

    # === Direct Identifiers ===

    def get_course_by_code(self, code: str) -> Optional[Course]:
        return self.catalog.get_by_course_code(code)
    
    def get_course_by_subject_and_number(self, subject: str, number: str) -> Optional[Course]:
        return self.catalog.get_by_subject_and_number(subject, number)
    
    def get_course_by_title(self, title: str) -> Optional[Course]:
        return self.catalog.get_by_title(title)
    
    # === Basic Filters ===

    def get_courses_by_subject(self, subjects: Union[str, List[str]], courses: Optional[List[Course]] = None) -> List[Course]:
        if courses is None:
            courses = self.catalog.courses
        if isinstance(subjects, str):
            subjects = [subjects]
        return [c for c in courses if c.subject_code in subjects]

    def get_courses_by_axle(self, axles: Union[str, List[str]], match_all: bool = False, courses: Optional[List[Course]] = None) -> List[Course]:
        if courses is None:
            courses = self.catalog.courses
        if isinstance(axles, str):
            axles = [axles]
        if match_all:
            return [c for c in courses if all(ax in (c.axle or []) for ax in axles)]
        else:
            return [c for c in courses if any(ax in (c.axle or []) for ax in axles)]

    def get_courses_by_level(self, level: int, courses: Optional[List[Course]] = None) -> List[Course]:
        if courses is None:
            courses = self.catalog.courses
        return [c for c in courses if c.level == level]

    def get_courses_by_level_range(self, min_level: Optional[int] = None, max_level: Optional[int] = None, courses: Optional[List[Course]] = None) -> List[Course]:
        if courses is None:
            courses = self.catalog.courses
        if min_level is None and max_level is None:
            return []
        result = []
        for course in courses:
            if course.level is None:
                continue
            if (
                (min_level is not None and course.level < min_level)
                or (max_level is not None and course.level > max_level)
            ):
                continue
            result.append(course)
        return result

    def get_courses_by_credits(self,credits: Union[int, List[int]],courses: Optional[List[Course]] = None) -> List[Course]:
        if courses is None:
            courses = self.catalog.courses
        if isinstance(credits, int):
            credits = [credits]

        target = set(credits)
        result = []
        for course in courses:
            credit_raw = course.credits
            if credit_raw is None:
                continue
            try:
                credit_val = int(str(credit_raw).strip())
            except InvalidCourseError:
                continue  # Skip if it can't be cleanly converted to an int
            if credit_val in target:
                result.append(course)
        return result

    def get_courses_with_prereqs(self, courses: Optional[List[Course]] = None) -> List[Course]:
        if courses is None:
            courses = self.catalog.courses
        return [c for c in courses if c.prerequisites and str(c.prerequisites).strip()]

    def get_courses_without_prereqs(self, courses: Optional[List[Course]] = None) -> List[Course]:
        if courses is None:
            courses = self.catalog.courses
        return [c for c in courses if not c.prerequisites or not str(c.prerequisites).strip()]

    def exclude_course_numbers(self, numbers: List[str], courses: Optional[List[Course]] = None) -> List[Course]:
        if courses is None:
            courses = self.catalog.courses
        return [c for c in courses if c.course_number not in numbers]

    # === Utilities ===

    def course_exists(self, subject: Optional[str] = None, number: Optional[str] = None,
                      code: Optional[str] = None, title: Optional[str] = None) -> bool:
        if subject and number:
            return self.get_course_by_subject_and_number(subject, number) is not None
        elif code:
            return self.get_course_by_code(code) is not None
        elif title:
            return self.get_course_by_title(title) is not None
        return False

    def get_subject_stats(self, subject: str) -> Dict[str, Union[int, Dict[int, int]]]:
        courses = self.get_courses_by_subject(subject)
        total = len(courses)
        level_dict: Dict[int, int] = {}
        for c in courses:
            if c.level:
                level_dict[c.level] = level_dict.get(c.level, 0) + 1
        return {
            "total_courses": total,
            "courses_by_level": level_dict
        }