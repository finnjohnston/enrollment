import json
from .program import Program
from .category import RequirementCategory
from .requirement_types import CourseListRequirement, CourseOptionsRequirement, CourseFilterRequirement, CompoundRequirement
from .restrictions import ExclusionRestriction, CourseGroupRestriction, CreditLimitRestriction, DistributionRestriction, TagQuotaRestriction, SubjectQuotaRestriction, LevelQuotaRestriction
from models.requirements.restrictions.group import RestrictionGroup
from db.database import SessionLocal
from db.models.program import Program as ORMProgram
from db.models.requirement_category import RequirementCategory as ORMCategory
from db.models.requirement import Requirement as ORMRequirement
from core.exceptions import UnknownRequirementTypeError

class ProgramBuilder:
    @staticmethod
    def build_requirement_from_db(req_orm):
        # If req_orm is a dict (from JSONB), use dict logic
        if isinstance(req_orm, dict):
            t = req_orm.get('type')
            data = req_orm.get('data', req_orm)
            restrictions = None  # TODO: handle restrictions if present in DB
            if t == 'course_list':
                return CourseListRequirement(data.get('courses', []), restrictions=restrictions)
            elif t == 'course_options':
                return CourseOptionsRequirement(data.get('options', []), data.get('min_required', 1), restrictions=restrictions)
            elif t == 'course_filter':
                return CourseFilterRequirement(
                    subject=data.get('subject'),
                    tags=data.get('tags'),
                    min_level=data.get('min_level'),
                    max_level=data.get('max_level'),
                    min_credits=data.get('min_credits'),
                    note=data.get('note'),
                    restrictions=restrictions
                )
            elif t == 'compound':
                op = data.get('op', 'OR')
                options = [ProgramBuilder.build_requirement_from_db(opt) for opt in data.get('options',[])]
                return CompoundRequirement(options, restrictions=restrictions, op=op)
            else:
                raise UnknownRequirementTypeError(f"Unknown requirement type: {t}")
        # Otherwise, treat as ORM object
        t = req_orm.type
        data = req_orm.data or {}
        restrictions = None  # TODO: handle restrictions if present in DB
        if t == 'course_list':
            return CourseListRequirement(data.get('courses', []), restrictions=restrictions)
        elif t == 'course_options':
            return CourseOptionsRequirement(data.get('options', []), data.get('min_required', 1), restrictions=restrictions)
        elif t == 'course_filter':
            return CourseFilterRequirement(
                subject=data.get('subject'),
                tags=data.get('tags'),
                min_level=data.get('min_level'),
                max_level=data.get('max_level'),
                min_credits=data.get('min_credits'),
                note=data.get('note'),
                restrictions=restrictions
            )
        elif t == 'compound':
            op = data.get('op', 'OR')
            options = [ProgramBuilder.build_requirement_from_db(opt) for opt in data.get('options',[])]
            return CompoundRequirement(options, restrictions=restrictions, op=op)
        else:
            raise UnknownRequirementTypeError(f"Unknown requirement type: {t}")

    @staticmethod
    def build_category_from_db(cat_orm):
        requirements = [ProgramBuilder.build_requirement_from_db(req) for req in cat_orm.requirements]
        restrictions = None  # TODO: handle restrictions if present in DB
        return RequirementCategory(
            category=cat_orm.category,
            min_credits=cat_orm.min_credits,
            requirements=requirements,
            restrictions=restrictions,
            notes=cat_orm.notes
        )

    @staticmethod
    def build_program_from_db(prog_orm):
        categories = [ProgramBuilder.build_category_from_db(cat) for cat in prog_orm.categories]
        return Program(
            name=prog_orm.name,
            type=prog_orm.type,
            total_credits=prog_orm.total_credits,
            categories=categories,
            notes=prog_orm.notes,
            school=prog_orm.school
        )

    @staticmethod
    def build_programs_from_db():
        session = SessionLocal()
        orm_programs = session.query(ORMProgram).all()
        programs = [ProgramBuilder.build_program_from_db(prog) for prog in orm_programs]
        session.close()
        return programs 