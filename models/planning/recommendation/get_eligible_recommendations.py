from typing import Dict, Set
from models.graph.eligibility import CourseEligibility
from models.graph.dependency_graph import DependencyGraph

def get_eligible_recommendations(recommendations_dict: Dict[str, Set[str]], completed_courses: Set[str], enrolled_courses: Set[str], graph: DependencyGraph) -> Dict[str, Set[str]]:
    """
    Given a dictionary {category: set(course_codes)}, completed_courses, enrolled_courses, and graph,
    returns a dictionary {category: set(eligible_course_codes)} with only eligible courses.
    """
    eligible_recs: Dict[str, Set[str]] = {}
    for category, course_codes in recommendations_dict.items():
        eligible = set()
        for code in course_codes:
            if CourseEligibility.is_course_eligible(code, completed_courses, enrolled_courses, graph):
                eligible.add(code)
        eligible_recs[category] = eligible
    return eligible_recs 