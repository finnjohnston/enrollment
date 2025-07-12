from typing import List, Optional, Union, cast
from .requirement import Requirement
from models.courses.course import Course

class CourseFilterRequirement(Requirement):
    """
    Requirement defined by course attributes (not explicit codes)
    """

    def __init__(self, subject: Optional[str] = None, tags: Optional[Union[List[str], str]] = None, 
                 min_level: Optional[int] = None, max_level: Optional[int] = None, 
                 min_credits: Optional[int] = None, note: Optional[str] = None, restrictions=None):
        super().__init__(restrictions=restrictions)
        self.subject = subject
        # Handle both string and list inputs for tags
        if isinstance(tags, str):
            self.tags = [tags]
        else:
            self.tags = tags if tags is not None else []
        self.min_level = min_level
        self.max_level = max_level
        self.min_credits = min_credits
        self.note = note
    
    def describe(self) -> str:
        parts = []
        if self.tags:
            parts.append("tagged with any of: " + ", ".join(f"'{tag}'" for tag in self.tags))
        if self.subject:
            parts.append(f"subject '{self.subject}'")
        if self.min_level:
            parts.append(f"{self.min_level}-level or higher")
        if self.max_level:
            parts.append(f"up to {self.max_level}-level")
        if self.note:
            parts.append(f"Note: {self.note}")
        return f"Take at least {self.min_credits} credits from courses matching: " + ", ".join(parts)
    
    def satisfied_credits(self, completed_courses: List[Course]) -> int:
        total = 0
        for course in completed_courses:
            try:
                if self.subject and course.subject_code != self.subject:
                    continue
                if self.tags and not any(tag in course.get_axle_requirements() for tag in self.tags):
                    continue

                # Handle course number conversion safely
                if course.course_number is None:
                    continue
                try:
                    course_num = int(course.course_number)
                except (ValueError, TypeError):
                    continue

                if self.min_level and course_num < self.min_level:
                    continue
                if self.max_level and course_num > self.max_level:
                    continue
                total += course.get_credit_hours()
            except Exception as e:
                print(f"Warning: Error processing course {course}: {e}")
                continue
        return total

    def get_completed_courses(self, completed_courses: List[Course]) -> List[Course]:
        """Returns the subset of completed_courses that satisfy this requirement."""
        matching = []
        for course in completed_courses:
            try:
                if self.subject and course.subject_code != self.subject:
                    continue
                if self.tags and not any(tag in course.get_axle_requirements() for tag in self.tags):
                    continue

                # Handle course number conversion safely
                if course.course_number is None:
                    continue
                try:
                    course_num = int(course.course_number)
                except (ValueError, TypeError):
                    continue

                if self.min_level and course_num < self.min_level:
                    continue
                if self.max_level and course_num > self.max_level:
                    continue
                matching.append(course)
            except Exception as e:
                print(f"Warning: Error processing course {course}: {e}")
                continue
        return matching

    def get_possible_courses(self, courses: List[Course]) -> List[Course]:
        """
        Returns all matching courses from the provided list, applying self.restrictions if present.
        """
        filtered = []
        for course in courses:
            try:
                if self.subject and course.subject_code != self.subject:
                    continue
                if self.tags and not any(tag in course.get_axle_requirements() for tag in self.tags):
                    continue
                if course.course_number is None:
                    continue
                # Use course.level for level filtering
                if self.min_level and (course.level is None or course.level < self.min_level):
                    continue
                if self.max_level and (course.level is None or course.level > self.max_level):
                    continue
                filtered.append(course)
            except Exception as e:
                print(f"Warning: Error processing course {course}: {e}")
                continue
        # Apply per-requirement restrictions if present
        if self.restrictions:
            from models.requirements.restrictions.group import RestrictionGroup
            if isinstance(self.restrictions, RestrictionGroup):
                restrictions = list(self.restrictions)
            else:
                restrictions = [self.restrictions]
            for r in restrictions:
                filter_func = getattr(r, 'filter_courses', None)
                if callable(filter_func):
                    filtered = cast(List[Course], filter_func(filtered))
        return filtered