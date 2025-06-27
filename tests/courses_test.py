import json
from models.requirements.program_builder import ProgramBuilder
from models.courses.catalog import Catalog
from models.courses.query import Query
from models.requirements.requirement_types.course_list import CourseListRequirement
from models.requirements.requirement_types.course_options import CourseOptionsRequirement
from models.requirements.requirement_types.course_filter import CourseFilterRequirement
from models.requirements.requirement_types.compound import CompoundRequirement
from models.requirements.restrictions.exclusion import ExclusionRestriction


def get_courses_for_requirement(req, catalog):
    # Returns a list of Course objects that can fulfill the requirement
    if isinstance(req, CourseListRequirement):
        return [c for code in req.courses if (c := catalog.get_by_course_code(code))]
    elif isinstance(req, CourseOptionsRequirement):
        return [c for code in req.options if (c := catalog.get_by_course_code(code))]
    elif isinstance(req, CourseFilterRequirement):
        q = Query(catalog).reset()
        # Apply subject filter if present
        if hasattr(req, 'subject') and req.subject:
            q = q.by_subject(req.subject)
        # Apply tag/axle filter if present
        if hasattr(req, 'tags') and req.tags:
            q = q.by_axle(req.tags)
        # Apply min_level/max_level using by_level_range
        min_level = getattr(req, 'min_level', None)
        max_level = getattr(req, 'max_level', None)
        if min_level is not None or max_level is not None:
            q = q.by_level_range(min_level=min_level, max_level=max_level)
        possible_courses = q.results()
        return possible_courses
    elif isinstance(req, CompoundRequirement):
        # Flatten all possible courses from all options
        all_courses = []
        for opt in req.options:
            all_courses.extend(get_courses_for_requirement(opt, catalog))
        # Remove duplicates by course code
        seen = set()
        unique_courses = []
        for c in all_courses:
            code = c.get_course_code()
            if code and code not in seen:
                seen.add(code)
                unique_courses.append(c)
        return unique_courses
    else:
        return []

def apply_exclusions(courses, restrictions):
    if not restrictions:
        return courses
    filtered = courses
    for restriction in restrictions.restrictions:
        if isinstance(restriction, ExclusionRestriction):
            filtered = restriction.filter_courses(filtered)
    return filtered

if __name__ == "__main__":
    with open("data/programs/majors.json") as f:
        majors = json.load(f)
    cs_major = majors[0]  # Computer Science major
    program = ProgramBuilder.build_program(cs_major)

    with open("data/courses/parsed.json") as f:
        courses_data = json.load(f)
    catalog = Catalog(courses_data)

    print("CS Major Program object description:")
    print(program.describe())

    print("\nCatalog loaded with", len(catalog.courses), "courses.")

    print("\nIterating over categories and requirements:")
    for category in program.categories:
        print(f"\nCategory: {category.category}")
        for req in category.requirements:
            print(f"  Requirement type: {type(req).__name__}")
            try:
                print(f"    Description: {req.describe()}")
            except Exception as e:
                print(f"    [Error describing requirement: {e}]")
            # Get all possible courses for this requirement
            possible_courses = get_courses_for_requirement(req, catalog)
            # Apply exclusions if any
            if category.restrictions:
                possible_courses = apply_exclusions(possible_courses, category.restrictions)
            print(f"    Possible courses ({len(possible_courses)}):")
            codes = [course.get_course_code() for course in possible_courses]
            print(f"      {codes}")
        if category.restrictions:
            print("  Restrictions:")
            for restriction in category.restrictions.restrictions:
                print(f"    Restriction type: {type(restriction).__name__}")
                try:
                    print(f"      Description: {restriction.describe()}")
                except Exception as e:
                    print(f"      [Error describing restriction: {e}]") 