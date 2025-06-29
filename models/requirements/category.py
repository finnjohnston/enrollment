from typing import List, Optional, Sequence
from models.requirements.requirement_types.requirement import Requirement
from models.requirements.restrictions.group import RestrictionGroup
from models.courses.course import Course

class RequirementCategory:
    """
    Represents a labeled section of a program.
    """

    def __init__(self, category: str, min_credits: int, requirements: Optional[Sequence[Requirement]] = None, restrictions: Optional[RestrictionGroup] = None, notes: Optional[str] = None):
        self.category = category
        self.min_credits = min_credits
        self.requirements = list(requirements) if requirements else []
        self.restrictions = restrictions
        self.notes = notes

    def progress(self, completed_courses: List[Course]) -> dict:
        earned = 0
        for req in self.requirements:
            try:
                earned += req.satisfied_credits(completed_courses)
            except Exception as e:
                print(f"Warning: Error calculating satisfied credits for requirement {req}: {e}")
                continue

        restriction_results = []
        restrictions_satisfied = True

        if self.restrictions and hasattr(self.restrictions, "restrictions"):
            for restriction in self.restrictions.restrictions:
                try:
                    result = restriction.is_satisfied_by(completed_courses)
                    restriction_results.append({
                        "type": restriction.__class__.__name__,
                        "description": restriction.describe(),
                        "satisfied": result
                    })
                    if not result:
                        restrictions_satisfied = False
                except Exception as e:
                    print(f"Warning: Error checking restriction {restriction}: {e}")
                    restrictions_satisfied = False

        complete = earned >= self.min_credits and restrictions_satisfied

        return {
            "category": self.category,
            "required_credits": self.min_credits,
            "earned_credits": earned,
            "complete": complete,
            "restrictions": restriction_results if restriction_results else None,
            "notes": self.notes
        }

    def get_completed_courses(self, completed_courses: List[Course]) -> List[Course]:
        """Returns completed courses that satisfy any requirement in this category."""
        all_completed = []
        for req in self.requirements:
            try:
                req_completed = req.get_completed_courses(completed_courses)
                all_completed.extend(req_completed)
            except Exception as e:
                print(f"Warning: Error getting completed courses for requirement {req}: {e}")
                continue
        
        # Remove duplicates by course code
        seen_codes = set()
        unique_courses = []
        for course in all_completed:
            code = course.get_course_code()
            if code and code not in seen_codes:
                seen_codes.add(code)
                unique_courses.append(course)
        
        return unique_courses
    
    def describe(self) -> str:
        lines = [f"Category: {self.category}", f"Minimum Credits: {self.min_credits}"]

        for req in self.requirements:
            try:
                lines.append(f"  - {req.describe()}")
            except Exception as e:
                lines.append(f"  - [Error describing requirement: {e}]")

        if self.restrictions: 
            lines.append("Restrictions:")
            try:
                for r in self.restrictions.describe_all():
                    lines.append(f"  - {r}")
            except Exception as e:
                lines.append(f"  - [Error describing restrictions: {e}]")

        if self.notes:
            lines.append(f"Notes: {self.notes}")

        return "\n".join(lines)