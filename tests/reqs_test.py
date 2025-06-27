import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from typing import List, Dict, Any
from models.courses.catalog import Catalog
from models.courses.course import Course

def extract_requisites(catalog: Catalog, course_code: str) -> Dict[str, List[List[str]]]:
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

    course = catalog.get_by_course_code(course_code)
    if not course:
        raise ValueError(f"Course '{course_code}' not found in catalog.")
    
    def extract_requisites_and_of_ors(reqs: Any) -> List[List[str]]:
        """
        Extracts requisites preserving AND-of-ORs structure.
        Each inner list is an OR group, and the outer list is an AND of those groups.
        """
        if not reqs:
            return []
        if isinstance(reqs, str):
            return [[reqs]]
        if isinstance(reqs, list):
            # If all items are strings, this is an OR group
            if all(isinstance(x, str) for x in reqs):
                return [reqs]
            # If this is a list of lists, treat each as a group (AND between groups)
            result = []
            for item in reqs:
                group = extract_requisites_and_of_ors(item)
                # Flatten one level if group is a single OR group
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

    print(f"DEBUG: raw_prereqs for {course_code}: {raw_prereqs}")
    print(f"DEBUG: raw_coreqs for {course_code}: {raw_coreqs}")

    prereq_edges = extract_requisites_and_of_ors(raw_prereqs)
    coreq_edges = extract_requisites_and_of_ors(raw_coreqs)

    return {
        'prereq_edges': prereq_edges,
        'coreq_edges': coreq_edges
    }

if __name__ == "__main__":
    import json

    script_dir = os.path.dirname(__file__)
    data_file = os.path.join(script_dir, "..", "data", "courses", "parsed.json")
    
    with open(data_file, "r") as f:
        course_data = json.load(f)

    catalog = Catalog(course_data)

    # Example course to analyze
    target_course_code = "PHYS 2953L"
    
    edges = extract_requisites(catalog, target_course_code)
    print("\nExtracted edges:")
    print(f"Prerequisite edges: {edges['prereq_edges']}")
    print(f"Corequisite edges: {edges['coreq_edges']}")
    
    # Test with a few more courses to verify the logic
    test_courses = ["PHYS 2255", "PHYS 1912", "PHYS 2250W"]
    print("\nTesting with additional courses:")
    for course_code in test_courses:
        try:
            course_edges = extract_requisites(catalog, course_code)
            print(f"\n{course_code}:")
            print(f"  Prereqs: {course_edges['prereq_edges']}")
            print(f"  Coreqs: {course_edges['coreq_edges']}")
        except ValueError as e:
            print(f"\n{course_code}: {e}")

