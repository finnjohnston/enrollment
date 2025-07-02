from models.courses.course import Course
from typing import List, Optional, cast
from .requirement import Requirement
from .course_list import CourseListRequirement
from .course_options import CourseOptionsRequirement
from .course_filter import CourseFilterRequirement

class CompoundRequirement(Requirement):
    """
    Supports OR between groups of courses
    """

    def __init__(self, options: List[Requirement], restrictions=None):
        super().__init__(restrictions=restrictions)
        self.options = options

    def describe(self):
        return "Choose one of the following sequences:\n" + "\n".join(
            f"  - {opt.describe()}" for opt in self.options
        )

    def satisfied_credits(self, completed_courses: List[Course]) -> int:
        max_credits = 0
        for opt in self.options:
            if isinstance(opt, CourseListRequirement):
                earned_credits = sum(
                    course.get_credit_hours()
                    for course in completed_courses
                    if course.get_course_code() in opt.courses
                )
                max_credits = max(max_credits, earned_credits)
            elif isinstance(opt, CourseOptionsRequirement):
                codes = {c.get_course_code() for c in completed_courses}
                matching_courses = [c for c in completed_courses if c.get_course_code() in opt.options]
                if len(matching_courses) >= opt.min_required:
                    earned_credits = opt.satisfied_credits(completed_courses)
                    max_credits = max(max_credits, earned_credits)
            elif isinstance(opt, CourseFilterRequirement):
                earned_credits = opt.satisfied_credits(completed_courses)
                if earned_credits >= (opt.min_credits or 0):
                    max_credits = max(max_credits, earned_credits)
            else:
                earned_credits = opt.satisfied_credits(completed_courses)
                max_credits = max(max_credits, earned_credits)
        return max_credits

    def get_possible_courses(self, courses: List[Course], completed_courses: Optional[List[Course]] = None) -> List[Course]:
        from models.courses.course import Course
        catalog_lookup = {c.get_course_code(): c for c in courses if hasattr(c, 'get_course_code')}
        completed_codes = set()
        if completed_courses is not None:
            completed_codes = {c.get_course_code() for c in completed_courses if hasattr(c, 'get_course_code')}
        # For each sequence, find the length of the matching prefix
        progress_list = []  # (progress, seq)
        for opt in self.options:
            if hasattr(opt, 'courses'):
                seq = opt.courses
                progress = 0
                for code in seq:
                    if code in completed_codes:
                        progress += 1
                    else:
                        break
                progress_list.append((progress, seq))
        if not progress_list:
            return []
        # Find the maximum progress value
        max_progress = max(progress for progress, seq in progress_list)
        # Find all sequences with this max progress
        best_seqs = [seq for progress, seq in progress_list if progress == max_progress]
        # If the student has diverged (taken a unique course in only one sequence), only recommend from that sequence
        if len(best_seqs) > 1 and max_progress > 0:
            # Check if the last completed course in each sequence is the same
            last_courses = set(seq[max_progress-1] for seq in best_seqs if max_progress <= len(seq))
            if len(last_courses) == 1:
                # Still on shared prefix, recommend next in all
                pass
            else:
                # Diverged, only recommend from the sequence(s) where the student has taken a unique course
                # Find which sequence(s) the student has diverged into
                diverged_seqs = []
                for seq in best_seqs:
                    if max_progress <= len(seq):
                        last = seq[max_progress-1]
                        # If this last course is not in the same position in any other sequence, it's unique
                        if all((other is seq or (max_progress > 1 and other[max_progress-1] != last)) for other in best_seqs):
                            diverged_seqs.append(seq)
                if diverged_seqs:
                    best_seqs = diverged_seqs
        # Recommend the next course in each best sequence, if not already completed
        next_courses = set()
        for seq in best_seqs:
            if max_progress < len(seq):
                code = seq[max_progress]
                if code not in completed_codes and code in catalog_lookup:
                    next_courses.add(catalog_lookup[code])
        if next_courses:
            return list(next_courses)
        # If no progress, recommend the first course in each sequence not started
        first_courses = []
        for opt in self.options:
            if hasattr(opt, 'courses'):
                seq = opt.courses
                if seq and seq[0] in catalog_lookup and seq[0] not in completed_codes:
                    first_courses.append(catalog_lookup[seq[0]])
        if first_courses:
            return first_courses
        return []