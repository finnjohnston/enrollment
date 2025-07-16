import json
from sqlalchemy.exc import IntegrityError
from db.database import SessionLocal
from db.models.course import Course
import re

def parse_credits(credits):
    if credits is None:
        return None
    if isinstance(credits, int):
        return credits
    if isinstance(credits, str):
        match = re.match(r'^(\d+)-(\d+)$', credits.strip())
        if match:
            return int(match.group(1))
        try:
            return int(credits)
        except ValueError:
            return None
    return None

def load_courses(json_path):
    with open(json_path, 'r') as f:
        return json.load(f)

def main():
    session = SessionLocal()
    courses = load_courses('db/data/courses/parsed.json')
    for course_data in courses:
        course = Course(
            course_code=course_data.get('course_code'),
            title=course_data.get('title'),
            subject_name=course_data.get('subject_name'),
            subject_code=course_data.get('subject_code'),
            course_number=course_data.get('course_number'),
            level=course_data.get('level'),
            axle=course_data.get('axle') if isinstance(course_data.get('axle'), list) else [course_data.get('axle')] if course_data.get('axle') else [],
            credits=parse_credits(course_data.get('credits')),
            prerequisites=course_data.get('prerequisites'),
            corequisites=course_data.get('corequisites'),
            description=course_data.get('description')
        )
        session.add(course)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
    session.close()

if __name__ == '__main__':
    main() 