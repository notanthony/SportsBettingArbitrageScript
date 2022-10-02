from sympy import solve, Symbol, Eq
from enum import Enum
from parsers.site_parser import SiteParser
from abc import ABC, abstractmethod


class BetType(Enum):
    NORMAL = "Normal"
    PROFIT_BOOST = "Profit Boost"
    INSURED = "Insured"
    FREE = "Free"


class BetRules(ABC):
    @abstractmethod
    def __init__(self, max_bet, bonus, min_odds):
        self._bonus = bonus
        self._max_bet = max_bet
        self._min_odds = SiteParser.odds_conversion(odds=min_odds)

    @property
    def max_bet(self):
        return self._max_bet

    @property
    def min_odds(self):
        return self._min_odds

    @property
    def bonus(self):
        return self._bonus

    def qualifies(self, odds):
        return self.odds_qualify(odds)

    @abstractmethod
    def get_bonus_amount(self, *args, **kwargs):
        pass

    def odds_qualify(self, odds):
        # Bit of a misnomer, lets say the odds have to be less than 50% then at minimum you need to bet on something less than .5 implied probability
        return odds <= self.min_odds


class BonusRules(BetRules):
    def __init__(self, max_bet=float("inf"), bonus=0, min_odds="1.0"):
        super().__init__(max_bet, bonus, min_odds)

    def get_bonus_amount(self, bet, odds):
        if self.qualifies(odds):
            return min(self.max_bet, bet)
        return 0

    def get_bonus_payout(self, bet, odds):
        return self.get_bonus_amount(bet, odds) * self.bonus


class ProfitBoostRules(BetRules):
    def __init__(self, max_bet, bonus=0, min_odds="1.0", max_winnings=float("inf")):
        super().__init__(bonus, max_bet, min_odds)
        self._max_winnings = max_winnings
        self._max_odds = self.get_max_odds()

    @property
    def max_winnings(self):
        return self._max_winnings

    @property
    def max_odds(self):
        return self._max_odds

    def get_boosted_odds(self, odds):
        return ProfitBoostRules.calc_odds_boost(odds, self.bonus)

    def get_bonus_amount(self, odds, bet=float("inf"), boosted=False):
        boosted_odds = self.get_boosted_odds(odds) if not boosted else odds
        if self.qualifies(odds):
            if boosted_odds < self.max_odds:
                max_bet_for_odds = self.get_max_bet(boosted_odds)
                return min(self.max_bet, bet, max_bet_for_odds)
            return min(self.max_bet, bet)
        return 0

    def get_max_odds(self, bet=None):
        if self.max_winnings == float("inf"):
            return 0
        bet = min(self.max_bet, bet) if bet else self.max_bet
        max_boosted_odds = Symbol("max_boosted_odds")
        # Calculates the odds that would return the max winnings for the max bet
        eq = Eq(bet / max_boosted_odds - bet, self._max_winnings)
        return solve(eq, max_boosted_odds)[0]

    def get_max_bet(self, odds):
        if odds == 0:
            return float("inf")
        max_bet = Symbol("max_bet")
        # Calculates the odds that would return the max winnings for the max bet
        eq = Eq(max_bet / odds - max_bet, self._max_winnings)
        return solve(eq, max_bet)[0]

    # Payout doesnt need to be calculated here, it is calculated in the bet class since it depends on the other variables

    @staticmethod
    def calc_odds_boost(odds, boost):
        x = ((1 / odds) - 1) * (1 + boost) + 1
        return 1 / x
