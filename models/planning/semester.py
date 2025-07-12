from typing import Optional

class Semester:
    """
    Immutable data container representing a single academic term.
    Holds metadata for semester identification. No scheduling logic.
    """
    MAX_CREDITS = 18

    def __init__(self, season: str, year: int):
        self.season = season
        self.year = year

    @property
    def term_id(self) -> str:
        return f"{self.season} {self.year}"

    def __repr__(self):
        return f"<Semester {self.term_id}, max_credits={self.MAX_CREDITS}>"

 