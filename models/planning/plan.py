from typing import List, Optional, Dict, Any
from models.planning.semester import Semester
from models.courses.course import Course

class Plan:
    """
    Structured container representing a student's full academic roadmap.
    Holds an ordered sequence of Semester objects, each with planned courses.
    Provides methods to interact with the timeline, but does not enforce requirements or calculate progress.
    """
    def __init__(self, semesters: List[Semester]):
        self.semesters = semesters

    def get_semester(self, season: str, year: int) -> Optional[Semester]:
        for sem in self.semesters:
            if sem.season == season and sem.year == year:
                return sem
        return None

    def get_semester_by_index(self, index: int) -> Semester:
        return self.semesters[index]

    def all_semesters(self) -> List[Semester]:
        return self.semesters

    def add_course_to_term(self, course: Course, season: str, year: int):
        sem = self.get_semester(season, year)
        if sem is not None:
            if course not in sem.planned_courses:
                sem.planned_courses.append(course)

    def remove_course_from_term(self, course: Course, season: str, year: int):
        sem = self.get_semester(season, year)
        if sem is not None:
            if course in sem.planned_courses:
                sem.planned_courses.remove(course)

    def clear_term(self, season: str, year: int):
        sem = self.get_semester(season, year)
        if sem is not None:
            sem.planned_courses.clear()

    def all_planned_courses(self) -> List[Course]:
        return [course for sem in self.semesters for course in sem.planned_courses]

    def to_dict(self) -> Dict[str, Any]:
        return {
            'semesters': [sem.to_dict() for sem in self.semesters]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], course_loader, semester_loader=None) -> 'Plan':
        if semester_loader is None:
            from models.planning.semester import Semester
            semester_loader = lambda d: Semester.from_dict(d, course_loader)
        semesters = [semester_loader(s) for s in data.get('semesters', [])]
        return cls(semesters)

    def __repr__(self):
        return f"<Plan semesters={len(self.semesters)} total_courses={sum(len(s.planned_courses) for s in self.semesters)} >" 