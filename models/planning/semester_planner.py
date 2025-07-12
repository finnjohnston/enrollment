from typing import Dict, List, Set, Optional
from models.courses.course import Course
from models.courses.catalog import Catalog
from models.graph.dependency_graph import DependencyGraph
from models.planning.semester import Semester
from models.planning.student_state import StudentState
from models.planning.recommendation_engine import get_unmet_requirements, get_all_recommendations, get_eligible_recommendations
from models.graph.eligibility import CourseEligibility


class SemesterPlanner:
    """
    Generates semester recommendations by filtering eligible courses and grouping mutual corequisites.
    """
    
    def __init__(self, catalog: Catalog, graph: DependencyGraph):
        self.catalog = catalog
        self.graph = graph
    
    def get_semester_recommendations(self, student_state: StudentState, semester: Semester, requirement_assignments: Optional[Dict[str, str]] = None) -> Dict[str, List]:
        completed_courses, enrolled_courses = student_state.get_eligibility_context()
        
        programs = [program for program in student_state.plan_config.programs]
        unmet = get_unmet_requirements(programs, completed_courses, requirement_assignments)
        all_recs = get_all_recommendations(unmet, self.catalog)
        eligible_recs = get_eligible_recommendations(all_recs, completed_courses, enrolled_courses, self.graph)
        
        recommendations = {}
        
        for category, courses in eligible_recs.items():
            category_recommendations = []
            processed_courses = set()
            
            for course in courses:
                if course in processed_courses:
                    continue
                    
                course_code = course.get_course_code()
                if not course_code:
                    continue
                
                completed_codes: Set[str] = set()
                for c in completed_courses:
                    code = c.get_course_code()
                    if code:
                        completed_codes.add(code)
                
                coreq_group = CourseEligibility._find_mutual_coreq_group(
                    course_code, 
                    completed_codes, 
                    self.graph
                )
                
                if len(coreq_group) > 1:
                    # Check if all courses in the corequisite group are eligible
                    group_courses = []
                    all_group_eligible = True
                    
                    for code in coreq_group:
                        course_obj = self.catalog.get_by_course_code(code)
                        if course_obj:
                            # Check if this course is eligible
                            if CourseEligibility.is_course_eligible(code, completed_codes, set(), self.graph):
                                group_courses.append(course_obj)
                            else:
                                all_group_eligible = False
                                break
                    
                    # If all courses in the group are eligible, add them as a nested list
                    if all_group_eligible and len(group_courses) > 1:
                        category_recommendations.append(group_courses)
                        for course_obj in group_courses:
                            processed_courses.add(course_obj)
                    else:
                        # If not all courses in the group are eligible, treat as individual
                        category_recommendations.append(course)
                        processed_courses.add(course)
                else:
                    category_recommendations.append(course)
                    processed_courses.add(course)
            
            if category_recommendations:
                recommendations[category] = category_recommendations
        
        return recommendations
    
    def __repr__(self):
        return f"<SemesterPlanner catalog={len(self.catalog.courses)} courses>" 