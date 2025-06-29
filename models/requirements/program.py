from typing import List, Optional, Literal
from .category import RequirementCategory
from models.courses.course import Course

class Program:
    """
    Represents a major or minor program.
    """

    def __init__(self, name: str, type: Literal["major", "minor"], total_credits: int, categories: Optional[List[RequirementCategory]] = None, notes: Optional[str] = None):
        self.name = name
        self.type = type
        self.total_credits = total_credits
        self.categories = categories or []
        self.notes = notes

    def get_category(self, category_name: str) -> Optional[RequirementCategory]:
        for category in self.categories:
            if category.category == category_name:
                return category
        return None
    
    def total_required_credits(self) -> int:
        return sum(cat.min_credits for cat in self.categories)
    
    def is_valid(self) -> bool:
        return self.total_required_credits() <= self.total_credits
    
    def progress(self, completed_courses: List[Course]) -> dict:
        category_progress = []
        total_earned = 0
        all_categories_complete = True

        for category in self.categories:
            cat_progress = category.progress(completed_courses)
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
    
    def get_completed_courses(self, completed_courses: List[Course]) -> List[Course]:
        """Returns all completed courses that satisfy any requirement in the program."""
        all_completed = []
        for category in self.categories:
            try:
                cat_completed = category.get_completed_courses(completed_courses)
                all_completed.extend(cat_completed)
            except Exception as e:
                print(f"Warning: Error getting completed courses for category {category.category}: {e}")
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
