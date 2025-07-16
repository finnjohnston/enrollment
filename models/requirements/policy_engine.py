from typing import Dict, List, Tuple, Any, Callable
import json
import os

# Rule function registry
RULE_FUNCTIONS: Dict[str, Callable] = {}

def rule(name):
    def decorator(fn):
        RULE_FUNCTIONS[name] = fn
        return fn
    return decorator

@rule("no_double_count_within_program")
def no_double_count_within_program(programs, assignments, **kwargs):
    errors = []
    for program in programs:
        bins = {}
        for course_code, course_assignments in assignments.items():
            for prog_name, category in course_assignments:
                if prog_name == program.name:
                    bins.setdefault(course_code, []).append(category)
        for course_code, cats in bins.items():
            if len(cats) > 1:
                errors.append(f"Course {course_code} assigned to multiple categories in {program.name}: {cats}")
    return errors

@rule("allow_cross_program_overlap")
def allow_cross_program_overlap(programs, assignments, condition=None, **kwargs):
    errors = []
    # Only applies to pairs of programs
    if len(programs) < 2:
        return errors
    for i, program1 in enumerate(programs):
        for program2 in programs[i+1:]:
            for course_code, course_assignments in assignments.items():
                p1_bins = [cat for prog, cat in course_assignments if prog == program1.name]
                p2_bins = [cat for prog, cat in course_assignments if prog == program2.name]
                if p1_bins and p2_bins:
                    # Course is shared between programs
                    if condition == "must_satisfy_both":
                        # Check if course actually satisfies a requirement in both (assume assignment means it does)
                        # If more logic is needed, add here
                        pass  # Already enforced by assignment logic
                    elif condition == "required_courses_only":
                        # Only allow if both bins are 'core' or 'required' (example logic)
                        if not ("Core" in p1_bins[0] and "Core" in p2_bins[0]):
                            errors.append(f"Course {course_code} cannot be shared unless both are core/required bins.")
    return errors

class PolicyEngine:
    def __init__(self, policy_config=None, config_path=None):
        if policy_config is not None:
            self.policy_config = policy_config
        else:
            # Load from JSON file
            if config_path is None:
                config_path = os.path.join(os.path.dirname(__file__), '../../db/data/policy/policy.json')
            with open(config_path, 'r') as f:
                self.policy_config = json.load(f)

    def get_policy(self, programs: List[Any]) -> List[Dict]:
        # Find all policies that match the set of program types
        # Use school information if available, otherwise fall back to type
        program_types = set()
        for p in programs:
            if hasattr(p, 'school') and p.school:
                # Map school names to policy types, respecting the actual program type
                program_type = getattr(p, 'type', 'major')  # Default to major if not specified
                if p.school == "School of Engineering":
                    if program_type == "major":
                        program_types.add("SoE Major")
                    elif program_type == "minor":
                        program_types.add("SoE Minor")
                    else:
                        program_types.add(f"SoE {program_type.title()}")
                elif p.school == "College of Arts and Science":
                    if program_type == "major":
                        program_types.add("A&S Major")
                    elif program_type == "minor":
                        program_types.add("A&S Minor")
                    else:
                        program_types.add(f"A&S {program_type.title()}")
            else:
                # Fall back to generic type
                program_types.add(getattr(p, 'type', None))
        
        applicable = []
        for policy in self.policy_config:
            if set(policy["program_types"]).issubset(program_types):
                applicable.append(policy)
        return applicable

    def validate_plan(self, programs: List[Any], assignments: Dict[str, List[Tuple[str, str]]]) -> Dict[str, Any]:
        errors = []
        warnings = []
        applicable_policies = self.get_policy(programs)
        for policy in applicable_policies:
            for rule in policy["rules"]:
                rule_type = rule["type"]
                fn = RULE_FUNCTIONS.get(rule_type)
                if fn:
                    rule_errors = fn(programs, assignments, **rule)
                    if rule_errors:
                        errors.extend(rule_errors)
        return {"is_valid": not errors, "errors": errors, "warnings": warnings} 