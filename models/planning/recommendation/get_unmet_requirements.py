from typing import List, Dict, Tuple
from models.requirements.program import Program
from models.requirements.requirement_types.requirement import Requirement
from models.courses.course import Course

def get_unmet_requirements(programs: List[Program], completed_courses: List[Course]) -> Dict[Tuple[str, str], List[Requirement]]:
    """
    Given a list of Program objects and a list of completed Course objects,
    return a dict mapping (program_name, category_name) to a list of unmet requirement objects for that category in that program.
    Only checks individual requirement satisfaction, not category credit totals.
    """
    unmet = {}
    for program in programs:
        for category in program.categories:
            unmet_reqs = []
            for req in category.requirements:
                # Use satisfied_credits as the satisfaction check
                try:
                    is_satisfied = req.satisfied_credits(completed_courses) > 0
                except Exception:
                    is_satisfied = False
                if not is_satisfied:
                    unmet_reqs.append(req)
            if unmet_reqs:
                unmet[(program.name, category.category)] = unmet_reqs
    return unmet 