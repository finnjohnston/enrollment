from typing import List, Dict, Tuple, Optional, Set
from models.requirements.program import Program
from models.requirements.requirement_types.requirement import Requirement
from models.requirements.requirement_types.course_filter import CourseFilterRequirement
from models.requirements.requirement_types.course_options import CourseOptionsRequirement
from models.requirements.requirement_types.course_list import CourseListRequirement
from models.requirements.requirement_types.compound import CompoundRequirement
from models.courses.course import Course
from models.courses.catalog import Catalog
from models.graph.eligibility import CourseEligibility
from models.graph.dependency_graph import DependencyGraph


def get_unmet_requirements(programs: List[Program], completed_courses: List[Course], requirement_assignments: Optional[Dict[str, List[Tuple[str, str]]]] = None) -> Dict[Tuple[str, str], List[Requirement]]:
    """
    Given a list of Program objects and a list of completed Course objects,
    return a dict mapping (program_name, category_name) to a list of unmet requirement objects for that category in that program.
    Checks both individual requirement satisfaction AND category-level completion (total credits).
    
    Args:
        programs: List of programs to check
        completed_courses: List of completed courses
        requirement_assignments: Optional dict mapping course_code to category_name for assigned courses
    """
    unmet = {}
    for program in programs:
        for category in program.categories:
            # Always filter completed courses to only those assigned to this category
            if requirement_assignments:
                assigned_courses = []
                for course in completed_courses:
                    course_code = course.get_course_code()
                    if course_code and course_code in requirement_assignments:
                        for prog_name, cat_name in requirement_assignments[course_code]:
                            if prog_name == program.name and cat_name == category.category:
                                assigned_courses.append(course)
                                break
            else:
                assigned_courses = completed_courses

            # First check if the category as a whole is complete
            category_progress = category.progress(assigned_courses, None)
            category_complete = category_progress.get("complete", False)
            
            # If the category is complete, skip it entirely
            if category_complete:
                continue
                
            # Otherwise, check individual requirements
            unmet_reqs = []
            for req in category.requirements:
                try:
                    satisfied_credits = req.satisfied_credits(assigned_courses)
                    if isinstance(req, CourseOptionsRequirement):
                        completed_codes = {c.get_course_code() for c in assigned_courses}
                        matching_courses = completed_codes.intersection(set(req.options))
                        is_satisfied = len(matching_courses) >= req.min_required
                    elif isinstance(req, CourseListRequirement):
                        completed_codes = {c.get_course_code() for c in assigned_courses}
                        is_satisfied = all(course in completed_codes for course in req.courses)
                    elif isinstance(req, CompoundRequirement):
                        is_satisfied = False
                        for opt in req.options:
                            if hasattr(opt, 'min_credits') and getattr(opt, 'min_credits', None) is not None:
                                if opt.satisfied_credits(assigned_courses) >= getattr(opt, 'min_credits', 0):
                                    is_satisfied = True
                                    break
                            elif hasattr(opt, 'min_required') and getattr(opt, 'min_required', None) is not None:
                                completed_codes = {c.get_course_code() for c in assigned_courses}
                                matching_courses = completed_codes.intersection(set(getattr(opt, 'options', [])))
                                if len(matching_courses) >= getattr(opt, 'min_required', 0):
                                    is_satisfied = True
                                    break
                            elif hasattr(opt, 'courses'):
                                completed_codes = {c.get_course_code() for c in assigned_courses}
                                if all(course in completed_codes for course in getattr(opt, 'courses', [])):
                                    is_satisfied = True
                                    break
                            else:
                                if opt.satisfied_credits(assigned_courses) > 0:
                                    is_satisfied = True
                                    break
                    else:
                        is_satisfied = satisfied_credits > 0
                except Exception:
                    is_satisfied = False
                if not is_satisfied:
                    unmet_reqs.append(req)
            if unmet_reqs:
                unmet[(program.name, category.category)] = unmet_reqs
    return unmet


def get_all_recommendations(unmet_requirements: Dict[Tuple[str, str], List[Requirement]], catalog: Catalog) -> Dict[str, List[Course]]:
    """
    For each unmet requirement in each category, get all potential courses that could satisfy it (not filtered on completion or eligibility),
    and group them by requirement category (category_name).
    Returns: dict where key is category name and value is list of Course objects that could satisfy unmet requirements in that category.
    """
    all_courses = catalog.courses
    recommendation_sets = {}
    for (program_name, category_name), requirement_list in unmet_requirements.items():
        category_courses = []
        if not requirement_list:
            category_courses = [c for c in all_courses if c.get_course_code()]
        else:
            for req in requirement_list:
                possible = req.get_possible_courses(all_courses)
                for course in possible:
                    if course.get_course_code():
                        category_courses.append(course)
        if category_name not in recommendation_sets:
            recommendation_sets[category_name] = []
        recommendation_sets[category_name].extend(category_courses)
    return recommendation_sets


def get_eligible_recommendations(recommendations_dict: Dict[str, List[Course]], completed_courses: List[Course], enrolled_courses: List[Course], graph: DependencyGraph) -> Dict[str, List[Course]]:
    """
    Given a dictionary {category: list(courses)}, completed_courses, enrolled_courses, and graph,
    returns a dictionary {category: list(eligible_courses)} with only eligible courses.
    """
    # Convert Course objects to course codes for eligibility checking
    completed_codes: Set[str] = set()
    for course in completed_courses:
        code = course.get_course_code()
        if code:
            completed_codes.add(code)
    
    enrolled_codes: Set[str] = set()
    for course in enrolled_courses:
        code = course.get_course_code()
        if code:
            enrolled_codes.add(code)
    
    eligible_recs: Dict[str, List[Course]] = {}
    for category, courses in recommendations_dict.items():
        eligible = []
        for course in courses:
            code = course.get_course_code()
            if code and CourseEligibility.is_course_eligible(code, completed_codes, enrolled_codes, graph):
                eligible.append(course)
        eligible_recs[category] = eligible
    return eligible_recs 