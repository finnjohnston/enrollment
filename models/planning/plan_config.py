from typing import List, Dict, Any
from models.requirements.program import Program
from models.courses.course import Course

class PlanConfig:
    """
    Central configuration/state for the planning engine.
    Holds all information about a student's academic plan at a point in time.
    """
    def __init__(self, programs: List[Program], completed_courses: List[Course]):
        self.programs = programs
        self.completed_courses = completed_courses

    def __repr__(self):
        return (
            f"<PlanConfig programs={len(self.programs)} completed_courses={len(self.completed_courses)}>"
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'programs': [self._program_to_dict(p) for p in self.programs],
            'completed_courses': [c.to_dict() for c in self.completed_courses]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], program_loader, course_loader) -> 'PlanConfig':

        programs = [program_loader(p) for p in data.get('programs', [])]
        completed_courses = [course_loader(c) for c in data.get('completed_courses', [])]
        return cls(programs, completed_courses)

    def validate(self) -> bool:
        if not self.programs or not isinstance(self.programs, list):
            return False
        if not isinstance(self.completed_courses, list):
            return False
        return True

    @staticmethod
    def _program_to_dict(program: Program) -> Dict[str, Any]:
        return {'description': program.describe()} 