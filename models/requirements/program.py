from typing import List, Optional, Literal, Dict
from .category import RequirementCategory
from models.courses.course import Course

class Program:
    """
    Represents a major or minor program.
    """

    def __init__(self, name: str, type: Literal["major", "minor"], total_credits: int, categories: Optional[List[RequirementCategory]] = None, notes: Optional[str] = None, school: Optional[str] = None):
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Program name must be a non-empty string")
        if not isinstance(type, str) or type not in ("major", "minor"):
            raise ValueError("Program type must be 'major' or 'minor'")
        if not isinstance(total_credits, int) or total_credits <= 0:
            raise ValueError("total_credits must be a positive integer")
        if categories is not None and not all(isinstance(cat, RequirementCategory) for cat in categories):
            raise ValueError("All categories must be RequirementCategory instances")
        self.name = name
        self.type = type
        self.total_credits = total_credits
        self.categories = categories or []
        self.notes = notes
        self.school = school

    def get_category(self, category_name: str) -> Optional[RequirementCategory]:
        for category in self.categories:
            if category.category == category_name:
                return category
        return None
    
    def total_required_credits(self) -> int:
        return sum(cat.min_credits for cat in self.categories)
    
    def is_valid(self) -> bool:
        return self.total_required_credits() <= self.total_credits
    
    def progress(self, completed_courses: List[Course], requirement_assignments: Optional[Dict[str, list]] = None) -> dict:
        category_progress = []
        total_earned = 0
        all_categories_complete = True

        for category in self.categories:
            # Only use courses explicitly assigned to this (program, category)
            if requirement_assignments:
                assigned_courses = []
                for course in completed_courses:
                    code = course.get_course_code()
                    if code and code in requirement_assignments:
                        # requirement_assignments[code] is a list of (program_name, category_name)
                        for prog, cat in requirement_assignments[code]:
                            if prog == self.name and cat == category.category:
                                assigned_courses.append(course)
                                break
                cat_progress = category.progress(assigned_courses, None)
            else:
                cat_progress = category.progress(completed_courses, None)
            category_progress.append(cat_progress)
            total_earned += cat_progress.get("earned_credits", 0)
            if not cat_progress.get("complete", False):
                all_categories_complete = False

        program_complete = (
            total_earned >= self.total_credits and all_categories_complete
        )

        return {
            "program": self.name,
            "type": self.type,
            "total_required": self.total_credits,
            "total_earned": total_earned,
            "complete": program_complete,
            "categories": category_progress,
            "notes": self.notes
        }
    
    def describe(self) -> str:
        lines = [
            f"{self.name} ({self.type.title()})",
            f"Total Credits Required: {self.total_credits}",
            ""
        ]
        for cat in self.categories:
            lines.append(cat.describe())
            lines.append("")

        if self.notes:
            lines.append(f"Notes: {self.notes}")

        return "\n".join(lines)
