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
# Specify category assignments for ambiguous courses here
user_category_assignments = {
    "ECON 1010": "Liberal Arts Core",
    "ENGL 1230W": "Liberal Arts Core",
    "ECON 1020": "Liberal Arts Core"
}

# Specify planned courses for each semester (Fall 2025, Spring 2026, ...)
user_semester_courses = [
    # Fall 2025
    ["CHEM 1601", "CHEM 1601L", "MATH 1300", "ES 1401", "ES 1402", "ES 1403", "ECON 1010", "ENGL 1230W"],
    # Spring 2026
    ["PHYS 1601", "PHYS 1601L", "MATH 1301", "CS 1101", "ECON 1020"],
    # Fall 2026
    ["PHYS 1602", "PHYS 1602L", "CS 2201", "CS 2212"],
]

# === Recommendation Logic ===
def recommend_courses_for_semester(plan_config: PlanConfig, plan: Plan, semester: Semester, catalog: Catalog, dependency_graph: DependencyGraph, user_category_assignments=None) -> Dict[str, List[Union[Course, List[Course]]]]:
    if user_category_assignments is None:
        user_category_assignments = {}
    completed_codes = {c.course_code for c in plan_config.completed_courses if hasattr(c, 'course_code') and not isinstance(c, list) and c.course_code}
    planned_codes = set()
    for sem in plan.semesters:
        for c in getattr(sem, 'planned_courses', []):
            if hasattr(c, 'course_code') and not isinstance(c, list):
                planned_codes.add(c.course_code)
    all_taken_codes = completed_codes | planned_codes
    eligible_by_category = {}
    assignment_manager = CategoryAssignmentManager()
    # --- Assign completed/planned courses to categories (user override if present) ---
    for program in plan_config.programs:
        for cat in program.categories:
            for req in cat.requirements:
                from models.requirements.requirement_types.compound import CompoundRequirement
                if isinstance(req, CompoundRequirement):
                    possible = req.get_possible_courses(catalog.courses, [c for c in catalog.courses if c.course_code in all_taken_codes])
                else:
                    possible = req.get_possible_courses(catalog.courses)
                for possible_course in possible:
                    if isinstance(possible_course, list):
                        continue
                    code = possible_course.course_code
                    if code in all_taken_codes:
                        # Use user assignment if present, else default
                        category = user_category_assignments.get(code, cat.category)
                        if code is not None and not assignment_manager.is_assigned(code):
                            assignment_manager.assign(code, category)
    # --- Build eligible_by_category, excluding already assigned courses ---
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

# === Main Script ===
if __name__ == "__main__":
    # --- Load data ---
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
    completed_codes = set()
    for i in range(num_years * 2):
        season = seasons[i % 2]
        year = start_year + (i // 2)
        planned_codes = user_semester_courses[i] if i < len(user_semester_courses) else []
        planned_courses = [c for c in catalog.courses if hasattr(c, 'course_code') and c.course_code in planned_codes]
        semesters.append(Semester(season, year, planned_courses))
        completed_codes.update(planned_codes)
    # Find the first semester with no courses input (or the first semester if none input)
    next_semester_index = 0
    for i, codes in enumerate(user_semester_courses):
        if not codes:
            next_semester_index = i
            break
    else:
        next_semester_index = len(user_semester_courses)
        if next_semester_index >= len(semesters):
            print("All semesters are filled. No recommendations to make.")
            sys.exit(0)
    plan = Plan(semesters)
    completed_courses = [c for c in catalog.courses if hasattr(c, 'course_code') and c.course_code in completed_codes]
    plan_config = PlanConfig([program], completed_courses, start_season=start_season, start_year=start_year, num_years=num_years)
    graph = DependencyGraph(catalog)
    target_semester = semesters[next_semester_index]
    eligible_by_category = recommend_courses_for_semester(plan_config, plan, target_semester, catalog, graph, user_category_assignments)
    print(f"Eligible courses for {target_semester.season} {target_semester.year} by category:")
    if not eligible_by_category:
        print("No eligible courses found.")
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
            is_lab = item.course_code.endswith('L')
            coreq_list = getattr(item, 'corequisites', []) or []
            coreqs_in_recs = [c for c in courses if not isinstance(c, list) and hasattr(c, 'course_code') and c.course_code in coreq_list]
            if is_lab and coreqs_in_recs:
                coreq_str = ', '.join(f'{c.course_code}' for c in coreqs_in_recs)
                print(f"  - {item.course_code}: {item.title} (Must be taken with {coreq_str})")
            else:
                print(f"  - {item.course_code}: {item.title}") 