from typing import List, Optional
from .restriction import Restriction
from models.courses.course import Course

class ExclusionRestriction(Restriction):
    """
    Excludes courses based on:
        - full course code match
        - specific course numbers
        - number range
        - course level
    Each instance should be used for one exclusion condition only.
    Use RestrictionGroup to compose multiple exclusions.
    """
    
    def __init__(self,excluded_course_codes: Optional[List[str]] = None, excluded_numbers: Optional[List[int]] = None, min_number: Optional[int] = None, max_number: Optional[int] = None, excluded_levels: Optional[List[int]] = None,  subject: Optional[str] = None):
        self.excluded_course_codes = excluded_course_codes or []
        self.excluded_numbers = excluded_numbers or []
        self.min_number = min_number
        self.max_number = max_number
        self.excluded_levels = excluded_levels or []
        self.subject = subject

    def is_satisfied_by(self, courses: List[Course]) -> bool:
        for course in courses:
            if course.get_course_code() in self.excluded_course_codes:
                return False

            if self.subject and course.subject_code != self.subject:
                continue

            # Robustly check course_number exclusions
            course_num = course.course_number
            course_num_int = None
            if course_num is not None:
                try:
                    course_num_int = int(course_num)
                except (ValueError, TypeError):
                    course_num_int = None

            if course_num_int is not None:
                if course_num_int in self.excluded_numbers:
                    return False
                if self.min_number is not None and self.max_number is not None:
                    if self.min_number <= course_num_int <= self.max_number:
                        return False

            if course.level in self.excluded_levels:
                return False

        return True

    def describe(self) -> str:
        parts = []
        if self.excluded_course_codes:
            parts.append(f"excluded course code(s): {', '.join(self.excluded_course_codes)}")
        if self.excluded_numbers:
            parts.append(f"excluded course number(s): {', '.join(map(str, self.excluded_numbers))}")
        if self.min_number is not None and self.max_number is not None:
            range_str = f"{self.min_number}–{self.max_number}"
            parts.append(f"excluded number range: {range_str}")
            if self.subject:
                parts[-1] += f" (subject = {self.subject})"
        if self.excluded_levels:
            parts.append(f"excluded level(s): {', '.join(map(str, self.excluded_levels))}")
            if self.subject:
                parts[-1] += f" (subject = {self.subject})"
        return "Excludes " + "; ".join(parts)

    def filter_courses(self, courses: List[Course]) -> List[Course]:
        """
        Returns a new list of courses with all excluded courses removed.
        """
        filtered = []
        for course in courses:
            # Exclude by full course code
            if course.get_course_code() in self.excluded_course_codes:
                continue

            # Exclude by subject if specified
            if self.subject and course.subject_code != self.subject:
                filtered.append(course)
                continue

            # Exclude by course number
            course_num = course.course_number
            course_num_int = None
            if course_num is not None:
                try:
                    course_num_int = int(course_num)
                except (ValueError, TypeError):
                    course_num_int = None

            if course_num_int is not None:
                if course_num_int in self.excluded_numbers:
                    continue
                if self.min_number is not None and self.max_number is not None:
                    if self.min_number <= course_num_int <= self.max_number:
                        continue

            # Exclude by level
            if course.level in self.excluded_levels:
                continue

            filtered.append(course)
        return filtered