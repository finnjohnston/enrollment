from pydantic import BaseModel
from typing import List, Optional, Any, Tuple

class CourseSchema(BaseModel):
    course_code: str
    title: str
    subject_name: Optional[str]
    subject_code: Optional[str]
    course_number: Optional[str]
    level: Optional[int]
    axle: Optional[Any]
    credits: Optional[int]
    prerequisites: Optional[Any]
    corequisites: Optional[Any]
    description: Optional[str]

class RequirementSchema(BaseModel):
    id: Optional[int]
    type: str
    data: Any
    min_credits: Optional[int]
    notes: Optional[str]

class CategorySchema(BaseModel):
    id: Optional[int]
    category: str
    min_credits: int
    requirements: List[RequirementSchema]
    notes: Optional[str]

class ProgramSchema(BaseModel):
    id: Optional[int]
    name: str
    type: str
    total_credits: int
    categories: List[CategorySchema]
    notes: Optional[str]
    school: Optional[str]

class PlanCreateSchema(BaseModel):
    program_ids: List[int]
    start_semester: str
    year: int

class PlanSchema(BaseModel):
    id: int
    programs: List[ProgramSchema]
    completed_courses: List[str]
    current_semester: str
    assignments: Any

class RecommendationSchema(BaseModel):
    recommendations: Any

class ValidationResultSchema(BaseModel):
    is_valid: bool
    errors: List[str]
    warnings: List[str] 