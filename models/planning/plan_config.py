from typing import List, Dict, Any
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

    def to_dict(self) -> Dict[str, Any]:
        return {
            'programs': [self._program_to_dict(p) for p in self.programs],
            'completed_courses': [c.to_dict() for c in self.completed_courses],
            'start_season': self.start_season,
            'start_year': self.start_year,
            'num_years': self.num_years
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], program_loader, course_loader) -> 'PlanConfig':
        programs = [program_loader(p) for p in data.get('programs', [])]
        completed_courses = [course_loader(c) for c in data.get('completed_courses', [])]
        start_season = data['start_season']
        start_year = data['start_year']
        num_years = data['num_years']
        return cls(programs, completed_courses, start_season, start_year, num_years)

    def validate(self) -> bool:
        if not self.programs or not isinstance(self.programs, list):
            return False
        if not isinstance(self.completed_courses, list):
            return False
        if not isinstance(self.start_season, str) or not self.start_season:
            return False
        if not isinstance(self.start_year, int) or self.start_year < 1900:
            return False
        if not isinstance(self.num_years, int) or self.num_years <= 0:
            return False
        return True

    @staticmethod
    def _program_to_dict(program: Program) -> Dict[str, Any]:
        return {'description': program.describe()} 