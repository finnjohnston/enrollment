class EnrollmentError(Exception):
    """Base class for all enrollment-related errors."""
    pass

# --- Model/Validation Errors ---
class InvalidCourseError(EnrollmentError):
    """Raised when a course is invalid or missing required fields."""
    pass

class InvalidProgramError(EnrollmentError):
    """Raised when a program is invalid or missing required fields."""
    pass

class InvalidRequirementError(EnrollmentError):
    """Raised when a requirement is invalid or missing required fields."""
    pass

class InvalidCategoryError(EnrollmentError):
    """Raised when a category is invalid or missing required fields."""
    pass

class InvalidCreditsError(EnrollmentError):
    """Raised when credits are invalid (e.g., negative or not an integer)."""
    pass

class InvalidLevelError(EnrollmentError):
    """Raised when a course or requirement level is invalid."""
    pass

# --- Policy/Requirement/Rule Errors ---
class PolicyConfigError(EnrollmentError):
    """Raised when the policy configuration is invalid."""
    pass

class UnknownRequirementTypeError(EnrollmentError):
    """Raised when an unknown requirement type is encountered."""
    pass

class UnknownPolicyRuleError(EnrollmentError):
    """Raised when an unknown policy rule type is encountered."""
    pass

# --- Not Implemented/Abstract Errors ---
class RequirementNotImplementedError(EnrollmentError, NotImplementedError):
    """Raised when a requirement method is not implemented."""
    pass

class RestrictionNotImplementedError(EnrollmentError, NotImplementedError):
    """Raised when a restriction method is not implemented."""
    pass

# --- API/Resource Errors (for completeness, if you want to wrap HTTPException) ---
class ResourceNotFoundError(EnrollmentError):
    """Raised when a requested resource (course, program, plan, etc.) is not found."""
    pass

class InvalidAssignmentError(EnrollmentError):
    pass

class DatabaseError(EnrollmentError):
    pass 