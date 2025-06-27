from typing import List, Set, Dict, Optional

class PrerequisiteLogic:
    """
    Handles prerequisite logic for a course, including AND/OR groupings and satisfaction checking.
    """
    def __init__(self, groups: List[List[str]]):
        """groups: AND-of-ORs structure, e.g. [['MATH 2501'], ['MATH 2300', 'MATH 2310']]"""
        self.groups = groups

    # --- Core Logic Evaluation ---
    def is_satisfied(self, completed_courses: Set[str]) -> bool:
        # All AND groups must have at least one course satisfied
        for group in self.groups:
            if not any(course in completed_courses for course in group):
                return False
        return True

    def is_partially_satisfied(self, completed_courses: Set[str]) -> bool:
        return any(any(course in completed_courses for course in group) for group in self.groups)

    def get_satisfaction_percentage(self, completed_courses: Set[str]) -> float:
        if not self.groups:
            return 1.0
        satisfied = sum(1 for group in self.groups if any(course in completed_courses for course in group))
        return satisfied / len(self.groups)

    def get_satisfaction_details(self, completed_courses: Set[str], graph: Optional[object] = None) -> Dict:
        details = {
            'total_groups': len(self.groups),
            'satisfied_groups': sum(1 for group in self.groups if any(course in completed_courses for course in group)),
            'missing_groups': self.get_missing_requirements(completed_courses),
            'is_satisfied': self.is_satisfied(completed_courses),
            'satisfaction_percentage': self.get_satisfaction_percentage(completed_courses),
        }
        return details

    # --- Missing Requirements Analysis ---
    def get_missing_requirements(self, completed_courses: Set[str]) -> List[List[str]]:
        return [group for group in self.groups if not any(course in completed_courses for course in group)]

    def get_missing_courses(self, completed_courses: Set[str]) -> Set[str]:
        missing = set()
        for group in self.get_missing_requirements(completed_courses):
            missing.update(group)
        return missing

    def get_minimum_remaining(self, completed_courses: Set[str]) -> int:
        return len(self.get_missing_requirements(completed_courses))

    def get_blocking_courses(self, completed_courses: Set[str], graph: Optional[object] = None) -> List[str]:
        # Return one course from each missing group
        return [group[0] for group in self.get_missing_requirements(completed_courses) if group]

    # --- Logic Structure Analysis ---
    def get_and_groups(self) -> List[List[str]]:
        return self.groups
    def get_or_groups(self) -> List[List[str]]:
        return self.groups
    def get_all_courses(self) -> Set[str]:
        return set(c for group in self.groups for c in group)
    def get_logic_depth(self) -> int:
        return 2  # AND-of-ORs
    def get_logic_complexity(self) -> float:
        return float(len(self.groups))

    # --- Alternative Path Analysis ---
    def get_all_satisfying_combinations(self, completed_courses: Set[str]) -> List[List[str]]:
        # Return all combinations of one course per AND group
        from itertools import product
        if not self.groups:
            return []
        return [list(combo) for combo in product(*self.groups)]

    def get_optimal_satisfaction_path(self, completed_courses: Set[str]) -> List[str]:
        # Return one missing course from each group
        return [group[0] for group in self.get_missing_requirements(completed_courses) if group]

    def get_alternative_paths(self, completed_courses: Set[str]) -> List[List[str]]:
        # All possible ways to satisfy the logic
        return self.get_all_satisfying_combinations(completed_courses)

    def get_flexible_requirements(self) -> List[List[str]]:
        # OR groups with more than one option
        return [group for group in self.groups if len(group) > 1]

    def get_rigid_requirements(self) -> List[str]:
        # AND groups with only one option
        return [group[0] for group in self.groups if len(group) == 1]

    def get_critical_courses(self) -> Set[str]:
        # Courses that appear in every AND group
        if not self.groups:
            return set()
        from functools import reduce
        return set.intersection(*(set(group) for group in self.groups)) if self.groups else set()

    # --- Prerequisite-Specific Methods ---
    def is_prereq_satisfied(self, completed_courses: Set[str]) -> bool:
        return self.is_satisfied(completed_courses)
    
    def get_prereq_missing(self, completed_courses: Set[str]) -> List[List[str]]:
        return self.get_missing_requirements(completed_courses)
    
    def get_prereq_impact(self, completed_courses: Set[str], graph: Optional[object] = None) -> List[str]:
        # Integration with graph for dependents should be handled externally
        return []

    # --- Logic Validation & Debugging ---
    def validate_logic(self) -> bool:
        return all(isinstance(group, list) and all(isinstance(c, str) for c in group) for group in self.groups)
    
    def has_redundant_conditions(self) -> bool:
        # Check for duplicate courses in groups
        seen = set()
        for group in self.groups:
            for c in group:
                if c in seen:
                    return True
                seen.add(c)
        return False
    
    def has_conflicting_conditions(self) -> bool:
        # No way to satisfy if any group is empty
        return any(len(group) == 0 for group in self.groups)
    
    def explain_satisfaction(self, completed_courses: Set[str]) -> str:
        if self.is_satisfied(completed_courses):
            return "All prerequisites satisfied."
        missing = self.get_missing_requirements(completed_courses)
        return f"Missing: {missing}"
    
    def get_unsatisfied_reasons(self, completed_courses: Set[str]) -> List[str]:
        return [f"Missing one of: {group}" for group in self.get_missing_requirements(completed_courses)]

    # --- Logic Transformation ---
    def to_boolean_expression(self) -> str:
        return " AND ".join(["(" + " OR ".join(group) + ")" for group in self.groups])
    
    def to_natural_language(self) -> str:
        return "; ".join([" or ".join(group) for group in self.groups])
    
    def to_dict(self) -> Dict:
        return {'groups': self.groups}
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PrerequisiteLogic':
        return cls(data.get('groups', []))
    
    def combine_with(self, other_logic: 'PrerequisiteLogic', operation: str) -> 'PrerequisiteLogic':
        if operation == 'AND':
            return PrerequisiteLogic(self.groups + other_logic.groups)
        elif operation == 'OR':
            return PrerequisiteLogic([list(set(a + b)) for a, b in zip(self.groups, other_logic.groups)])
        return self
    
    def negate(self) -> 'PrerequisiteLogic':
        # Not implemented
        return self
    
    def substitute(self, course_mapping: Dict[str, str]) -> 'PrerequisiteLogic':
        new_groups = [[course_mapping.get(c, c) for c in group] for group in self.groups]
        return PrerequisiteLogic(new_groups)
    
    def simplify_logic(self) -> 'PrerequisiteLogic':
        # Remove duplicates
        new_groups = [list(set(group)) for group in self.groups]
        return PrerequisiteLogic(new_groups)
   
    def normalize_logic(self) -> 'PrerequisiteLogic':
        return self.simplify_logic()
    
    def minimize_logic(self) -> 'PrerequisiteLogic':
        return self.simplify_logic()

    # --- Program Integration ---
    def satisfies_requirement(self, requirement: object, completed_courses: Set[str]) -> bool:
        return self.is_satisfied(completed_courses)
    
    def get_requirement_contribution(self, requirement: object, completed_courses: Set[str]) -> float:
        return self.get_satisfaction_percentage(completed_courses)
    
    def get_requirement_impact(self, requirement: object) -> float:
        return float(len(self.groups))

    # --- Performance & Optimization ---
    def cache_evaluation_results(self, completed_courses: Set[str], result: bool):
        pass
    
    def clear_cache(self):
        pass
    
    def get_cache_stats(self) -> Dict:
        return {}
    
    def optimize_for_evaluation(self) -> 'PrerequisiteLogic':
        return self
    
    def precompute_partial_results(self) -> Dict:
        return {}

    # --- Utility Methods ---
    def get_logic_type(self) -> str:
        return "prerequisite"

class CorequisiteLogic:
    """
    Handles corequisite logic for a course, including AND/OR groupings and satisfaction checking.
    """
    def __init__(self, groups: List[List[str]]):
        self.groups = groups

    # --- Core Logic Evaluation ---
    def is_satisfied(self, completed_courses: Set[str], enrolled_courses: Set[str]) -> bool:
        # All AND groups must have at least one course satisfied in completed or enrolled
        all_courses = completed_courses | enrolled_courses
        for group in self.groups:
            if not any(course in all_courses for course in group):
                return False
        return True

    def is_partially_satisfied(self, completed_courses: Set[str], enrolled_courses: Set[str]) -> bool:
        all_courses = completed_courses | enrolled_courses
        return any(any(course in all_courses for course in group) for group in self.groups)

    def get_satisfaction_percentage(self, completed_courses: Set[str], enrolled_courses: Set[str]) -> float:
        all_courses = completed_courses | enrolled_courses
        if not self.groups:
            return 1.0
        satisfied = sum(1 for group in self.groups if any(course in all_courses for course in group))
        return satisfied / len(self.groups)

    def get_satisfaction_details(self, completed_courses: Set[str], enrolled_courses: Set[str], graph: Optional[object] = None) -> Dict:
        all_courses = completed_courses | enrolled_courses
        details = {
            'total_groups': len(self.groups),
            'satisfied_groups': sum(1 for group in self.groups if any(course in all_courses for course in group)),
            'missing_groups': self.get_missing_requirements(completed_courses, enrolled_courses),
            'is_satisfied': self.is_satisfied(completed_courses, enrolled_courses),
            'satisfaction_percentage': self.get_satisfaction_percentage(completed_courses, enrolled_courses),
        }
        return details

    # --- Missing Requirements Analysis ---
    def get_missing_requirements(self, completed_courses: Set[str], enrolled_courses: Set[str]) -> List[List[str]]:
        all_courses = completed_courses | enrolled_courses
        return [group for group in self.groups if not any(course in all_courses for course in group)]

    def get_missing_courses(self, completed_courses: Set[str], enrolled_courses: Set[str]) -> Set[str]:
        missing = set()
        for group in self.get_missing_requirements(completed_courses, enrolled_courses):
            missing.update(group)
        return missing

    def get_minimum_remaining(self, completed_courses: Set[str], enrolled_courses: Set[str]) -> int:
        return len(self.get_missing_requirements(completed_courses, enrolled_courses))

    def get_blocking_courses(self, completed_courses: Set[str], enrolled_courses: Set[str], graph: Optional[object] = None) -> List[str]:
        return [group[0] for group in self.get_missing_requirements(completed_courses, enrolled_courses) if group]

    # --- Logic Structure Analysis ---
    def get_and_groups(self) -> List[List[str]]:
        return self.groups
    
    def get_or_groups(self) -> List[List[str]]:
        return self.groups
    
    def get_all_courses(self) -> Set[str]:
        return set(c for group in self.groups for c in group)
    
    def get_logic_depth(self) -> int:
        return 2
    
    def get_logic_complexity(self) -> float:
        return float(len(self.groups))

    # --- Alternative Path Analysis ---
    def get_all_satisfying_combinations(self, completed_courses: Set[str], enrolled_courses: Set[str]) -> List[List[str]]:
        from itertools import product
        if not self.groups:
            return []
        return [list(combo) for combo in product(*self.groups)]

    def get_optimal_satisfaction_path(self, completed_courses: Set[str], enrolled_courses: Set[str]) -> List[str]:
        return [group[0] for group in self.get_missing_requirements(completed_courses, enrolled_courses) if group]

    def get_alternative_paths(self, completed_courses: Set[str], enrolled_courses: Set[str]) -> List[List[str]]:
        return self.get_all_satisfying_combinations(completed_courses, enrolled_courses)

    def get_flexible_requirements(self) -> List[List[str]]:
        return [group for group in self.groups if len(group) > 1]

    def get_rigid_requirements(self) -> List[str]:
        return [group[0] for group in self.groups if len(group) == 1]

    def get_critical_courses(self) -> Set[str]:
        if not self.groups:
            return set()
        from functools import reduce
        return set.intersection(*(set(group) for group in self.groups)) if self.groups else set()

    # --- Corequisite-Specific Methods ---
    def is_coreq_satisfied(self, completed_courses: Set[str], enrolled_courses: Set[str]) -> bool:
        return self.is_satisfied(completed_courses, enrolled_courses)
    
    def get_coreq_missing(self, completed_courses: Set[str], enrolled_courses: Set[str]) -> List[List[str]]:
        return self.get_missing_requirements(completed_courses, enrolled_courses)
    
    def can_take_concurrently(self, course_code: str, enrolled_courses: Set[str]) -> bool:
        return course_code in enrolled_courses
    
    def get_concurrent_options(self, enrolled_courses: Set[str]) -> List[str]:
        return [c for group in self.groups for c in group if c in enrolled_courses]

    # --- Logic Validation & Debugging ---
    def validate_logic(self) -> bool:
        return all(isinstance(group, list) and all(isinstance(c, str) for c in group) for group in self.groups)
    
    def has_redundant_conditions(self) -> bool:
        seen = set()
        for group in self.groups:
            for c in group:
                if c in seen:
                    return True
                seen.add(c)
        return False
    
    def has_conflicting_conditions(self) -> bool:
        return any(len(group) == 0 for group in self.groups)
    
    def explain_satisfaction(self, completed_courses: Set[str], enrolled_courses: Set[str]) -> str:
        if self.is_satisfied(completed_courses, enrolled_courses):
            return "All corequisites satisfied."
        missing = self.get_missing_requirements(completed_courses, enrolled_courses)
        return f"Missing: {missing}"
    
    def get_unsatisfied_reasons(self, completed_courses: Set[str], enrolled_courses: Set[str]) -> List[str]:
        return [f"Missing one of: {group}" for group in self.get_missing_requirements(completed_courses, enrolled_courses)]

    # --- Logic Transformation ---
    def to_boolean_expression(self) -> str:
        return " AND ".join(["(" + " OR ".join(group) + ")" for group in self.groups])
    
    def to_natural_language(self) -> str:
        return "; ".join([" or ".join(group) for group in self.groups])
    
    def to_dict(self) -> Dict:
        return {'groups': self.groups}
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CorequisiteLogic':
        return cls(data.get('groups', []))
    
    def combine_with(self, other_logic: 'CorequisiteLogic', operation: str) -> 'CorequisiteLogic':
        if operation == 'AND':
            return CorequisiteLogic(self.groups + other_logic.groups)
        elif operation == 'OR':
            return CorequisiteLogic([list(set(a + b)) for a, b in zip(self.groups, other_logic.groups)])
        return self
    
    def negate(self) -> 'CorequisiteLogic':
        return self
   
    def substitute(self, course_mapping: Dict[str, str]) -> 'CorequisiteLogic':
        new_groups = [[course_mapping.get(c, c) for c in group] for group in self.groups]
        return CorequisiteLogic(new_groups)
    
    def simplify_logic(self) -> 'CorequisiteLogic':
        new_groups = [list(set(group)) for group in self.groups]
        return CorequisiteLogic(new_groups)
    
    def normalize_logic(self) -> 'CorequisiteLogic':
        return self.simplify_logic()
    
    def minimize_logic(self) -> 'CorequisiteLogic':
        return self.simplify_logic()

    # --- Program Integration ---
    def satisfies_requirement(self, requirement: object, completed_courses: Set[str], enrolled_courses: Set[str]) -> bool:
        return self.is_satisfied(completed_courses, enrolled_courses)
    
    def get_requirement_contribution(self, requirement: object, completed_courses: Set[str], enrolled_courses: Set[str]) -> float:
        return self.get_satisfaction_percentage(completed_courses, enrolled_courses)
    
    def get_requirement_impact(self, requirement: object) -> float:
        return float(len(self.groups))

    # --- Performance & Optimization ---
    def cache_evaluation_results(self, completed_courses: Set[str], enrolled_courses: Set[str], result: bool):
        pass
    
    def clear_cache(self):
        pass
    
    def get_cache_stats(self) -> Dict:
        return {}
    
    def optimize_for_evaluation(self) -> 'CorequisiteLogic':
        return self
    
    def precompute_partial_results(self) -> Dict:
        return {}

    # --- Utility Methods ---
    def get_logic_type(self) -> str:
        return "corequisite" 