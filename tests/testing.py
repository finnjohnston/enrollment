import json
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.courses.catalog import Catalog
from models.requirements.program_builder import ProgramBuilder
from models.graph.dependency_graph import DependencyGraph
from models.planning.plan_config import PlanConfig

with open("data/courses/parsed.json", 'r') as f:
    courses_data = json.load(f)
    catalog = Catalog(courses_data)
    graph = DependencyGraph(catalog)

with open("data/programs/majors.json", 'r') as f:
    majors_data = json.load(f)
    cs_major_data = majors_data[0]
    cs_major = ProgramBuilder.build_program(cs_major_data)

completed_codes = ["MATH 1300", "MATH 1301", "MATH 2300", "MATH 2600"]
completed_courses = [catalog.get_by_course_code(code) for code in completed_codes]
completed_courses = [c for c in completed_courses if c is not None]

plan_config = PlanConfig([cs_major], completed_courses)
print(cs_major.progress(plan_config.completed_courses))