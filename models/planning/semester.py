from typing import List, Optional, Dict, Any
from models.courses.course import Course

class Semester:
    """
    Immutable data container representing a single academic term.
    Holds metadata and a list of planned Course objects. No scheduling logic.
    """
    MAX_CREDITS = 18

    def __init__(self, season: str, year: int, planned_courses: Optional[List[Course]] = None):
        self.season = season
        self.year = year
        self.planned_courses = planned_courses or []

    @property
    def term_id(self) -> str:
        return f"{self.season} {self.year}"

    def __repr__(self):
        return (
            f"<Semester {self.term_id}, courses={len(self.planned_courses)}, max_credits={self.MAX_CREDITS}>"
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'season': self.season,
            'year': self.year,
            'planned_courses': [c.to_dict() for c in self.planned_courses],
            'max_credits': self.MAX_CREDITS
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], course_loader) -> 'Semester':
        planned_courses = [course_loader(c) for c in data.get('planned_courses', [])]
        return cls(
            season=data['season'],
            year=data['year'],
            planned_courses=planned_courses
        ) 