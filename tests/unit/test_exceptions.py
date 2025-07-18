import pytest
from core.exceptions import (
    EnrollmentError, InvalidCourseError, DatabaseError, ResourceNotFoundError
)

def test_enrollment_error():
    with pytest.raises(EnrollmentError):
        raise EnrollmentError("Test EnrollmentError")

def test_invalid_course_error():
    with pytest.raises(InvalidCourseError):
        raise InvalidCourseError("Test InvalidCourseError")

def test_database_error():
    with pytest.raises(DatabaseError):
        raise DatabaseError("Test DatabaseError")

def test_resource_not_found_error():
    with pytest.raises(ResourceNotFoundError):
        raise ResourceNotFoundError("Test ResourceNotFoundError") 