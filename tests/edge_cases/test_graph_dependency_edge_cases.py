import pytest
from models.graph.dependency_graph import DependencyGraph
from models.graph.eligibility import CourseEligibility
from types import SimpleNamespace

# Helper to create a mock course object
def make_course(code, prereqs=None, coreqs=None):
    return SimpleNamespace(
        course_code=code,
        prereqs=prereqs,
        coreqs=coreqs,
        prerequisites=prereqs,
        corequisites=coreqs
    )

class MockCatalog:
    def __init__(self, courses):
        self.courses = courses
        self._by_code = {c.course_code: c for c in courses}
    def get_by_course_code(self, code):
        return self._by_code.get(code)

# --- Circular prerequisites ---
def test_circular_prerequisites():
    c1 = make_course('A', prereqs=['B'])
    c2 = make_course('B', prereqs=['A'])
    catalog = MockCatalog([c1, c2])
    graph = DependencyGraph(catalog)
    # Should not infinite loop, and should return correct prereqs
    assert set(graph.get_prerequisites('A')) == {'B'}
    assert set(graph.get_prerequisites('B')) == {'A'}

# --- Self-referential prerequisites ---
def test_self_referential_prerequisite():
    c1 = make_course('A', prereqs=['A'])
    catalog = MockCatalog([c1])
    graph = DependencyGraph(catalog)
    assert set(graph.get_prerequisites('A')) == {'A'}

# --- Disconnected nodes ---
def test_disconnected_nodes():
    c1 = make_course('A')
    c2 = make_course('B')
    catalog = MockCatalog([c1, c2])
    graph = DependencyGraph(catalog)
    assert graph.get_prerequisites('A') == []
    assert graph.get_prerequisites('B') == []
    assert graph.get_corequisites('A') == []
    assert graph.get_corequisites('B') == []

# --- Multiple paths to eligibility (AND/OR logic) ---
def test_multiple_paths_to_eligibility():
    # A requires (B or C) and D
    cA = make_course('A', prereqs=[[['B', 'C'], ['D']]])
    cB = make_course('B')
    cC = make_course('C')
    cD = make_course('D')
    catalog = MockCatalog([cA, cB, cC, cD])
    graph = DependencyGraph(catalog)
    # Should parse as two groups: ['B', 'C'] (OR), ['D'] (AND)
    prereqs = graph.get_prerequisites('A')
    assert set(prereqs) >= {'B', 'C', 'D'}

# --- Empty course catalog ---
def test_empty_course_catalog():
    catalog = MockCatalog([])
    graph = DependencyGraph(catalog)
    # Any get should return []
    assert graph.get_prerequisites('X') == []
    assert graph.get_corequisites('X') == []

# --- Nonexistent course codes in prerequisites/corequisites ---
def test_nonexistent_course_codes_in_prereqs_coreqs():
    c1 = make_course('A', prereqs=['B'], coreqs=['C'])
    # B and C do not exist in catalog
    catalog = MockCatalog([c1])
    graph = DependencyGraph(catalog)
    # Should not raise, but return the codes as prereqs/coreqs
    assert set(graph.get_prerequisites('A')) == {'B'}
    assert set(graph.get_corequisites('A')) == {'C'}

# --- Eligibility with circular prereqs ---
def test_eligibility_circular_prereqs():
    c1 = make_course('A', prereqs=['B'])
    c2 = make_course('B', prereqs=['A'])
    catalog = MockCatalog([c1, c2])
    graph = DependencyGraph(catalog)
    # Should not infinite loop, and should return False for eligibility
    eligible = CourseEligibility.is_course_eligible('A', set(), set(), graph)
    assert eligible is False
    eligible = CourseEligibility.is_course_eligible('B', set(), set(), graph)
    assert eligible is False 