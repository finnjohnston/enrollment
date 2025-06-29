from typing import Dict, Set, List, Optional, Tuple
from models.courses.course import Course
from models.requirements.program import Program
from models.requirements.requirement_types.requirement import Requirement
from models.graph.logic import PrerequisiteLogic, CorequisiteLogic

class DependencyGraph:
    """
    Represents the dependency graph for all courses in the catalog.
    Handles navigation, prerequisite/corequisite logic, and program integration for scheduling.
    """
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
                continue  # Skip courses with no valid code
            self.nodes[code] = course
            self.adjacency[code] = set()
            self.reverse_adjacency[code] = set()
            # Extract logic using self._extract_requisites
            edges = self._extract_requisites(code)
            prereq_groups = edges.get('prereq_edges', [])
            coreq_groups = edges.get('coreq_edges', [])
            self.prereq_logic[code] = PrerequisiteLogic(prereq_groups)
            self.coreq_logic[code] = CorequisiteLogic(coreq_groups)
            # Build edges for prerequisites
            for group in prereq_groups:
                for prereq in group:
                    if prereq and isinstance(prereq, str):
                        self.reverse_adjacency[code].add(prereq)
                        self.adjacency.setdefault(prereq, set()).add(code)
            # Build edges for corequisites (for navigation, not blocking)
            for group in coreq_groups:
                for coreq in group:
                    if coreq and isinstance(coreq, str):
                        self.adjacency.setdefault(coreq, set()).add(code)

    # --- Core Graph Operations ---
    def add_node(self, course: Course):
        code = getattr(course, 'course_code', None)
        if not code or not isinstance(code, str):
            return
        self.nodes[code] = course
        self.adjacency[code] = set()
        self.reverse_adjacency[code] = set()

    def remove_node(self, course_code: str):
        if not course_code or not isinstance(course_code, str):
            return
        if course_code in self.nodes:
            del self.nodes[course_code]
        if course_code in self.adjacency:
            del self.adjacency[course_code]
        if course_code in self.reverse_adjacency:
            del self.reverse_adjacency[course_code]
        for adj in self.adjacency.values():
            adj.discard(course_code)
        for rev in self.reverse_adjacency.values():
            rev.discard(course_code)

    def get_node(self, course_code: str) -> Optional[Course]:
        if not course_code or not isinstance(course_code, str):
            return None
        return self.nodes.get(course_code)
    def has_node(self, course_code: str) -> bool:
        return bool(course_code) and course_code in self.nodes
    def get_all_nodes(self) -> List[Course]:
        return list(self.nodes.values())
    def get_node_count(self) -> int:
        return len(self.nodes)

    # --- Edge Management ---
    def add_prerequisite_edge(self, from_course: str, to_course: str, logic: PrerequisiteLogic):
        if not from_course or not to_course:
            return
        self.reverse_adjacency.setdefault(to_course, set()).add(from_course)
        self.adjacency.setdefault(from_course, set()).add(to_course)
        self.prereq_logic[to_course] = logic
    def add_corequisite_edge(self, from_course: str, to_course: str, logic: CorequisiteLogic):
        if not from_course or not to_course:
            return
        self.adjacency.setdefault(from_course, set()).add(to_course)
        self.coreq_logic[to_course] = logic
    def remove_edge(self, from_course: str, to_course: str, edge_type: str):
        if not from_course or not to_course:
            return
        if edge_type == 'prereq':
            self.reverse_adjacency.get(to_course, set()).discard(from_course)
            self.adjacency.get(from_course, set()).discard(to_course)
        elif edge_type == 'coreq':
            self.adjacency.get(from_course, set()).discard(to_course)

    def get_edges(self, course_code: str) -> Dict[str, List[str]]:
        # Only call get_all_courses if logic object is not None
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

    # --- Logic Integration ---
    def add_course_with_logic(self, course: Course):
        code = getattr(course, 'course_code', None)
        if not code or not isinstance(code, str):
            return
        edges = self._extract_requisites(code)
        prereq_groups = edges.get('prereq_edges', [])
        coreq_groups = edges.get('coreq_edges', [])
        self.prereq_logic[code] = PrerequisiteLogic(prereq_groups)
        self.coreq_logic[code] = CorequisiteLogic(coreq_groups)

    def get_course_logic(self, course_code: str) -> Tuple[Optional[PrerequisiteLogic], Optional[CorequisiteLogic]]:
        if not course_code or not isinstance(course_code, str):
            return (None, None)
        return (
            self.prereq_logic.get(course_code),
            self.coreq_logic.get(course_code)
        )
        
    def get_prerequisite_logic(self, course_code: str) -> Optional[PrerequisiteLogic]:
        if not course_code or not isinstance(course_code, str):
            return None
        return self.prereq_logic.get(course_code)
        
    def get_corequisite_logic(self, course_code: str) -> Optional[CorequisiteLogic]:
        if not course_code or not isinstance(course_code, str):
            return None
        return self.coreq_logic.get(course_code)

    def update_course_logic(self, course_code: str, prereq_logic: PrerequisiteLogic, coreq_logic: CorequisiteLogic):
        if not course_code or not isinstance(course_code, str):
            return
        self.prereq_logic[course_code] = prereq_logic
        self.coreq_logic[course_code] = coreq_logic

    # --- Traversal & Navigation ---
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

    def get_path_to_course(self, from_course: str, to_course: str) -> List[str]:
        if not from_course or not to_course:
            return []
        from collections import deque
        queue = deque([(from_course, [from_course])])
        visited = set()
        while queue:
            curr, path = queue.popleft()
            if curr == to_course:
                return path
            for neighbor in self.get_dependents(curr):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        return []

    def get_all_paths_to_course(self, from_course: str, to_course: str) -> List[List[str]]:
        if not from_course or not to_course:
            return []
        def dfs(curr, path, all_paths):
            if curr == to_course:
                all_paths.append(path[:])
                return
            for neighbor in self.get_dependents(curr):
                if neighbor not in path:
                    dfs(neighbor, path + [neighbor], all_paths)
        all_paths = []
        dfs(from_course, [from_course], all_paths)
        return all_paths

    def get_critical_path(self, target_course: str) -> List[str]:
        if not target_course or not isinstance(target_course, str):
            return []
        # Longest path to target_course
        def dfs(curr, path):
            if not self.get_prerequisites(curr):
                return path
            max_path = []
            for prereq in self.get_prerequisites(curr):
                candidate = dfs(prereq, [prereq] + path)
                if len(candidate) > len(max_path):
                    max_path = candidate
            return max_path
        return dfs(target_course, [target_course])

    # --- Availability & Planning ---
    def is_available(self, course_code: str, completed_courses: List[Course]) -> bool:
        """Check if a course is available given completed courses."""
        # Convert to set of course codes for internal processing
        completed_codes = {course.get_course_code() for course in completed_courses if course.get_course_code()}
        return self._is_available_internal(course_code, completed_codes)
    
    def _is_available_internal(self, course_code: str, completed_codes: Set[str]) -> bool:
        """Internal method that works with course codes."""
        if course_code in completed_codes:
            return False
        
        prereqs = self.get_prerequisites(course_code)
        if not prereqs:
            return True
        
        # Check if any prerequisite group is satisfied
        for group in prereqs:
            if all(course in completed_codes for course in group):
                return True
        
        return False

    def get_available_courses(self, completed_courses: List[Course]) -> Set[str]:
        """Get all courses that can be taken with the given completed courses."""
        # Convert to set of course codes for internal processing
        completed_codes = {course.get_course_code() for course in completed_courses if course.get_course_code()}
        available = set()
        for course_code in self.nodes:
            if self._is_available_internal(course_code, completed_codes):
                available.add(course_code)
        return available

    def get_blocked_courses(self, completed_courses: List[Course]) -> Set[str]:
        """Get all courses that are blocked by missing prerequisites."""
        # Convert to set of course codes for internal processing
        completed_codes = {course.get_course_code() for course in completed_courses if course.get_course_code()}
        blocked = set()
        for course_code in self.nodes:
            if not self._is_available_internal(course_code, completed_codes):
                blocked.add(course_code)
        return blocked

    def get_missing_prerequisites(self, course_code: str, completed_courses: List[Course]) -> List[List[str]]:
        """Get missing prerequisite groups for a course."""
        # Convert to set of course codes for internal processing
        completed_codes = {course.get_course_code() for course in completed_courses if course.get_course_code()}
        prereqs = self.get_prerequisites(course_code)
        missing = []
        for group in prereqs:
            if not all(course in completed_codes for course in group):
                missing.append(group)
        return missing

    def get_course_availability_details(self, course_code: str, completed_courses: List[Course]) -> Dict:
        """Get detailed availability information for a course."""
        # Convert to set of course codes for internal processing
        completed_codes = {course.get_course_code() for course in completed_courses if course.get_course_code()}
        
        is_available = self._is_available_internal(course_code, completed_codes)
        missing_prereqs = self.get_missing_prerequisites(course_code, completed_courses)
        dependents = self.get_dependents(course_code)
        
        return {
            "course_code": course_code,
            "available": is_available,
            "missing_prerequisites": missing_prereqs,
            "dependents": dependents,
            "completed_courses": list(completed_codes)
        }

    # --- Program Integration ---
    def get_optimal_schedule(self, program: Program, completed_courses: List[Course]) -> List[List[str]]:
        """Generate an optimal schedule for completing the program."""
        # Convert to set of course codes for internal processing
        completed_codes = {course.get_course_code() for course in completed_courses if course.get_course_code()}
        
        # This is a simplified implementation
        # In practice, you'd want more sophisticated scheduling logic
        schedule = []
        remaining_courses = set()
        
        # Get all required courses from the program
        for category in program.categories:
            for req in category.requirements:
                if hasattr(req, 'courses'):
                    remaining_courses.update(req.courses)
                elif hasattr(req, 'options'):
                    remaining_courses.update(req.options)
        
        # Remove already completed courses
        remaining_courses -= completed_codes
        
        # Simple scheduling: take available courses
        available = self.get_available_courses(completed_courses)
        current_term = list(available & remaining_courses)
        
        if current_term:
            schedule.append(current_term)
        
        return schedule

    def get_unlocked_requirements(self, program: Program, completed_courses: List[Course]) -> List[Requirement]:
        """Get requirements that are unlocked by completed courses."""
        # Convert to set of course codes for internal processing
        completed_codes = {course.get_course_code() for course in completed_courses if course.get_course_code()}
        
        unlocked = []
        for category in program.categories:
            for req in category.requirements:
                if hasattr(req, 'courses') and isinstance(req.courses, list):
                    if all(self._is_available_internal(c, completed_codes) for c in req.courses if isinstance(c, str)):
                        unlocked.append(req)
        
        return unlocked

    def get_degree_plan(self, program: Program, completed_courses: List[Course]) -> List[List[str]]:
        """Generate a degree plan showing what to take each term."""
        # Convert to set of course codes for internal processing
        completed_codes = {course.get_course_code() for course in completed_courses if course.get_course_code()}
        
        # This is a simplified implementation
        # In practice, you'd want more sophisticated planning logic
        plan = []
        remaining_courses = set()
        
        # Get all required courses from the program
        for category in program.categories:
            for req in category.requirements:
                if hasattr(req, 'courses'):
                    remaining_courses.update(req.courses)
                elif hasattr(req, 'options'):
                    remaining_courses.update(req.options)
        
        # Remove already completed courses
        remaining_courses -= completed_codes
        
        # Simple planning: take available courses each term
        while remaining_courses:
            available = self.get_available_courses(completed_courses)
            current_term = list(available & remaining_courses)
            
            if not current_term:
                break  # No more courses can be taken
                
            plan.append(current_term)
            remaining_courses -= set(current_term)
            
            # Update completed courses for next iteration
            completed_codes.update(current_term)
            # Update completed_courses list for next get_available_courses call
            # This is a simplified approach - in practice you'd want to track actual Course objects
        
        return plan

    # --- Graph Analysis ---
    def detect_cycles(self) -> List[List[str]]:
        # Simple DFS-based cycle detection
        visited = set()
        stack = set()
        cycles = []
        def visit(node, path):
            if node in stack:
                idx = path.index(node)
                cycles.append(path[idx:])
                return
            if node in visited:
                return
            visited.add(node)
            stack.add(node)
            for neighbor in self.get_dependents(node):
                visit(neighbor, path + [neighbor])
            stack.remove(node)
        for node in self.nodes:
            visit(node, [node])
        return cycles
   
    def validate_graph(self) -> bool:
        return len(self.detect_cycles()) == 0
    
    def get_graph_stats(self) -> Dict:
        return {
            'node_count': self.get_node_count(),
            'edge_count': self.get_edge_count(),
        }
    
    def get_course_centrality(self, course_code: str) -> float:
        if not course_code or not isinstance(course_code, str):
            return 0.0
        # Simple centrality: number of dependents
        return float(len(self.get_dependents(course_code)))
    
    def get_bottleneck_courses(self) -> List[str]:
        # Courses with the most dependents
        max_dependents = 0
        bottlenecks = []
        for code in self.nodes:
            num = len(self.get_dependents(code))
            if num > max_dependents:
                max_dependents = num
                bottlenecks = [code]
            elif num == max_dependents:
                bottlenecks.append(code)
        return bottlenecks
   
    def get_subgraph(self, course_codes: List[str]) -> 'DependencyGraph':
        # Create a subgraph with only the specified course codes
        sub_catalog = type(self.catalog)([self.nodes[code] for code in course_codes if code in self.nodes])
        return DependencyGraph(sub_catalog)

    # --- Utility & Export ---
    def to_dict(self) -> Dict:
        return {
            'nodes': list(self.nodes.keys()),
            'edges': {k: list(v) for k, v in self.adjacency.items()},
        }
    
    def export_dot(self) -> str:
        lines = ['digraph G {']
        for src, targets in self.adjacency.items():
            for tgt in targets:
                lines.append(f'  "{src}" -> "{tgt}";')
        lines.append('}')
        return '\n'.join(lines)

    def get_all_full_prerequisite_paths(self, course_code: str) -> List[List[str]]:
        """
        Recursively enumerate all full prerequisite chains from root courses to the given course,
        expanding all AND/OR logic. Each path is a list of course codes from the earliest prerequisite
        up to the target course (inclusive), with no repeats.
        """
        logic = self.get_prerequisite_logic(course_code)
        # Base case: no prereqs or no logic
        if not logic or not logic.groups:
            return [[course_code]]
        all_paths = []
        combos = logic.get_all_satisfying_combinations(set())
        for combo in combos:
            # For each course in the combo, recursively expand
            subpaths = [self.get_all_full_prerequisite_paths(prereq) for prereq in combo]
            # Cartesian product of all subpaths
            from itertools import product
            for path_tuple in product(*subpaths):
                # Merge and deduplicate while preserving order
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