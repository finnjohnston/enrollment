from typing import Dict, Optional, List

class CategoryAssignmentManager:
    """
    Manages assignment of completed or planned courses to requirement categories.
    Allows querying, assigning, and listing assignments for use in planning and recommendation.
    """
    def __init__(self):
        # course_code -> category
        self.assignments: Dict[str, str] = {}

    def assign(self, course_code: str, category: str) -> None:
        self.assignments[course_code] = category

    def get_category(self, course_code: str) -> Optional[str]:
        return self.assignments.get(course_code)

    def is_assigned(self, course_code: str) -> bool:
        return course_code in self.assignments

    def get_courses_for_category(self, category: str) -> List[str]:
        return [c for c, cat in self.assignments.items() if cat == category]

    def unassign(self, course_code: str) -> None:
        if course_code in self.assignments:
            del self.assignments[course_code]

    def clear(self) -> None:
        self.assignments.clear()

    def get_all_assignments(self) -> Dict[str, str]:
        return dict(self.assignments) 