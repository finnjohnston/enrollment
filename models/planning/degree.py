from typing import List, Dict, Optional, Set, Any
from models.courses.course import Course
from models.courses.catalog import Catalog
from models.graph.dependency_graph import DependencyGraph
from models.requirements.program import Program
from models.requirements.requirement_types.requirement import Requirement
from models.requirements.requirement_types.course_list import CourseListRequirement
from models.requirements.requirement_types.course_options import CourseOptionsRequirement
from models.requirements.requirement_types.course_filter import CourseFilterRequirement
from models.requirements.requirement_types.compound import CompoundRequirement

class DegreePlanner:
    """
    Core degree planning functionality.
    """
    
    def __init__(self, program: Program, completed_courses: List[Course],
                 catalog: Catalog, dependency_graph: DependencyGraph):
        self.program = program
        self.completed_courses = completed_courses
        self.catalog = catalog
        self.dependency_graph = dependency_graph
        
        # Convert completed_courses to set of course codes for compatibility
        self.completed_course_codes = {course.get_course_code() for course in completed_courses}

    # 1. Course Availability & Planning
    
    def get_available_courses(self) -> List[Course]:
        """Get all courses that can be taken with current completed courses."""
        available_courses = []
        for course in self.catalog.courses:
            course_code = course.get_course_code()
            if isinstance(course_code, str) and self.can_take_course(course_code, self.completed_courses):
                available_courses.append(course)
        return available_courses
    
    def get_available_courses_for_requirement(self, requirement: Requirement) -> List[Course]:
        """Get courses that can be taken to satisfy a specific requirement."""
        # Get possible courses for this requirement
        possible_courses = requirement.get_possible_courses(self.catalog.courses)
        
        # Filter to only available courses
        available_courses = []
        for course in possible_courses:
            course_code = course.get_course_code()
            if isinstance(course_code, str) and self.can_take_course(course_code, self.completed_courses):
                available_courses.append(course)
        
        return available_courses
    
    def can_take_course(self, course_code: str, completed_courses: List[Course]) -> bool:
        """Check if a course can be taken with the given completed courses."""
        return self.dependency_graph.is_available(course_code, completed_courses)
    
    def get_missing_prerequisites(self, course_code: str, completed_courses: List[Course]) -> List[List[str]]:
        """Get missing prerequisites for a course."""
        return self.dependency_graph.get_missing_prerequisites(course_code, completed_courses)
    
    # 2. Course Information & Context
    
    def get_course_details(self, course_code: str) -> Dict:
        """Get detailed information about a course including planning context."""
        course = self.catalog.get_by_course_code(course_code)
        if not course:
            return {"error": "Course not found"}
        
        # Check availability
        availability = self.get_course_availability(course_code)
        
        # Find which requirements this course satisfies
        satisfying_requirements = []
        for category in self.program.categories:
            for req in category.requirements:
                possible_courses = req.get_possible_courses([course])
                if course in possible_courses:
                    satisfying_requirements.append({
                        "category": category.category,
                        "requirement": req.describe()
                    })
        
        return {
            "course": course,
            "availability": availability,
            "satisfying_requirements": satisfying_requirements,
            "prerequisites": self.dependency_graph.get_prerequisites(course_code),
            "dependents": self.dependency_graph.get_dependents(course_code)
        }
    
    def get_course_availability(self, course_code: str) -> Dict:
        """Get availability information for a specific course."""
        course = self.catalog.get_by_course_code(course_code)
        if not course:
            return {"available": False, "reason": "Course not found in catalog"}
        
        # Check if already completed
        if course_code in self.completed_course_codes:
            return {"available": False, "reason": "Course already completed"}
        
        # Check prerequisites
        can_take = self.can_take_course(course_code, self.completed_courses)
        missing_prereqs = self.get_missing_prerequisites(course_code, self.completed_courses)
        
        return {
            "available": can_take,
            "course": course,
            "missing_prerequisites": missing_prereqs,
            "reason": "Prerequisites not met" if missing_prereqs else "Available"
        }
    
    def get_alternatives_for_course(self, course_code: str) -> List[Course]:
        """Get alternative courses that could be taken instead of the specified course."""
        course = self.catalog.get_by_course_code(course_code)
        if not course:
            return []
        
        # Find requirements this course satisfies
        alternatives = []
        for category in self.program.categories:
            for req in category.requirements:
                possible_courses = req.get_possible_courses([course])
                if course in possible_courses:
                    # Get all possible courses for this requirement
                    all_possible = req.get_possible_courses(self.catalog.courses)
                    # Filter to available courses that aren't the original course
                    for alt_course in all_possible:
                        alt_code = alt_course.get_course_code()
                        if (isinstance(alt_code, str) and alt_code != course_code and 
                            self.can_take_course(alt_code, self.completed_courses)):
                            alternatives.append(alt_course)
        
        # Remove duplicates
        seen_codes = set()
        unique_alternatives = []
        for alt in alternatives:
            code = alt.get_course_code()
            if code not in seen_codes:
                seen_codes.add(code)
                unique_alternatives.append(alt)
        
        return unique_alternatives
    
    def get_dependent_courses(self, course_code: str) -> List[Course]:
        """Get courses that depend on the specified course (prerequisites)."""
        dependents = self.dependency_graph.get_dependents(course_code)
        dependent_courses = []
        for dep_code in dependents:
            course = self.catalog.get_by_course_code(dep_code)
            if course:
                dependent_courses.append(course)
        return dependent_courses

    # Helper methods
    
    def _get_requirements_satisfied_by(self, course_code: str) -> List[str]:
        """Get requirement categories satisfied by a course."""
        satisfied = []
        
        for category in self.program.categories:
            for requirement in category.requirements:
                if self._course_satisfies_requirement(course_code, requirement):
                    satisfied.append(category.category)
        
        return list(set(satisfied))  # Remove duplicates
    
    def _course_satisfies_requirement(self, course_code: str, requirement: Requirement) -> bool:
        """Check if a course satisfies a specific requirement."""
        if isinstance(requirement, CourseListRequirement):
            return course_code in requirement.courses
        
        elif isinstance(requirement, CourseOptionsRequirement):
            return course_code in requirement.options
        
        elif isinstance(requirement, CourseFilterRequirement):
            course = self.catalog.get_by_course_code(course_code)
            if not course:
                return False
            
            # Check subject filter
            if requirement.subject and course.subject_code != requirement.subject:
                return False
            
            # Check level filters
            if requirement.min_level and (course.level is None or course.level < requirement.min_level):
                return False
            if requirement.max_level and (course.level is None or course.level > requirement.max_level):
                return False
            
            # Check tag filters
            if requirement.tags:
                course_tags = course.get_axle_requirements()
                if not any(tag in course_tags for tag in requirement.tags):
                    return False
            
            return True
        
        elif isinstance(requirement, CompoundRequirement):
            # For compound requirements, check if course satisfies any option
            return any(self._course_satisfies_requirement(course_code, option) 
                      for option in requirement.options)
        
        return False
