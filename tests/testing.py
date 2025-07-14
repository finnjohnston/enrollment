import json
import sys
from pathlib import Path
import types

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.courses.catalog import Catalog
from models.requirements.program_builder import ProgramBuilder
from models.planning.semester import Semester
from models.planning.academic_planner import AcademicPlanner
from models.requirements.policy_engine import PolicyEngine

# Load data
with open("data/courses/parsed.json", 'r') as f:
    courses_data = json.load(f)
    catalog = Catalog(courses_data)

with open("data/programs/majors.json", 'r') as f:
    majors_data = json.load(f)
    cs_major_data = majors_data[0]
    math_major_data = majors_data[1]
    cs_major = ProgramBuilder.build_program(cs_major_data)
    math_major = ProgramBuilder.build_program(math_major_data)

# Initialize policy engine
policy_engine = PolicyEngine()

# Initialize academic planner
start_semester = Semester("Fall", 2024)
planner = AcademicPlanner(catalog, [cs_major, math_major], start_semester, policy_engine=policy_engine)

print("=== Academic Planner Test ===\n")

# Semester 1
print("SEMESTER 1: Planning Fall 2024")
# New format: {course_code: [(program_name, category_name), ...]}
chosen_courses_sem1 = {
    "PHYS 1601": [("Computer Science", "Science")],
    "PHYS 1601L": [("Computer Science", "Science")],
    "MATH 1300": [("Computer Science", "Mathematics - Calculus/Linear Algebra"), ("Mathematics - Applied Track", "Calculus Sequence")],
    "ES 1401": [("Computer Science", "Introduction to Engineering")],
    "ES 1402": [("Computer Science", "Introduction to Engineering")],
    "ES 1403": [("Computer Science", "Introduction to Engineering")]
}
semester_result = planner.plan_semester(chosen_courses_sem1)

print(f"\n=== Semester 1 Results ===")
print(f"Plan valid: {semester_result['plan_valid']}")
print(f"Assignment results: {semester_result['assignment_results']}")
if not semester_result['plan_valid']:
    print("Plan has validation errors:")
    for error in semester_result['validation_result']['errors']:
        print(f"  - {error}")

# Semester 2
print("\nSEMESTER 2: Planning Spring 2025")
planner.advance_semester()
chosen_courses_sem2 = {
    "PHYS 1602": [("Computer Science", "Science")],
    "PHYS 1602L": [("Computer Science", "Science")],
    "MATH 1301": [("Computer Science", "Mathematics - Calculus/Linear Algebra"), ("Mathematics - Applied Track", "Calculus Sequence")],
    "CS 1101": [("Computer Science", "Computer Science Core")]
}
semester_result2 = planner.plan_semester(chosen_courses_sem2)

print(f"\n=== Semester 2 Results ===")
print(f"Plan valid: {semester_result2['plan_valid']}")
print(f"Assignment results: {semester_result2['assignment_results']}")
if not semester_result2['plan_valid']:
    print("Plan has validation errors:")
    for error in semester_result2['validation_result']['errors']:
        print(f"  - {error}")

# Semester 3 - Get recommendations
print("\nSEMESTER 3: Getting Recommendations for F~ll 2025")
planner.advance_semester()
recommendations = planner.get_recommendations()

# Get progress summary
print("\n=== Progress Summary ===")
progress = planner.get_progress_summary()
print(f"Current Semester: {progress['current_semester']}")
print(f"Total Completed Credits: {progress['total_completed_credits']}")
print(f"Completed Courses: {len(progress['completed_courses'])}")

for program_progress in progress['programs']:
    print(f"\nProgram: {program_progress['program']}")
    print(f"Type: {program_progress['type']}")
    print(f"Total Required: {program_progress['total_required']} credits")
    print(f"Total Earned: {program_progress['total_earned']} credits")
    print(f"Complete: {program_progress['complete']}")
    
    print("Category Progress:")
    for category in program_progress['categories']:
        print(f"  {category['category']}: {category['earned_credits']}/{category['required_credits']} credits ({'complete' if category['complete'] else 'incomplete'})")

print("\n=== Planning Complete ===")

