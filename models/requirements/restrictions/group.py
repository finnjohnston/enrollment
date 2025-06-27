from typing import List, Optional, Iterator
from .restriction import Restriction

class RestrictionGroup(Restriction):
    """
    Groups multiple restrictions applied to a requirement.
    """
    
    def __init__(self, restrictions: List[Restriction], description: Optional[str] = None):
        self.restrictions = restrictions
        self.description = description

    def describe_all(self) -> List[str]:
        return [r.describe() for r in self.restrictions]

    def __iter__(self) -> Iterator[Restriction]:
        return iter(self.restrictions)