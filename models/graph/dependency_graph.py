from typing import Dict, Set, List, Optional, Tuple, cast
from models.courses.course import Course
from models.requirements.program import Program
from models.requirements.requirement_types.requirement import Requirement
from models.requirements.requirement_types.course_list import CourseListRequirement
from models.requirements.requirement_types.course_options import CourseOptionsRequirement
from models.graph.logic import PrerequisiteLogic, CorequisiteLogic

class DependencyGraph:
    """
    Represents the dependency graph for all courses in the catalog.
    Handles navigation, prerequisite/corequisite logic, and availability checking for planning.
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
            raise ValueError(f"Course '{course_code}' not found in catalog.")

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
        if not course_code or not isinstance(course_code, str):
            return []
        return list(self.reverse_adjacency.get(course_code, set()))

    def get_corequisites(self, course_code: str) -> List[str]:
        if not course_code or not isinstance(course_code, str):
            return []
        logic = self.coreq_logic.get(course_code)
        return list(logic.get_all_courses()) if logic else []

    def get_dependents(self, course_code: str) -> List[str]:
        if not course_code or not isinstance(course_code, str):
            return []
        return list(self.adjacency.get(course_code, set()))

    def get_all_prerequisites(self, course_code: str) -> Set[str]:
        if not course_code or not isinstance(course_code, str):
            return set()
        visited = set()
        stack = list(self.get_prerequisites(course_code))
        while stack:
            curr = stack.pop()
            if curr not in visited:
                visited.add(curr)
                stack.extend(self.get_prerequisites(curr))
        return visited

    def get_all_dependents(self, course_code: str) -> Set[str]:
        if not course_code or not isinstance(course_code, str):
            return set()
        visited = set()
        stack = list(self.get_dependents(course_code))
        while stack:
            curr = stack.pop()
            if curr not in visited:
                visited.add(curr)
                stack.extend(self.get_dependents(curr))
        return visited

    # === PATH FINDING ===
    
    def get_all_full_prerequisite_paths(self, course_code: str) -> List[List[str]]:
        logic = self.get_prerequisite_logic(course_code)

        if not logic or not logic.groups:
            return [[course_code]]
        all_paths = []
        combos = logic.get_all_satisfying_combinations(set())
        for combo in combos:
            subpaths = [self.get_all_full_prerequisite_paths(prereq) for prereq in combo]

            from itertools import product
            for path_tuple in product(*subpaths):
                merged = []
                seen = set()
                for sub in path_tuple:
                    for course in sub:
                        if course not in seen:
                            seen.add(course)
                            merged.append(course)
                merged.append(course_code)
                all_paths.append(merged)
        return all_paths 

    def get_all_paths_to_course(self, from_course: str, to_course: str) -> List[List[str]]:
        if not from_course or not to_course:
            return []
        
        all_prereq_paths = self.get_all_full_prerequisite_paths(to_course)
        
        valid_paths = []
        for path in all_prereq_paths:
            if from_course in path:
                try:
                    start_index = path.index(from_course)
                    candidate_path = path[start_index:]
                    
                    if self._includes_all_required_prereqs(candidate_path, to_course):
                        if candidate_path not in valid_paths:
                            valid_paths.append(candidate_path)
                except ValueError:
                    continue
        
        return valid_paths

    def get_shortest_path_to_course(self, from_course: str, to_course: str) -> List[str]:
        if not from_course or not to_course:
            return []
        
        all_paths = self.get_all_paths_to_course(from_course, to_course)
        if not all_paths:
            return []
        
        return min(all_paths, key=len)

    def get_critical_path(self, target_course: str) -> List[str]:
        """
        Get the longest prerequisite path to a target course, respecting AND/OR logic.
        This represents the maximum time needed to reach the course.
        """
        if not target_course or not isinstance(target_course, str):
            return []
        
        all_prereq_paths = self.get_all_full_prerequisite_paths(target_course)
        if not all_prereq_paths:
            return [target_course]
        
        return max(all_prereq_paths, key=len)

    def _includes_all_required_prereqs(self, path: List[str], target_course: str) -> bool:
        """
        Check if a path includes all required prerequisites for the target course.
        """
        if not path or path[-1] != target_course:
            return False
        
        target_logic = self.get_prerequisite_logic(target_course)
        if not target_logic:
            return True
        
        path_set = set(path[:-1])
        return target_logic.is_satisfied(path_set)

    # === AVAILABILITY & PLANNING ===
    
    def _is_available_internal(self, course_code: str, completed_codes: Set[str]) -> bool:
        """Internal method that works with course codes."""
        if course_code in completed_codes:
            return False
        
        logic = self.prereq_logic.get(course_code)
        if not logic:
            return True
        
        return logic.is_satisfied(completed_codes)

    # === UTILITY METHODS ===
    
    def get_edges(self, course_code: str) -> Dict[str, List[str]]:
        """Get all edges (prerequisites, corequisites, dependents) for a course."""
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
        """Get total number of edges in the graph."""
        return sum(len(v) for v in self.adjacency.values())

    def get_node_count(self) -> int:
        """Get total number of nodes in the graph."""
        return len(self.nodes)