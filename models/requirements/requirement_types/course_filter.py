from typing import List, Optional, Union, cast
from .requirement import Requirement
from models.courses.course import Course
import redis
from config.config import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD
from core.exceptions import InvalidRequirementError, InvalidCreditsError, EnrollmentError

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, password=REDIS_PASSWORD)

def _req_cache_key(prefix, subject, tags, min_level, max_level, min_credits, completed_courses):
    completed = ','.join(sorted([c.get_course_code() for c in completed_courses]))
    tags_str = ','.join(sorted(tags)) if tags else ''
    return f"{prefix}:{subject}|tags:{tags_str}|minlvl:{min_level}|maxlvl:{max_level}|mincred:{min_credits}|completed:{completed}"

def invalidate_requirement_cache():
    for pattern in ["req_credits:*", "req_completed:*"]:
        keys = redis_client.keys(pattern)
        if isinstance(keys, (list, tuple, set)) and keys:
            redis_client.delete(*keys)

class CourseFilterRequirement(Requirement):
    """
    Requirement defined by course attributes (not explicit codes)
    """

    def __init__(self, subject: Optional[str] = None, tags: Optional[Union[List[str], str]] = None, 
                 min_level: Optional[int] = None, max_level: Optional[int] = None, 
                 min_credits: Optional[int] = None, note: Optional[str] = None, restrictions=None):
        super().__init__(restrictions=restrictions)
        if subject is not None and not isinstance(subject, str):
            raise InvalidRequirementError("subject must be a string if provided")
        if isinstance(tags, str):
            tags = [tags]
        if tags is not None and not all(isinstance(tag, str) for tag in tags):
            raise InvalidRequirementError("tags must be a list of strings")
        if min_level is not None and (not isinstance(min_level, int) or min_level < 0):
            raise InvalidCreditsError("min_level must be a non-negative integer")
        if max_level is not None and (not isinstance(max_level, int) or max_level < 0):
            raise InvalidCreditsError("max_level must be a non-negative integer")
        if min_credits is not None and (not isinstance(min_credits, int) or min_credits < 0):
            raise InvalidCreditsError("min_credits must be a non-negative integer")
        self.subject = subject
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
        key = _req_cache_key('req_credits', self.subject, self.tags, self.min_level, self.max_level, self.min_credits, completed_courses)
        cached = redis_client.get(key)
        if isinstance(cached, bytes):
            try:
                return int(cached.decode())
            except EnrollmentError:
                invalidate_requirement_cache()
        total = 0
        for course in completed_courses:
            try:
                if self.subject and course.subject_code != self.subject:
                    continue
                if self.tags and not any(tag in course.get_axle_requirements() for tag in self.tags):
                    continue
                # Use course.level for level filtering
                if self.min_level and (course.level is None or course.level < self.min_level):
                    continue
                if self.max_level and (course.level is None or course.level > self.max_level):
                    continue
                total += course.get_credit_hours()
            except EnrollmentError as e:
                print(f"Warning: Error processing course {course}: {e}")
                continue
        redis_client.set(key, total)
        invalidate_requirement_cache()
        return total

    def get_completed_courses(self, completed_courses: List[Course]) -> List[Course]:
        key = _req_cache_key('req_completed', self.subject, self.tags, self.min_level, self.max_level, self.min_credits, completed_courses)
        cached = redis_client.get(key)
        if isinstance(cached, bytes):
            import pickle
            try:
                return pickle.loads(cached)
            except EnrollmentError:
                invalidate_requirement_cache()
        matching = []
        for course in completed_courses:
            try:
                if self.subject and course.subject_code != self.subject:
                    continue
                if self.tags and not any(tag in course.get_axle_requirements() for tag in self.tags):
                    continue
                # Use course.level for level filtering
                if self.min_level and (course.level is None or course.level < self.min_level):
                    continue
                if self.max_level and (course.level is None or course.level > self.max_level):
                    continue
                matching.append(course)
            except EnrollmentError as e:
                print(f"Warning: Error processing course {course}: {e}")
                continue
        import pickle
        redis_client.set(key, pickle.dumps(matching))
        invalidate_requirement_cache()
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
            except EnrollmentError as e:
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