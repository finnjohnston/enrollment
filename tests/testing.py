import json
import sys
from pathlib import Path
import types

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.courses.catalog import Catalog
from models.requirements.program_builder import ProgramBuilder
from models.planning.semester import Semester
from models.planning.academic_planner import AcademicPlanner

# Load data
with open("data/courses/parsed.json", 'r') as f:
    courses_data = json.load(f)
    catalog = Catalog(courses_data)

with open("data/programs/majors.json", 'r') as f:
    majors_data = json.load(f)
    cs_major_data = majors_data[0]
    cs_major = ProgramBuilder.build_program(cs_major_data)

# Initialize academic planner
start_semester = Semester("Fall", 2024)
planner = AcademicPlanner(catalog, [cs_major], start_semester)

print("=== Academic Planner Test ===\n")

# Semester 1
print("SEMESTER 1: Planning Fall 2024")
chosen_courses_sem1 = {
    "PHYS 1601": "Science",
    "PHYS 1601L": "Science",
    "MATH 1300": "Mathematics - Calculus/Linear Algebra",
    "ES 1401": "Introduction to Engineering",
    "ES 1402": "Introduction to Engineering",
    "ES 1403": "Introduction to Engineering"
}
planner.plan_semester(chosen_courses_sem1)

# Semester 2
print("\nSEMESTER 2: Planning Spring 2025")
planner.advance_semester()
chosen_courses_sem2 = {
    "PHYS 1602": "Science",
    "PHYS 1602L": "Science",
    "MATH 1301": "Mathematics - Calculus/Linear Algebra",
    "CS 1101": "Computer Science Core"
}
planner.plan_semester(chosen_courses_sem2)

# Semester 3
print("\nSEMESTER 3: Planning Fall 2025")
planner.advance_semester()
chosen_courses_sem3 = {
    "CHEM 1601": "Science",
    "CHEM 1601L": "Science",
    "CS 2201": "Computer Science Core",
    "CS 2212": "Computer Science Core"
}
planner.plan_semester(chosen_courses_sem3)

# Semester 4
print("\nSEMESTER 4: Planning Spring 2026")
planner.advance_semester()
chosen_courses_sem4 = {
    "MATH 2300": "Mathematics - Calculus/Linear Algebra",
    "CS 2281": "Computer Science Core",
    "CS 2281L": "Computer Science Core",
    "CS 3251": "Computer Science Core",
    "CS 1151": "Liberal Arts Core"
}
planner.plan_semester(chosen_courses_sem4)

# Semester 5
print("\nSEMESTER 5: Planning Fall 2026")
planner.advance_semester()
chosen_courses_sem5 = {
    "MATH 2820": "Mathematics - Statistics/Probability",
    "CS 3270": "Computer Science Core",
    "CS 3281": "Computer Science Core"
}
planner.plan_semester(chosen_courses_sem5)

# Semester 6
print("\nSEMESTER 6: Planning Spring 2027")
planner.advance_semester()
chosen_courses_sem6 = {
    "MATH 2410": "Mathematics - Calculus/Linear Algebra",
    "CS 3250": "Computer Science Core",
    "CS 4266": "Computer Science Depth"
}
planner.plan_semester(chosen_courses_sem6)

# Semester 7
print("\nSEMESTER 7: Planning Fall 2027")
planner.advance_semester()
chosen_courses_sem7 = {
    "CS 4959": "Computer Science Seminar",
    "CS 4262": "Computer Science Depth",
    "CS 4260": "Computer Science Depth",
    "CS 4267": "Computer Science Depth"
}
planner.plan_semester(chosen_courses_sem7)

# Semester 8
print("\nSEMESTER 8: Planning Spring 2028")
planner.advance_semester()
chosen_courses_sem8 = {
    "CS 4269": "Computer Science Project",
    "CS 4247": "Computer Science Depth"
}
planner.plan_semester(chosen_courses_sem8)

# Get final recommendations
print("\nSEMESTER 9: Final Recommendations")
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

