from typing import Set
from .dependency_graph import DependencyGraph
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def _eligibility_cache_key(course_code, completed_courses, enrolled_courses):
    # Sort sets to ensure consistent key
    completed = ','.join(sorted(completed_courses))
    enrolled = ','.join(sorted(enrolled_courses))
    return f"eligibility:{course_code}|completed:{completed}|enrolled:{enrolled}"

class CourseEligibility:
    @staticmethod
    def is_course_eligible(course_code: str, completed_courses: Set[str], enrolled_courses: Set[str], graph: DependencyGraph) -> bool:
        key = _eligibility_cache_key(course_code, completed_courses, enrolled_courses)
        cached = redis_client.get(key)
        if cached is not None:
            return cached == b'True'
        
        # Treat enrolled_courses as the same as completed_courses
        all_completed = set(completed_courses) | set(enrolled_courses)
        if course_code in all_completed:
            redis_client.set(key, 'False')
            return False
        
        # Check prerequisites first
        prereq_logic = graph.get_prerequisite_logic(course_code)
        prereqs_ok = prereq_logic.is_satisfied(all_completed) if prereq_logic else True
        if not prereqs_ok:
            redis_client.set(key, 'False')
            return False
        
        # Handle mutual corequisites
        group = CourseEligibility._find_mutual_coreq_group(course_code, completed_courses, graph)
        if len(group) > 1:
            # For mutual corequisites, we need to check if any course in the group
            # is already completed (which would make the whole group ineligible)
            # or if the entire group can be taken together
            if group.intersection(completed_courses):
                # If any course in the group is already completed, not eligible
                redis_client.set(key, 'False')
                return False
            # If none are completed, check if ALL courses in the group are eligible to be taken together
            for group_course in group:
                # Check prerequisites for each course in the group
                prereq_logic = graph.get_prerequisite_logic(group_course)
                if prereq_logic and not prereq_logic.is_satisfied(all_completed):
                    # If any course in the group has unsatisfied prerequisites, the whole group is ineligible
                    redis_client.set(key, 'False')
                    return False
            # All courses in the group are eligible to be taken together
            redis_client.set(key, 'True')
            return True
        
        # For regular corequisites, check if they can be satisfied
        coreq_logic = graph.get_corequisite_logic(course_code)
        if coreq_logic:
            # Check if corequisites are satisfied by completed courses
            coreqs_ok = coreq_logic.is_satisfied(all_completed, all_completed)
            if not coreqs_ok:
                # If corequisites are not satisfied by completed courses,
                # check if they can be satisfied by taking them together
                coreq_courses = coreq_logic.get_all_courses()
                # If any corequisite is already completed, we can take this course
                if coreq_courses.intersection(completed_courses):
                    redis_client.set(key, 'True')
                    return True
                # If no corequisites are completed, check if they can be taken together
                # For now, we'll be conservative and only allow if the corequisites
                # are simple (single course) and not already completed
                if len(coreq_courses) == 1:
                    coreq_course = list(coreq_courses)[0]
                    # Check if the corequisite course is eligible to be taken
                    if coreq_course not in all_completed:
                        # Check if the corequisite has its own prerequisites satisfied
                        prereq_logic = graph.get_prerequisite_logic(coreq_course)
                        if prereq_logic:
                            coreq_prereqs_ok = prereq_logic.is_satisfied(all_completed)
                            if not coreq_prereqs_ok:
                                redis_client.set(key, 'False')
                                return False
                        redis_client.set(key, 'True')
                        return True
                # For complex corequisite groups, be conservative and require them to be completed
                redis_client.set(key, 'False')
                return False
            redis_client.set(key, 'True')
            return True
        
        redis_client.set(key, 'True')
        return True

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