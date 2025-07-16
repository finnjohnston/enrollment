from collections import defaultdict
from typing import List, Optional, Dict, Any
from .course import Course
from db.database import SessionLocal
from db.models.course import Course as ORMCourse

class Catalog:
    """
    Data structure for course storage and fast indexed access.
    """

    def __init__(self):
        session = SessionLocal()
        orm_courses = session.query(ORMCourse).all()
        self.courses: List[Course] = [Course.from_orm(oc) for oc in orm_courses]
        session.close()

        # Core direct lookups
        self.by_course_code: Dict[str, Course] = {}
        self.by_title: Dict[str, Course] = {}

        # Primary hierarchy: subject -> level -> course_number -> course
        self.by_subject_number: Dict[str, Dict[int, Dict[str, Course]]] = defaultdict(lambda: defaultdict(dict))

        # Additional groupings
        self.by_subject: Dict[str, List[Course]] = defaultdict(list)
        self.by_level: Dict[int, List[Course]] = defaultdict(list)
        self.by_credits: Dict[Any, List[Course]] = defaultdict(list)
        self.by_axle: Dict[str, List[Course]] = defaultdict(list)

        self._build_indexes()

    def _build_indexes(self):
        for course in self.courses:
            # Normalize keys
            code = (course.course_code or "").strip().upper()
            title = (course.title or "").strip().lower()

            # Direct lookups
            if code:
                self.by_course_code[code] = course
            if title:
                self.by_title[title] = course

            # Primary nested index
            subj = course.subject_code
            num = course.course_number
            lvl = course.level
            if subj and num and lvl is not None:
                self.by_subject_number[subj][lvl][num] = course

            # Groupings
            if subj:
                self.by_subject[subj].append(course)
            if lvl is not None:
                self.by_level[lvl].append(course)
            if course.credits is not None:
                try:
                    credits = int(course.credits)
                except (ValueError, TypeError):
                    credits = course.credits
                self.by_credits[credits].append(course)
            if course.axle:
                axles = course.axle if isinstance(course.axle, list) else [course.axle]
                for axle in axles:
                    if axle:
                        self.by_axle[axle].append(course)

    # === Access Methods ===

    def get_by_course_code(self, code: str) -> Optional[Course]:
        return self.by_course_code.get(code.strip().upper())
    
    def get_by_title(self, title: str) -> Optional[Course]:
        return self.by_title.get(title.strip().lower())
    
    def get_by_subject_and_number(self, subject: str, number: str) -> Optional[Course]:
        levels = self.by_subject_number.get(subject, {})
        for level_courses in levels.values():
            if number in level_courses:
                return level_courses[number]
        return None
    
    def get_by_subject(self, subject: str) -> List[Course]:
        return self.by_subject.get(subject, [])
        
    def get_by_level(self, level: int, subject: Optional[str] = None) -> List[Course]:
        if subject:
            return [
                course for course in self.by_subject.get(subject, [])
                if course.level == level
            ]
        return self.by_level.get(level, [])
    
    def get_by_credits(self, credits: int) -> List[Course]:
        return self.by_credits.get(credits, [])

    def get_by_axle(self, axle: str) -> List[Course]:
        return self.by_axle.get(axle, [])
    
    # === Utility ===

    def get_all_subjects(self) -> List[str]:
        return list(self.by_subject.keys())

    def get_all_levels(self) -> List[int]:
        return sorted(self.by_level.keys())

    def get_all_axles(self) -> List[str]:
        return list(self.by_axle.keys())