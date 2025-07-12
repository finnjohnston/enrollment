from typing import List
from models.requirements.program import Program
from models.courses.course import Course

class PlanConfig:
    """
    Central configuration/state for the planning engine.
    Holds all information about a student's academic plan at a point in time, including
    start term and planning horizon.
    """
    def __init__(self, programs: List[Program], completed_courses: List[Course], start_season: str, start_year: int, num_years: int):
        self.programs = programs
        self.completed_courses = completed_courses
        self.start_season = start_season
        self.start_year = start_year
        self.num_years = num_years

    def __repr__(self):
        return (
            f"<PlanConfig programs={len(self.programs)} completed_courses={len(self.completed_courses)} "
            f"start={self.start_season} {self.start_year} years={self.num_years}>"
        )

 