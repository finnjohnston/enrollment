import json
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.courses.catalog import Catalog
from models.requirements.program_builder import ProgramBuilder
from models.graph.dependency_graph import DependencyGraph

with open("data/courses/parsed.json", 'r') as f:
    courses_data = json.load(f)
    catalog = Catalog(courses_data)

with open("data/programs/majors.json", 'r') as f:
    majors_data = json.load(f)
    cs_major_data = majors_data[0]
    cs_major = ProgramBuilder.build_program(cs_major_data)

graph = DependencyGraph(catalog)