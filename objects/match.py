import datetime as dt
from datetime import datetime

class Match:
    def __init__(self, site : str, category : str, date : datetime, teams : list, odds : dict) -> None:
        self._id = self._gen_id(teams, date)
        self._category = category
        self._date = date
        self._site = site
        self._odds = odds
        self._teams = teams

    def _gen_id(self, teams, date) -> str:
        return f"{str(date)}_{' '.join(sorted(teams))}"

    @property
    def id(self) -> str:
        return self._id
    
    @property
    def site(self) -> str:
        return self._site

    @property
    def teams(self) -> list:
        return self._teams
    
    @property
    def date(self) -> datetime:
        return self._date
    
    @property
    def odds(self) -> dict:
        return self._odds

    @property
    def category(self) -> str:
        return self._category
    
    def __str__(self) -> str:
        return f"{self.site} - {self.date} - {self.category} - {self.date} - {self.teams}"

    def __eq__(self, other):
        if not isinstance(other, Match):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)