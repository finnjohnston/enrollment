from typing import Dict, List, Set, Tuple
from models.requirements.requirement_types.compound import CompoundRequirement
from models.courses.course import Course
from models.requirements.requirement_types.requirement import Requirement
from models.courses.catalog import Catalog

def build_recommendation_sets(unmet_requirements: Dict[Tuple[str, str], List[Requirement]],catalog: Catalog) -> Dict[str, Set[str]]:
    """
    For each unmet requirement in each category, get all potential courses that could satisfy it (not filtered on completion or eligibility),
    and group them by requirement category (category_name).
    Returns: dict where key is category name and value is set of course codes that could satisfy unmet requirements in that category.
    """
    all_courses = catalog.courses
    recommendation_sets = {}
    for (program_name, category_name), requirement_list in unmet_requirements.items():
        category_courses = set()
        for req in requirement_list:
            possible = req.get_possible_courses(all_courses)
            for course in possible:
                code = course.get_course_code()
                if code:
                    category_courses.add(code)
        if category_name not in recommendation_sets:
            recommendation_sets[category_name] = set()
        recommendation_sets[category_name].update(category_courses)
    return recommendation_sets 