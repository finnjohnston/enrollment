from .requirement import Requirement
import redis
from config.config import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD
from core.exceptions import InvalidRequirementError, EnrollmentError

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, password=REDIS_PASSWORD)

def _req_cache_key(prefix, req_id, completed_courses):
    completed = ','.join(sorted([c.get_course_code() for c in completed_courses]))
    return f"{prefix}:{req_id}|completed:{completed}"

def invalidate_requirement_cache():
    for pattern in ["req_credits:*", "req_completed:*"]:
        keys = redis_client.keys(pattern)
        if isinstance(keys, (list, tuple, set)) and keys:
            redis_client.delete(*keys)

class CourseOptionsRequirement(Requirement):
    """
    A list of course options where a student picks one or more.
    """

    def __init__(self, options, min_required = 1, restrictions=None):
        super().__init__(restrictions=restrictions)
        if not isinstance(options, list) or not all(isinstance(o, str) and o.strip() for o in options):
            raise InvalidRequirementError("options must be a list of non-empty strings")
        if not isinstance(min_required, int) or min_required < 1:
            raise InvalidRequirementError("min_required must be a positive integer")
        self.options = options
        self.min_required = min_required

    def describe(self):
        return f"Choose at least {self.min_required} from {', '.join(self.options)}"
    
    def satisfied_credits(self, completed_courses):
        key = _req_cache_key('req_credits', ','.join(sorted(self.options)), completed_courses)
        cached = redis_client.get(key)
        if isinstance(cached, bytes):
            try:
                return int(cached.decode())
            except EnrollmentError:
                invalidate_requirement_cache()
        matching = [
            (course, course.get_credit_hours())
            for course in completed_courses
            if course.get_course_code() in self.options
        ]
        result = sum(ch for c, ch in matching)
        redis_client.set(key, result)
        invalidate_requirement_cache()
        return result

    def get_completed_courses(self, completed_courses):
        key = _req_cache_key('req_completed', ','.join(sorted(self.options)), completed_courses)
        cached = redis_client.get(key)
        if isinstance(cached, bytes):
            import pickle
            try:
                return pickle.loads(cached)
            except EnrollmentError:
                invalidate_requirement_cache()
        result = [course for course in completed_courses if course.get_course_code() in self.options]
        import pickle
        redis_client.set(key, pickle.dumps(result))
        invalidate_requirement_cache()
        return result

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