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
    
    def get_all_requisite_paths(self, course_code: str) -> List[List[str]]:
        """
        Recursively enumerate all full prerequisite chains from root courses to the given course,
        expanding all AND/OR logic. Each path is a list of course codes from the earliest prerequisite
        up to the target course (inclusive), with no repeats. Corequisites are included in the same step as the target course.
        """
        logic = self.get_prerequisite_logic(course_code)
        coreq_logic = self.get_corequisite_logic(course_code)

        # Base case: no prereqs or no logic
        if (not logic or not logic.groups) and (not coreq_logic or not coreq_logic.groups):
            return [[course_code]]
        all_paths = []
        combos = logic.get_all_satisfying_combinations(set()) if logic and logic.groups else [[]]
        for combo in combos:
            # For each course in the combo, recursively expand
            subpaths = []
            for prereq in combo:
                # If this is an OR group, preserve as a list
                if isinstance(prereq, list):
                    subpaths.append([prereq])
                else:
                    subpaths.append(self.get_all_requisite_paths(prereq))
            from itertools import product
            for path_tuple in product(*subpaths):
                # Merge and deduplicate while preserving order, and preserve OR groups as lists
                merged = []
                seen = set()
                for sub in path_tuple:
                    if isinstance(sub, list) and all(isinstance(x, str) for x in sub):
                        # This is a single path
                        for course in sub:
                            if course not in seen:
                                seen.add(course)
                                merged.append(course)
                    elif isinstance(sub, list) and all(isinstance(x, list) for x in sub):
                        # This is a preserved OR group
                        for group in sub:
                            merged.append(group)
                    elif isinstance(sub, list):
                        # Could be a preserved OR group
                        for item in sub:
                            if isinstance(item, list):
                                merged.append(item)
                            elif item not in seen:
                                seen.add(item)
                                merged.append(item)
                    else:
                        if sub not in seen:
                            seen.add(sub)
                            merged.append(sub)
                # Add corequisites (if any) in the same step as the target course
                coreqs = list(coreq_logic.get_all_courses()) if coreq_logic else []
                if coreqs:
                    merged.append(coreqs)
                # Finally, add the target course
                merged.append(course_code)
                all_paths.append(merged)
        return all_paths

    def get_all_paths_to_course(self, from_course: str, to_course: str) -> List[List[str]]:
        """
        Get all valid paths from from_course to to_course, considering both prerequisites and corequisites.
        Each path is a valid sequence of courses (with no repeats) that includes from_course and ends at to_course.
        """
        if not from_course or not to_course:
            return []
        all_prereq_paths = self.get_all_requisite_paths(to_course)
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

    def get_critical_path(self, target_course: str) -> List[str]:
        """
        Get the longest prerequisite path to a target course, respecting AND/OR logic and including corequisites.
        This represents the maximum time needed to reach the course, with corequisites taken concurrently.
        """
        if not target_course or not isinstance(target_course, str):
            return []
        all_prereq_paths = self.get_all_requisite_paths(target_course)
        if not all_prereq_paths:
            return [target_course]
        # The critical path is the longest one
        return max(all_prereq_paths, key=len)

    def get_shortest_path_to_course(self, from_course: str, to_course: str) -> List[str]:
        """
        Get the shortest path from from_course to to_course, considering both prerequisites and corequisites.
        Returns the shortest valid path (in terms of number of courses) that includes from_course and ends at to_course.
        """
        if not from_course or not to_course:
            return []
        all_paths = self.get_all_paths_to_course(from_course, to_course)
        if not all_paths:
            return []
        # The shortest path is the one with the fewest courses
        return min(all_paths, key=len)

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