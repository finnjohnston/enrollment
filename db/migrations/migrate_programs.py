import json
from sqlalchemy.exc import IntegrityError
from db.database import SessionLocal
from db.models.program import Program
from db.models.requirement_category import RequirementCategory
from db.models.requirement import Requirement
from config.config import PROGRAMS_PATH

def load_programs(json_path):
    with open(json_path, 'r') as f:
        return json.load(f)

def main():
    session = SessionLocal()
    programs = load_programs(PROGRAMS_PATH)
    for prog_data in programs:
        program = Program(
            name=prog_data.get('name'),
            type=prog_data.get('type'),
            total_credits=prog_data.get('total_credits'),
            notes=prog_data.get('notes'),
            school=prog_data.get('school')
        )
        session.add(program)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            continue
        for cat_data in prog_data.get('categories', []):
            category = RequirementCategory(
                program_id=program.id,
                category=cat_data.get('category'),
                min_credits=cat_data.get('min_credits'),
                notes=cat_data.get('notes')
            )
            session.add(category)
            session.commit()
            for req_data in cat_data.get('requirements', []):
                req_type = req_data.get('type')
                min_credits = req_data.get('min_credits') if 'min_credits' in req_data else None
                notes = req_data.get('note') if 'note' in req_data else None
                requirement = Requirement(
                    category_id=category.id,
                    type=req_type,
                    data=req_data,
                    min_credits=min_credits,
                    notes=notes
                )
                session.add(requirement)
                session.commit()
    session.close()

if __name__ == '__main__':
    main() 