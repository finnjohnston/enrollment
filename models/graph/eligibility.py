from typing import Set
from .dependency_graph import DependencyGraph

class CourseEligibility:
    @staticmethod
    def is_course_eligible(course_code: str, completed_courses: Set[str], enrolled_courses: Set[str], graph: DependencyGraph) -> bool:
        # Treat enrolled_courses as the same as completed_courses
        all_completed = set(completed_courses) | set(enrolled_courses)
        if course_code in all_completed:
            return False
        prereq_logic = graph.get_prerequisite_logic(course_code)
        coreq_logic = graph.get_corequisite_logic(course_code)
        prereqs_ok = prereq_logic.is_satisfied(all_completed) if prereq_logic else True
        if not prereqs_ok:
            return False
        # Handle mutual corequisites
        group = CourseEligibility._find_mutual_coreq_group(course_code, completed_courses, graph)
        if len(group) > 1:
            # All courses in the group must be in all_completed (i.e., being taken together or already completed)
            # But if any are already completed, not eligible (shouldn't re-take)
            if group.issubset(all_completed) and group.isdisjoint(completed_courses):
                return True
            else:
                return False
        # Otherwise, use standard coreq logic
        coreqs_ok = coreq_logic.is_satisfied(all_completed, all_completed) if coreq_logic else True
        return coreqs_ok

    @staticmethod
    def _find_mutual_coreq_group(course_code: str, completed_courses: Set[str], graph: DependencyGraph) -> Set[str]:
        # Traverse through coreqs to find all mutually-locked courses (excluding completed)
        group = set()
        visited = set()
        stack = [course_code]
        while stack:
            curr = stack.pop()
            if curr in visited or curr in completed_courses:
                continue
            visited.add(curr)
            group.add(curr)
            coreq_logic = graph.get_corequisite_logic(curr)
            if not coreq_logic:
                continue
            for coreq in coreq_logic.get_all_courses():
                other_coreq_logic = graph.get_corequisite_logic(coreq)
                if other_coreq_logic and curr in other_coreq_logic.get_all_courses():
                    if coreq not in visited and coreq not in completed_courses:
                        stack.append(coreq)
        return group