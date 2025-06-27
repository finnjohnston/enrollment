import json
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.courses import Catalog, Course
from models.graph.dependency_graph import DependencyGraph
from models.requirements.program_builder import ProgramBuilder

with open("data/courses/parsed.json", "r") as f:
    course_data = json.load(f)

with open("data/programs/majors.json", "r") as f:
    program_data = json.load(f)

program = ProgramBuilder.build_program(program_data[0])
catalog = Catalog(course_data)
graph = DependencyGraph(catalog)