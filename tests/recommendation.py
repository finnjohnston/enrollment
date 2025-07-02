import json
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from typing import List, Set, Dict, Union

# === Imports from project ===
from models.planning.plan_config import PlanConfig
from models.planning.plan import Plan
from models.planning.semester import Semester
from models.courses.course import Course
from models.courses.catalog import Catalog
from models.graph.dependency_graph import DependencyGraph
from models.planning.category_assignment import CategoryAssignmentManager

# === User Configuration ===
# Specify planned courses by semester as a list of lists of dicts: [{course_code: category}, ...]
planned_courses_by_semester = [
    # Fall 2025
    [
        {"PHYS 1601": "Science"},
        {"PHYS 1601L": "Science"},
        {"MATH 1300": "Mathematics - Calculus/Linear Algebra"},
        {"ES 1401": "Introduction to Engineering"},
        {"ES 1402": "Introduction to Engineering"},
        {"ES 1403": "Introduction to Engineering"},
        {"ECON 1010": "Liberal Arts Core"},
        {"ENGL 1230W": "Liberal Arts Core"}
    ],
    # Spring 2026
    [
        {"PHYS 1602": "Science"},
        {"PHYS 1602L": "Science"},
        {"MATH 1301": "Mathematics - Calculus/Linear Algebra"},
        {"CS 1101": "Computer Science Core"},
        {"ECON 1020": "Liberal Arts Core"}
    ],
    # Fall 2026
    [
        {"CHEM 1601": "Science"},
        {"CHEM 1601L": "Science"},
        {"CS 2201": "Computer Science Core"},
        {"CS 2212": "Computer Science Core"},
        {"ECON 3012": "Liberal Arts Core"}
    ],
    # Spring 2027
    [],
    # Fall 2027
    [],
    # Spring 2028
    [],
    # Fall 2028
    [],
    # Spring 2029
    [],
]

# === Main Logic ===
def recommend_courses_for_semester(plan_config: PlanConfig, plan: Plan, semester: Semester, catalog: Catalog, dependency_graph: DependencyGraph) -> Dict[str, List[Union[Course, List[Course]]]]:
    completed_codes = {c.course_code for c in plan_config.completed_courses if hasattr(c, 'course_code') and not isinstance(c, list) and c.course_code}
    planned_codes = set()

    for sem in plan.semesters:
        for c in getattr(sem, 'planned_courses', []):
            if hasattr(c, 'course_code') and c.course_code:
                planned_codes.add(c.course_code)

    all_taken_codes = completed_codes | planned_codes
    assignment_manager = CategoryAssignmentManager()

    # Assign completed courses to categories (first eligible by default)
    program = plan_config.programs[0]
    for cat in program.categories:
        for possible_course in plan_config.completed_courses:
            if hasattr(possible_course, 'course_code') and possible_course.course_code in all_taken_codes:
                if possible_course.course_code is not None and not assignment_manager.is_assigned(possible_course.course_code):
                    assignment_manager.assign(possible_course.course_code, cat.category)

    # Assign planned courses to categories using user assignments from planned_courses_by_semester
    for sem_idx, sem in enumerate(plan.semesters):
        if sem_idx < len(planned_courses_by_semester):
            for course_dict in planned_courses_by_semester[sem_idx]:
                for course_code, category in course_dict.items():
                    if course_code and not assignment_manager.is_assigned(course_code):
                        assignment_manager.assign(course_code, category)

    # --- Build eligible_by_category, excluding already assigned courses ---
    eligible_by_category = {}
    for program in plan_config.programs:
        progress = program.progress([c for c in catalog.courses if c.course_code in all_taken_codes])
        for cat, cat_progress in zip(program.categories, progress.get('categories', [])):
            taken_courses = [c for c in catalog.courses if c.course_code in all_taken_codes]
            cat_progress = cat.progress(taken_courses)
            if not cat_progress.get('complete', False):
                category_name = cat.category
                eligible_by_category[category_name] = []
                for req in cat.requirements:
                    from models.requirements.requirement_types.compound import CompoundRequirement
                    if isinstance(req, CompoundRequirement):
                        possible = req.get_possible_courses(catalog.courses, [c for c in catalog.courses if c.course_code in all_taken_codes])
                    else:
                        possible = req.get_possible_courses(catalog.courses)
                    for possible_course in possible:
                        if isinstance(possible_course, list):
                            continue
                        # Exclude if already assigned to another category
                        if possible_course.course_code and possible_course.course_code not in all_taken_codes and possible_course.course_code is not None and not assignment_manager.is_assigned(possible_course.course_code):
                            eligible_by_category[category_name].append(possible_course)
    eligible_by_category = {k: v for k, v in eligible_by_category.items() if v}
    def is_eligible(course_code, checked=None):
        if checked is None:
            checked = set()
        if course_code in checked:
            return False
        checked.add(course_code)
        all_requisite_paths = dependency_graph.get_all_requisite_paths(course_code)
        for path in all_requisite_paths:
            missing = []
            for req in path:
                if isinstance(req, list):
                    if not any(code in all_taken_codes for code in req):
                        missing.append(req)
                else:
                    if req != course_code and req not in all_taken_codes:
                        missing.append(req)
            if not missing:
                return True
            coreqs = set(dependency_graph.get_corequisites(course_code))
            missing_coreqs = [req for req in missing if (isinstance(req, str) and req in coreqs) or (isinstance(req, list) and any(code in coreqs for code in req))]
            missing_prereqs = [req for req in missing if req not in missing_coreqs]
            if not missing_prereqs and missing_coreqs:
                def coreq_code_list(req):
                    if isinstance(req, list):
                        return [code for code in req if code in eligible_codes]
                    elif isinstance(req, str):
                        return [req] if req in eligible_codes else []
                    return []
                if all(any(is_eligible(code, checked.copy()) for code in coreq_code_list(req)) for req in missing_coreqs):
                    return True
        return False
    eligible_codes = set()
    for program in plan_config.programs:
        for cat in program.categories:
            for req in cat.requirements:
                from models.requirements.requirement_types.compound import CompoundRequirement
                if isinstance(req, CompoundRequirement):
                    possible = req.get_possible_courses(catalog.courses, [c for c in catalog.courses if hasattr(c, 'course_code') and not isinstance(c, list) and c.course_code in all_taken_codes])
                else:
                    possible = req.get_possible_courses(catalog.courses)
                for possible_course in possible:
                    if isinstance(possible_course, list):
                        continue
                    if hasattr(possible_course, 'course_code') and possible_course.course_code and possible_course.course_code not in all_taken_codes and possible_course.course_code is not None and not assignment_manager.is_assigned(possible_course.course_code):
                        eligible_codes.add(possible_course.course_code)
    # --- Group mutually corequisite courses robustly ---
    for category in list(eligible_by_category.keys()):
        eligible_courses = [c for c in eligible_by_category[category] if hasattr(c, 'course_code')]
        code_to_course = {c.course_code: c for c in eligible_courses}
        used_codes = set()
        groups = []
        def find_mutual_coreq_group(start_code, eligible_codes):
            group = set([start_code])
            queue = [start_code]
            while queue:
                code = queue.pop()
                coreqs = set(dependency_graph.get_corequisites(code)) & eligible_codes
                for coreq in coreqs:
                    if coreq not in group:
                        coreq_coreqs = set(dependency_graph.get_corequisites(coreq))
                        if group <= coreq_coreqs | set([coreq]):
                            group.add(coreq)
                            queue.append(coreq)
            return group
        eligible_codes = set(code_to_course.keys())
        for code in eligible_codes:
            if code in used_codes:
                continue
            group = find_mutual_coreq_group(code, eligible_codes)
            if len(group) > 1:
                groups.append(sorted(group))
                used_codes.update(group)
            else:
                groups.append([code])
                used_codes.add(code)
        unique_groups = []
        seen = set()
        for group in groups:
            group_tuple = tuple(sorted(group))
            if group_tuple not in seen:
                unique_groups.append(group)
                seen.add(group_tuple)
        filtered = []
        for group in unique_groups:
            if len(group) > 1:
                group_eligible = True
                for c in group:
                    all_requisite_paths = dependency_graph.get_all_requisite_paths(c)
                    eligible = False
                    for path in all_requisite_paths:
                        missing = []
                        for req in path:
                            if isinstance(req, list):
                                if not any(code in all_taken_codes or code in group for code in req):
                                    missing.append(req)
                            else:
                                if req != c and req not in all_taken_codes and req not in group:
                                    missing.append(req)
                        if all((isinstance(req, str) and req in group) or (isinstance(req, list) and any(code in group for code in req)) for req in missing):
                            eligible = True
                            break
                    if not eligible:
                        group_eligible = False
                        break
                if group_eligible:
                    filtered.append([code_to_course[c] for c in group])
            else:
                c = group[0]
                if is_eligible(c):
                    filtered.append(code_to_course[c])
        if filtered:
            eligible_by_category[category] = filtered
        else:
            del eligible_by_category[category]
    return eligible_by_category

# === Build Plan and Run Recommendation ===
if __name__ == "__main__":
    with open(os.path.join("data", "courses", "parsed.json"), "r") as f:
        courses_data = json.load(f)
        catalog = Catalog(courses_data)

    with open(os.path.join("data", "programs", "majors.json"), "r") as f:
        majors_data = json.load(f)
        first_major_data = majors_data[0]
        from models.requirements.program_builder import ProgramBuilder
        program = ProgramBuilder.build_program(first_major_data)

    start_year = 2025
    start_season = 'Fall'
    num_years = 4
    seasons = ['Fall', 'Spring']
    semesters = []
    for i, semester_courses in enumerate(planned_courses_by_semester):
        season = seasons[i % 2]
        year = start_year + (i // 2)
        planned_courses = []
        for course_dict in semester_courses:
            for course_code in course_dict:
                course = catalog.get_by_course_code(course_code)
                if course:
                    planned_courses.append(course)
        semesters.append(Semester(season, year, planned_courses))

    plan = Plan(semesters)
    completed_courses = []  # You can add completed courses here if needed
    plan_config = PlanConfig([program], completed_courses, start_season, start_year, num_years)

    # Find the first empty semester (or recommend for the first semester if all are empty)
    target_semester_idx = next((i for i, sem in enumerate(plan.semesters) if not sem.planned_courses), 0)
    target_semester = plan.semesters[target_semester_idx]

    graph = DependencyGraph(catalog)
    eligible_by_category = recommend_courses_for_semester(plan_config, plan, target_semester, catalog, graph)

    print(f"\nRecommendations for semester {target_semester_idx + 1}:")
    for category, courses in eligible_by_category.items():
        print(f"\n{category}:")
        for item in courses:
            if isinstance(item, list):
                print("  - Group:")
                for c in item:
                    print(f"    - {c.course_code}: {c.title}")
                continue
            if not hasattr(item, 'course_code') or not item.course_code:
                continue
            print(f"  - {item.course_code}: {item.title}") 