from typing import List, Optional, Union, Any
from models.courses.course import Course

class Requirement:
    """
    Abstract base class for all requirement types.
    """
    
    def __init__(self, restrictions: Optional[object] = None):
        self.restrictions = restrictions
    
    def describe(self) -> str:
        raise NotImplementedError("Subclasses must implement describe()")
    
    def satisfied_credits(self, completed_courses: List[Course]) -> int:
        raise NotImplementedError("Subclasses must implement satisfied_credits()")
    
    def get_completed_courses(self, completed_courses: List[Course]) -> List[Course]:
        """Returns the subset of completed_courses that satisfy this requirement."""
        raise NotImplementedError("Subclasses must implement get_completed_courses()")
    
    def get_possible_courses(self, courses: List[Course]) -> List[Course]:
        """Returns all courses from the provided list that could satisfy this requirement."""
        raise NotImplementedError("Subclasses must implement get_possible_courses()")

def extract_course_codes(reqs: Any) -> List[List[str]]:
    """
    Given a prereqs/coreqs list, extract all possible AND-paths as lists of course codes.
    Each returned list is a set of course codes that, if all are taken, satisfy one path.
    """
    from itertools import product
    if reqs is None:
        return []
    if isinstance(reqs, str):
        return [[reqs]]
    if isinstance(reqs, list):
        # If all items are strings, this is an OR-group
        if all(isinstance(x, str) for x in reqs):
            return [[x] for x in reqs]
        # If all items are lists, treat as OR between those paths
        if all(isinstance(x, list) for x in reqs):
            # Special case: [course, [[or-group1], [or-group2], ...]]
            if len(reqs) == 2 and isinstance(reqs[0], str) and all(isinstance(g, list) for g in reqs[1]):
                nested = [extract_course_codes(reqs[0])]
                for group in reqs[1]:
                    nested.append(extract_course_codes(group))
                combos = list(product(*nested))
                return [[item for sublist in combo for item in sublist] for combo in combos]
            # Otherwise, treat as OR between paths
            result = []
            for path in reqs:
                subpaths = extract_course_codes(path)
                result.extend(subpaths)
            return result
        # If any item is a list of lists (nested AND of OR-groups), take cartesian product
        if any(isinstance(x, list) and all(isinstance(y, list) for y in x) for x in reqs):
            subresults = []
            for x in reqs:
                if isinstance(x, list) and all(isinstance(y, list) for y in x):
                    # Each y is an OR-group
                    or_group_results = []
                    for y in x:
                        or_group_results.append(extract_course_codes(y))
                    # Take cartesian product of all OR-groups
                    combos = list(product(*or_group_results))
                    subresults.append([[item for sublist in combo for item in sublist] for combo in combos])
                else:
                    subresults.append(extract_course_codes(x))
            combos = list(product(*subresults))
            return [[item for sublist in combo for item in sublist] for combo in combos]
        # Otherwise, treat as AND-group: cartesian product of subresults
        subresults = [extract_course_codes(x) for x in reqs]
        combos = list(product(*subresults))
        return [[item for sublist in combo for item in sublist] for combo in combos]
    return []