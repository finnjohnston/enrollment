import json
from .program import Program
from .category import RequirementCategory
from .requirement_types import CourseListRequirement, CourseOptionsRequirement, CourseFilterRequirement, CompoundRequirement
from .restrictions import ExclusionRestriction, CourseGroupRestriction, CreditLimitRestriction, DistributionRestriction, TagQuotaRestriction, SubjectQuotaRestriction, LevelQuotaRestriction
from models.requirements.restrictions.group import RestrictionGroup

class ProgramBuilder:
    @staticmethod
    def build_requirement(req_json):
        t = req_json.get('type')
        restrictions = None
        if 'restrictions' in req_json and req_json['restrictions']:
            built_restriction = ProgramBuilder.build_restriction(req_json['restrictions'])
            if built_restriction is not None:
                if not isinstance(built_restriction, RestrictionGroup):
                    restrictions = RestrictionGroup([built_restriction])
                else:
                    restrictions = built_restriction
        if t == 'course_list':
            return CourseListRequirement(req_json['courses'], restrictions=restrictions)
        elif t == 'course_options':
            return CourseOptionsRequirement(req_json['options'], req_json.get('min_required', 1), restrictions=restrictions)
        elif t == 'course_filter':
            return CourseFilterRequirement(
                subject=req_json.get('subject'),
                tags=req_json.get('tags'),
                min_level=req_json.get('min_level'),
                max_level=req_json.get('max_level'),
                min_credits=req_json.get('min_credits'),
                note=req_json.get('note'),
                restrictions=restrictions
            )
        elif t == 'compound':
            return CompoundRequirement([
                ProgramBuilder.build_requirement(opt) for opt in req_json['options']
            ], restrictions=restrictions)
        else:
            raise ValueError(f"Unknown requirement type: {t}")

    @staticmethod
    def build_restriction(rest_json):
        t = rest_json.get('type')
        if t == 'exclusion':
            return ExclusionRestriction(
                excluded_course_codes=rest_json.get('excluded_course_codes'),
                excluded_numbers=rest_json.get('excluded_numbers'),
                min_number=rest_json.get('min_number'),
                max_number=rest_json.get('max_number'),
                excluded_levels=rest_json.get('excluded_levels'),
                subject=rest_json.get('subject')
            )
        elif t == 'course_group':
            return CourseGroupRestriction(rest_json['courses'], rest_json['max_credits'])
        elif t == 'credit_limit':
            return CreditLimitRestriction(rest_json['courses'], rest_json['max_credits'])
        elif t == 'distribution':
            return DistributionRestriction(rest_json['courses'], rest_json['min_credits'])
        elif t == 'tag_quota':
            return TagQuotaRestriction(rest_json['tag'], rest_json['min_credits'])
        elif t == 'subject_quota':
            return SubjectQuotaRestriction(rest_json['subject'], rest_json.get('min_credits'), rest_json.get('max_credits'))
        elif t == 'level_quota':
            return LevelQuotaRestriction(rest_json['min_level'], rest_json['max_level'])
        elif t == 'group':
            return RestrictionGroup([
                ProgramBuilder.build_restriction(r) for r in rest_json['restrictions']
            ])
        else:
            raise ValueError(f"Unknown restriction type: {t}")

    @staticmethod
    def build_category(cat_json):
        requirements = [ProgramBuilder.build_requirement(r) for r in cat_json.get('requirements', [])]
        restrictions = None
        if 'restrictions' in cat_json and cat_json['restrictions']:
            built_restriction = ProgramBuilder.build_restriction(cat_json['restrictions'])
            if built_restriction is not None:
                if not isinstance(built_restriction, RestrictionGroup):
                    restrictions = RestrictionGroup([built_restriction])
                else:
                    restrictions = built_restriction
        return RequirementCategory(
            category=cat_json['category'],
            min_credits=cat_json['min_credits'],
            requirements=requirements,
            restrictions=restrictions,
            notes=cat_json.get('notes')
        )

    @staticmethod
    def build_program(prog_json):
        categories = [ProgramBuilder.build_category(cat) for cat in prog_json['categories']]
        return Program(
            name=prog_json['name'],
            type=prog_json['type'],
            total_credits=prog_json['total_credits'],
            categories=categories,
            notes=prog_json.get('notes'),
            school=prog_json.get('school')
        )

    @staticmethod
    def build_programs_from_file(json_path):
        with open(json_path, 'r') as f:
            data = json.load(f)
        return [ProgramBuilder.build_program(prog) for prog in data] 