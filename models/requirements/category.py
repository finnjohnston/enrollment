from typing import List, Optional, Sequence, Dict, Tuple
from models.requirements.requirement_types.requirement import Requirement
from models.requirements.requirement_types.course_filter import CourseFilterRequirement
from models.requirements.requirement_types.course_options import CourseOptionsRequirement
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

    def progress(self, completed_courses: List[Course], requirement_assignments: Optional[Dict[str, List[Tuple[str, str]]]] = None) -> dict:
        earned = 0
        used_courses = set()
        
        # Filter completed courses to only those assigned to this category
        assigned_courses = []
        if requirement_assignments:
            for course in completed_courses:
                course_code = course.get_course_code()
                if course_code and course_code in requirement_assignments:
                    # Check if this course is assigned to this specific category
                    for program_name, assigned_category in requirement_assignments[course_code]:
                        if assigned_category == self.category:
                            assigned_courses.append(course)
                            break
        else:
            # If no assignments provided, use all completed courses (backward compatibility)
            assigned_courses = completed_courses
        
        for req in self.requirements:
            try:
                matching = req.get_completed_courses(assigned_courses)
                # Only consider unused courses
                unused_matching = [course for course in matching if course.get_course_code() not in used_courses]
                credits_needed = getattr(req, 'min_credits', None)
                if credits_needed is not None and credits_needed > 0:
                    credits_accum = 0
                    for course in unused_matching:
                        code = course.get_course_code()
                        if code not in used_courses:
                            ch = course.get_credit_hours()
                            if credits_accum < credits_needed:
                                earned += ch
                                credits_accum += ch
                                used_courses.add(code)
                            if credits_accum >= credits_needed:
                                break
                else:
                    # For requirements without min_credits, just add all unused matching courses
                    for course in unused_matching:
                        code = course.get_course_code()
                        if code not in used_courses:
                            earned += course.get_credit_hours()
                            used_courses.add(code)
            except Exception as e:
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