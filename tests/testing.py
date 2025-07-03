import json
import sys
from pathlib import Path
import types

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.courses.catalog import Catalog
from models.requirements.program_builder import ProgramBuilder
from models.graph.dependency_graph import DependencyGraph
from models.planning.plan_config import PlanConfig
from models.planning.semester import Semester
from models.planning.plan import Plan
from models.courses.course import Course
from models.planning.recommendation import get_unmet_requirements
from models.planning.recommendation.get_unmet_requirements import get_unmet_requirements
from models.planning.recommendation.build_recommendation_sets import build_recommendation_sets


with open("data/courses/parsed.json", 'r') as f:
    courses_data = json.load(f)
    catalog = Catalog(courses_data)
    graph = DependencyGraph(catalog)

with open("data/programs/majors.json", 'r') as f:
    majors_data = json.load(f)
    cs_major_data = majors_data[0]
    cs_major = ProgramBuilder.build_program(cs_major_data)

unmet = get_unmet_requirements([cs_major], [])
recs = build_recommendation_sets(unmet, catalog)
print(recs)



