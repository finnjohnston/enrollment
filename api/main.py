from fastapi import FastAPI, HTTPException, Depends, APIRouter, Body
from typing import List, Dict, Any
from api.schemas import CourseSchema, ProgramSchema, CategorySchema, RequirementSchema, PlanCreateSchema, PlanSchema, RecommendationSchema, ValidationResultSchema
from models.courses.catalog import Catalog
from models.requirements.program_builder import ProgramBuilder
from models.requirements.policy_engine import PolicyEngine
from models.planning.academic_planner import AcademicPlanner
from models.planning.semester import Semester
import threading

app = FastAPI(title="Academic Planning API")

# --- Routers ---
courses_router = APIRouter()
programs_router = APIRouter()
categories_router = APIRouter()
requirements_router = APIRouter()
planning_router = APIRouter()
recommendations_router = APIRouter()
validation_router = APIRouter()
policies_router = APIRouter()

# --- In-memory plan storage (thread-safe) ---
plans: Dict[int, AcademicPlanner] = {}
plan_lock = threading.Lock()
plan_counter = 0

def get_catalog():
    return Catalog()

def get_programs():
    return ProgramBuilder.build_programs_from_db()

def get_policy_engine():
    return PolicyEngine()

def serialize_restriction(r):
    if r is None:
        return None
    if hasattr(r, 'restrictions') and isinstance(getattr(r, 'restrictions'), list):
        return {
            'type': r.__class__.__name__,
            'description': getattr(r, 'description', None),
            'restrictions': [serialize_restriction(sub) for sub in r.restrictions]
        }
    return {
        'type': r.__class__.__name__,
        'description': r.describe() if hasattr(r, 'describe') else None
    }

def serialize_requirement(r, req_id=None):
    if r is None:
        return None
    # Compose the 'data' field from the requirement's attributes
    data = {}
    for attr in ['courses', 'options', 'subject', 'tags', 'min_level', 'max_level', 'op', 'restrictions']:
        if hasattr(r, attr):
            val = getattr(r, attr)
            # Recursively serialize options and restrictions
            if attr == 'options' and isinstance(val, list):
                data[attr] = [serialize_requirement(opt) for opt in val]
            elif attr == 'restrictions':
                data[attr] = serialize_restriction(val)
            else:
                data[attr] = val
    # Compose the requirement dict to match RequirementSchema
    return {
        'id': req_id,  # Pass id from caller or None
        'type': r.__class__.__name__,
        'data': data,
        'min_credits': getattr(r, 'min_credits', None),
        'notes': getattr(r, 'notes', None)
    }

def requirement_to_dict(r, req_id=None):
    return serialize_requirement(r, req_id)

def category_to_dict(c, ci):
    return {
        'id': ci,
        'category': c.category,
        'min_credits': c.min_credits,
        'requirements': [serialize_requirement(r, ri) for ri, r in enumerate(getattr(c, 'requirements', []))],
        'notes': c.notes
    }

def program_to_dict(p, i):
    return {
        'id': i,
        'name': p.name,
        'type': p.type,
        'total_credits': p.total_credits,
        'categories': [category_to_dict(c, ci) for ci, c in enumerate(p.categories)],
        'notes': p.notes,
        'school': p.school
    }

def serialize_recommendations(obj):
    # Recursively serialize recommendations structure
    if isinstance(obj, list):
        return [serialize_recommendations(item) for item in obj]
    elif hasattr(obj, 'to_dict'):
        return obj.to_dict()
    elif hasattr(obj, 'get_course_code'):
        return obj.get_course_code()
    elif isinstance(obj, dict):
        return {k: serialize_recommendations(v) for k, v in obj.items()}
    else:
        return obj

@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok"}

# --- Courses ---
@courses_router.get("/courses", response_model=List[CourseSchema], tags=["Courses"])
def list_courses():
    catalog = get_catalog()
    return [CourseSchema(
        course_code=str(c.to_dict().get('course_code', '')),
        title=str(c.to_dict().get('title', '')),
        subject_name=c.to_dict().get('subject_name'),
        subject_code=c.to_dict().get('subject_code'),
        course_number=c.to_dict().get('course_number'),
        level=c.to_dict().get('level'),
        axle=c.to_dict().get('axle'),
        credits=c.to_dict().get('credits'),
        prerequisites=c.to_dict().get('prerequisites'),
        corequisites=c.to_dict().get('corequisites'),
        description=c.to_dict().get('description')
    ) for c in catalog.courses]

@courses_router.get("/courses/{course_code}", response_model=CourseSchema, tags=["Courses"])
def get_course(course_code: str):
    catalog = get_catalog()
    course = catalog.get_by_course_code(course_code)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    d = course.to_dict()
    return CourseSchema(
        course_code=str(d.get('course_code', '')),
        title=str(d.get('title', '')),
        subject_name=d.get('subject_name'),
        subject_code=d.get('subject_code'),
        course_number=d.get('course_number'),
        level=d.get('level'),
        axle=d.get('axle'),
        credits=d.get('credits'),
        prerequisites=d.get('prerequisites'),
        corequisites=d.get('corequisites'),
        description=d.get('description')
    )

# --- Programs ---
@programs_router.get("/programs", response_model=List[ProgramSchema], tags=["Programs"])
def list_programs():
    programs = get_programs()
    return [program_to_dict(p, i) for i, p in enumerate(programs)]

@programs_router.get("/programs/{program_id}", response_model=ProgramSchema, tags=["Programs"])
def get_program(program_id: int):
    if program_id < 0:
        raise HTTPException(status_code=404, detail="Program not found")
    programs = get_programs()
    if program_id < 0 or program_id >= len(programs):
        raise HTTPException(status_code=404, detail="Program not found")
    p = programs[program_id]
    return program_to_dict(p, program_id)

@programs_router.get("/programs/{program_id}/categories", response_model=List[CategorySchema], tags=["Programs"])
def list_program_categories(program_id: int):
    if program_id < 0:
        raise HTTPException(status_code=404, detail="Program not found")
    programs = get_programs()
    if program_id < 0 or program_id >= len(programs):
        raise HTTPException(status_code=404, detail="Program not found")
    p = programs[program_id]
    return [category_to_dict(c, ci) for ci, c in enumerate(p.categories)]

# --- Categories ---
@categories_router.get("/categories/{category_id}", response_model=CategorySchema, tags=["Categories"])
def get_category(category_id: int):
    if category_id < 0:
        raise HTTPException(status_code=404, detail="Category not found")
    programs = get_programs()
    for p in programs:
        if category_id < len(p.categories):
            c = p.categories[category_id]
            return category_to_dict(c, category_id)
    raise HTTPException(status_code=404, detail="Category not found")

@categories_router.get("/categories/{category_id}/requirements", response_model=List[RequirementSchema], tags=["Categories"])
def list_category_requirements(category_id: int):
    if category_id < 0:
        raise HTTPException(status_code=404, detail="Category not found")
    programs = get_programs()
    for p in programs:
        if category_id < len(p.categories):
            c = p.categories[category_id]
            return [requirement_to_dict(r) for r in getattr(c, 'requirements', [])]
    raise HTTPException(status_code=404, detail="Category not found")

# --- Requirements ---
@requirements_router.get("/requirements/{requirement_id}", response_model=RequirementSchema, tags=["Requirements"])
def get_requirement(requirement_id: int):
    if requirement_id < 0:
        raise HTTPException(status_code=404, detail="Requirement not found")
    programs = get_programs()
    for p in programs:
        for c in p.categories:
            if requirement_id < len(c.requirements):
                r = c.requirements[requirement_id]
                return requirement_to_dict(r, requirement_id)
    raise HTTPException(status_code=404, detail="Requirement not found")

# --- Planning ---
@planning_router.post("/plans", response_model=PlanSchema, tags=["Planning"])
def create_plan(plan: PlanCreateSchema):
    global plan_counter
    with plan_lock:
        plan_id = plan_counter
        plan_counter += 1
    catalog = get_catalog()
    programs = get_programs()
    selected_programs = [programs[pid] for pid in plan.program_ids if 0 <= pid < len(programs)]
    start_semester = Semester(plan.start_semester, plan.year)
    planner = AcademicPlanner(catalog, selected_programs, start_semester, policy_engine=get_policy_engine())
    with plan_lock:
        plans[plan_id] = planner
    return {
        'id': plan_id,
        'programs': [program_to_dict(p, i) for i, p in enumerate(selected_programs)],
        'completed_courses': [],
        'current_semester': str(start_semester),
        'assignments': {}
    }

@planning_router.get("/plans/{plan_id}", response_model=PlanSchema, tags=["Planning"])
def get_plan(plan_id: int):
    if plan_id < 0:
        raise HTTPException(status_code=404, detail="Plan not found")
    planner = plans.get(plan_id)
    if not planner:
        raise HTTPException(status_code=404, detail="Plan not found")
    return {
        'id': plan_id,
        'programs': [program_to_dict(p, i) for i, p in enumerate(planner.plan_config.programs)],
        'completed_courses': [c.get_course_code() for c in planner.student_state.get_completed_courses()],
        'current_semester': str(planner.student_state.get_current_semester()),
        'assignments': planner.assigner.get_assignment_summary()
    }

@planning_router.post("/plans/{plan_id}/add_completed_course", response_model=PlanSchema, tags=["Planning"])
def add_completed_course(plan_id: int, data: dict = Body(...)):
    if plan_id < 0:
        raise HTTPException(status_code=404, detail="Plan not found")
    planner = plans.get(plan_id)
    if not planner:
        raise HTTPException(status_code=404, detail="Plan not found")
    planner.add_completed_courses(data)
    return get_plan(plan_id)

@planning_router.post("/plans/{plan_id}/remove_completed_course", response_model=PlanSchema, tags=["Planning"])
def remove_completed_course(plan_id: int, data: dict = Body(...)):
    if plan_id < 0:
        raise HTTPException(status_code=404, detail="Plan not found")
    planner = plans.get(plan_id)
    if not planner:
        raise HTTPException(status_code=404, detail="Plan not found")
    course_code = data.get("course_code")
    planner.student_state.completed_courses = [c for c in planner.student_state.completed_courses if c.get_course_code() != course_code]
    return get_plan(plan_id)

@planning_router.post("/plans/{plan_id}/advance_semester", response_model=PlanSchema, tags=["Planning"])
def advance_semester(plan_id: int):
    if plan_id < 0:
        raise HTTPException(status_code=404, detail="Plan not found")
    planner = plans.get(plan_id)
    if not planner:
        raise HTTPException(status_code=404, detail="Plan not found")
    planner.advance_semester()
    return get_plan(plan_id)

@planning_router.get("/plans/{plan_id}/progress", response_model=PlanSchema, tags=["Planning"])
def get_progress(plan_id: int):
    if plan_id < 0:
        raise HTTPException(status_code=404, detail="Plan not found")
    return get_plan(plan_id)

# --- Recommendations ---
@recommendations_router.get("/plans/{plan_id}/recommendations", response_model=RecommendationSchema, tags=["Recommendations"])
def get_recommendations(plan_id: int):
    if plan_id < 0:
        raise HTTPException(status_code=404, detail="Plan not found")
    planner = plans.get(plan_id)
    if not planner:
        raise HTTPException(status_code=404, detail="Plan not found")
    recs = planner.get_recommendations()
    recs_serialized = serialize_recommendations(recs)
    return RecommendationSchema(recommendations=recs_serialized)

# --- Validation ---
@validation_router.post("/plans/{plan_id}/validate", response_model=ValidationResultSchema, tags=["Validation"])
def validate_plan(plan_id: int):
    if plan_id < 0:
        raise HTTPException(status_code=404, detail="Plan not found")
    planner = plans.get(plan_id)
    if not planner:
        raise HTTPException(status_code=404, detail="Plan not found")
    result = planner.validate_plan()
    return ValidationResultSchema(
        is_valid=result.get("is_valid", False),
        errors=result.get("errors", []),
        warnings=result.get("warnings", [])
    )

@validation_router.post("/plans/{plan_id}/validate_semester", response_model=ValidationResultSchema, tags=["Validation"])
def validate_semester(plan_id: int):
    if plan_id < 0:
        raise HTTPException(status_code=404, detail="Plan not found")
    return validate_plan(plan_id)

@validation_router.post("/plans/{plan_id}/validate_assignment", response_model=ValidationResultSchema, tags=["Validation"])
def validate_assignment(plan_id: int):
    if plan_id < 0:
        raise HTTPException(status_code=404, detail="Plan not found")
    return validate_plan(plan_id)

# --- Policies ---
@policies_router.get("/policies", tags=["Policies"])
def list_policies():
    engine = get_policy_engine()
    return engine.policy_config

@policies_router.get("/policies/{policy_id}", tags=["Policies"])
def get_policy(policy_id: int):
    engine = get_policy_engine()
    if policy_id < 0 or policy_id >= len(engine.policy_config):
        raise HTTPException(status_code=404, detail="Policy not found")
    return engine.policy_config[policy_id]

# --- Register routers ---
app.include_router(courses_router)
app.include_router(programs_router)
app.include_router(categories_router)
app.include_router(requirements_router)
app.include_router(planning_router)
app.include_router(recommendations_router)
app.include_router(validation_router)
app.include_router(policies_router) 