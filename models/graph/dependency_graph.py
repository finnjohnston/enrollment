from typing import Dict, Set, List, Optional, Tuple, cast
from models.courses.course import Course
from models.requirements.program import Program
from models.requirements.requirement_types.requirement import Requirement
from models.requirements.requirement_types.course_list import CourseListRequirement
from models.requirements.requirement_types.course_options import CourseOptionsRequirement
from models.graph.logic import PrerequisiteLogic, CorequisiteLogic
import redis
from config.config import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD
from core.exceptions import ResourceNotFoundError

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, password=REDIS_PASSWORD)

def _graph_cache_key(course_code, traversal):
    return f"graph:{course_code}|traversal:{traversal}"

def invalidate_graph_cache():
    for pattern in ["graph:*"]:
        keys = redis_client.keys(pattern)
        if isinstance(keys, (list, tuple, set)) and keys:
            redis_client.delete(*keys)

class DependencyGraph:
    """
    Represents the structure of course relationships (prerequisites, corequisites, dependents) for all courses in the catalog.
    Provides fast access to course relationship data for use by other logic modules.
    """
    
    # === INITIALIZATION & CONSTRUCTION ===
    
    def __init__(self, catalog):
        self.nodes: Dict[str, Course] = {}
        self.adjacency: Dict[str, Set[str]] = {}  # course_code -> set of dependent course codes
        self.reverse_adjacency: Dict[str, Set[str]] = {}  # course_code -> set of prerequisite course codes
        self.prereq_logic: Dict[str, PrerequisiteLogic] = {}
        self.coreq_logic: Dict[str, CorequisiteLogic] = {}
        self.catalog = catalog
        self._build_graph(catalog)

    def _extract_requisites(self, course_code):
        """
        For a given course, extract graph-friendly prereq and coreq edge sets.
        Returns a dictionary:
        {
            'prereq_edges': [ [set of course codes] → course_code ],
            'coreq_edges':  [ [set of course codes] → course_code ]
        }
        Each inner list is a set of courses that *together* imply a directed edge toward the course.
        Each course in the inner list is treated as an OR-group within a requirement.
        A full outer list is treated as an AND-path.
        """
        course = self.catalog.get_by_course_code(course_code)
        if not course:
            raise ResourceNotFoundError(f"Course '{course_code}' not found in catalog.")

        def extract_requisites_and_of_ors(reqs):
            if not reqs:
                return []
            if isinstance(reqs, str):
                return [[reqs]]
            if isinstance(reqs, list):
                if all(isinstance(x, str) for x in reqs):
                    return [reqs]
                result = []
                for item in reqs:
                    group = extract_requisites_and_of_ors(item)
                    if len(group) == 1 and isinstance(group[0], list):
                        result.append(group[0])
                    else:
                        result.extend(group)
                return result
            return []

        def pick_first_nonempty(*args):
            for arg in args:
                if arg:
                    return arg
            return None

        raw_prereqs = pick_first_nonempty(getattr(course, 'prereqs', None), getattr(course, 'prerequisites', None))
        raw_coreqs = pick_first_nonempty(getattr(course, 'coreqs', None), getattr(course, 'corequisites', None))

        prereq_edges = extract_requisites_and_of_ors(raw_prereqs)
        coreq_edges = extract_requisites_and_of_ors(raw_coreqs)
        if course_code == 'MATH 2600':
            pass  # Debug print removed
        return {
            'prereq_edges': prereq_edges,
            'coreq_edges': coreq_edges
        }

    def _build_graph(self, catalog):
        for course in catalog.courses:
            code = getattr(course, 'course_code', None)
            if not code or not isinstance(code, str):
                continue 
            self.nodes[code] = course
            self.adjacency[code] = set()
            self.reverse_adjacency[code] = set()

            edges = self._extract_requisites(code)
            prereq_groups = edges.get('prereq_edges', [])
            coreq_groups = edges.get('coreq_edges', [])
            self.prereq_logic[code] = PrerequisiteLogic(prereq_groups)
            self.coreq_logic[code] = CorequisiteLogic(coreq_groups)

            for group in prereq_groups:
                for prereq in group:
                    if prereq and isinstance(prereq, str):
                        self.reverse_adjacency[code].add(prereq)
                        self.adjacency.setdefault(prereq, set()).add(code)

            for group in coreq_groups:
                for coreq in group:
                    if coreq and isinstance(coreq, str):
                        self.adjacency.setdefault(coreq, set()).add(code)

    # === LOGIC INTEGRATION ===
    
    def get_prerequisite_logic(self, course_code: str) -> Optional[PrerequisiteLogic]:
        if not course_code or not isinstance(course_code, str):
            return None
        return self.prereq_logic.get(course_code)
        
    def get_corequisite_logic(self, course_code: str) -> Optional[CorequisiteLogic]:
        if not course_code or not isinstance(course_code, str):
            return None
        return self.coreq_logic.get(course_code)

    # === BASIC NAVIGATION ===
    
    def get_prerequisites(self, course_code: str) -> List[str]:
        key = _graph_cache_key(course_code, 'prerequisites')
        cached = redis_client.get(key)
        if isinstance(cached, bytes):
            import json
            return json.loads(cached.decode())
        if not course_code or not isinstance(course_code, str):
            return []
        result = list(self.reverse_adjacency.get(course_code, set()))
        import json
        redis_client.set(key, json.dumps(result))
        invalidate_graph_cache()
        return result

    def get_corequisites(self, course_code: str) -> List[str]:
        key = _graph_cache_key(course_code, 'corequisites')
        cached = redis_client.get(key)
        if isinstance(cached, bytes):
            import json
            return json.loads(cached.decode())
        if not course_code or not isinstance(course_code, str):
            return []
        logic = self.coreq_logic.get(course_code)
        result = list(logic.get_all_courses()) if logic else []
        import json
        redis_client.set(key, json.dumps(result))
        invalidate_graph_cache()
        return result

    def get_dependents(self, course_code: str) -> List[str]:
        key = _graph_cache_key(course_code, 'dependents')
        cached = redis_client.get(key)
        if isinstance(cached, bytes):
            import json
            return json.loads(cached.decode())
        if not course_code or not isinstance(course_code, str):
            return []
        result = list(self.adjacency.get(course_code, set()))
        import json
        redis_client.set(key, json.dumps(result))
        invalidate_graph_cache()
        return result

    def get_edges(self, course_code: str) -> Dict[str, List[str]]:
        coreqs = []
        logic = self.coreq_logic.get(course_code)
        if logic is not None:
            coreqs = list(logic.get_all_courses())
        return {
            'prereqs': list(self.reverse_adjacency.get(course_code, set())),
            'coreqs': coreqs,
            'dependents': list(self.adjacency.get(course_code, set())),
        }

    def get_edge_count(self) -> int:
        return sum(len(v) for v in self.adjacency.values())

    def get_node_count(self) -> int:
        return len(self.nodes)