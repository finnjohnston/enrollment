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

chosen_courses_sem1 = {
    "PHYS 1601": [("Computer Science", "Science")],
    "PHYS 1601L": [("Computer Science", "Science")],
    "MATH 1300": [("Computer Science", "Mathematics - Calculus/Linear Algebra"), ("Mathematics - Applied Track", "Calculus Sequence")],
    "ES 1401": [("Computer Science", "Introduction to Engineering")],
    "ES 1402": [("Computer Science", "Introduction to Engineering")],
    "ES 1403": [("Computer Science", "Introduction to Engineering")],
    "ECON 1010": [("Computer Science", "Liberal Arts Core")],
    "ENGL 1230W": [("Computer Science", "Liberal Arts Core")]
}
semester_result = planner.plan_semester(chosen_courses_sem1)

chosen_courses_sem2 = {
    "PHYS 1602": [("Computer Science", "Science")],
    "PHYS 1602L": [("Computer Science", "Science")],
    "MATH 1301": [("Computer Science", "Mathematics - Calculus/Linear Algebra"), ("Mathematics - Applied Track", "Calculus Sequence")],
    "CS 1101": [("Computer Science", "Computer Science Core")],
    "ECON 1020": [("Computer Science", "Liberal Arts Core")],
}
semester_result = planner.plan_semester(chosen_courses_sem2)

chosen_courses_sem3 = {
    "CHEM 1601": [("Computer Science", "Science")],
    "CHEM 1601L": [("Computer Science", "Science")],
    "CS 2201": [("Computer Science", "Computer Science Core")],
    "CS 2212": [("Computer Science", "Computer Science Core")],
    "ECON 3012": [("Computer Science", "Liberal Arts Core")],
}
semester_result = planner.plan_semester(chosen_courses_sem3)

chosen_courses_sem4 = {
    "MATH 2300": [("Computer Science", "Mathematics - Calculus/Linear Algebra"), ("Mathematics - Applied Track", "Calculus Sequence")],
    "CS 2281": [("Computer Science", "Computer Science Core")],
    "CS 2281L": [("Computer Science", "Computer Science Core")],
    "CS 3251": [("Computer Science", "Computer Science Core")],
    "CS 1151": [("Computer Science", "Liberal Arts Core")],
    "ECON 3022": [("Computer Science", "Liberal Arts Core")]
}
semester_result = planner.plan_semester(chosen_courses_sem4)

chosen_courses_sem5 = {
    "MATH 2820": [("Computer Science", "Mathematics - Statistics/Probability")],
    "CS 3270": [("Computer Science", "Computer Science Core")],
    "CS 3281": [("Computer Science", "Computer Science Core")],
    "MATH 2600": [("Computer Science", "Mathematics - Calculus/Linear Algebra"), ("Mathematics - Applied Track", "Linear Algebra and Differential Equations")],
    "MATH 2420": [("Computer Science", "Open Electives"), ("Mathematics - Applied Track", "Linear Algebra and Differential Equations")]
}
semester_result = planner.plan_semester(chosen_courses_sem5)

chosen_courses_sem6 = {
    "CS 3250": [("Computer Science", "Computer Science Core")],
    "MATH 3330": [("Computer Science", "Open Electives"), ("Mathematics - Applied Track", "Upper-Level Mathematics")],
    "CS 4262": [("Computer Science", "Computer Science Depth")],
    "CS 3255": [("Computer Science", "Technical Electives")],
    "CS 4266": [("Computer Science", "Technical Electives")]
}
semester_result = planner.plan_semester(chosen_courses_sem6)

chosen_courses_sem7 = {
    "CS 4959": [("Computer Science", "Computer Science Seminar")],
    "CS 4247": [("Computer Science", "Computer Science Depth")],
    "CS 4260": [("Computer Science", "Computer Science Depth")],
    "CS 4267": [("Computer Science", "Computer Science Depth")],
    "MATH 3670": [("Computer Science", "Open Electives"), ("Mathematics - Applied Track", "Upper-Level Mathematics")]
}
semester_result = planner.plan_semester(chosen_courses_sem7)

chosen_courses_sem8 = {
    "CS 4269": [("Computer Science", "Computer Science Project")],
    "MATH 3640": [("Computer Science", "Open Electives"), ("Mathematics - Applied Track", "Upper-Level Mathematics")],
    "MATH 4630":  [("Computer Science", "Open Electives"), ("Mathematics - Applied Track", "Upper-Level Mathematics")],
    "ECE 4354": [("Computer Science", "Computer Science Depth")],
    "MATH 3700": [("Computer Science", "Open Electives"), ("Mathematics - Applied Track", "Upper-Level Mathematics")]
}
semester_result = planner.plan_semester(chosen_courses_sem8)

print("\nSEMESTER 9: Getting Recommendations")
planner.advance_semester()
recommendations = planner.get_recommendations()

print(f"\n=== Semester 8 Results ===")
print(f"Plan valid: {semester_result['plan_valid']}")
print(f"Assignment results: {semester_result['assignment_results']}")
if not semester_result['plan_valid']:
    print("Plan has validation errors:")
    for error in semester_result['validation_result']['errors']:
        print(f"  - {error}")

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

