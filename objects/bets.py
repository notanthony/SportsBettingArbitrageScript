from abc import ABC, abstractmethod
import logging
from sympy import solve, Symbol, Eq
from objects.bet_rules import BonusRules, ProfitBoostRules, BetType


def get_obj_variables(func):
    def wrapper(self, *args, **kwargs):
        # Get the variables
        try:
            known_variables, unknown_variables = (
                self._get_known_variables(),
                self._get_unknown_variables(),
            )
        except Exception as err:
            logging.error(f"Error getting known and unknown values: {err}")
            return None
        try:
            return func(
                self,
                *args,
                known_variables=known_variables,
                unknown_variables=unknown_variables,
                **kwargs,
            )
        except RuntimeError as err:
            logging.error(f"Error substituting variables: {err}")
            return None

    return wrapper


def verify_calc_bet_ev(func):
    @get_obj_variables
    def wrapper(self, **kwargs):
        # Ensure no unknown variables are passed
        if unknown_variables := kwargs.get("unknown_variables", []):
            logging.error(f"Cannot calculate payout with unknowns: {unknown_variables}")
            return None
        # Ensure known variables are passed
        if known_variables := kwargs.get("known_variables", None):
            try:
                return func(self, known_variables)
            except Exception as err:
                logging.error(f"Error calculating bet ev: {err}")
                return None
        else:
            logging.error(f"Cannot calculate payout with no known variables")
            return None

    return wrapper


def verify_calc_matching_bets(func):
    @get_obj_variables
    def wrapper(self, *args, **kwargs):
        # Ensure only one unknown variable is passed
        unknown_variables, known_variables = kwargs.get(
            "unknown_variables", []
        ), kwargs.get("known_variables", None)
        if len(unknown_variables) != 1:
            logging.error(
                f'Can only solve for one unknown! Given {unknown_variables if unknown_variables else "None"}'
            )
            return None
        if not known_variables:
            logging.error(f"Cannot calculate matching bet with no known variables")
            return None
        try:
            payout, spent = Bet._sum_ls_rs(args[0], args[1])
            if payout == 0:
                logging.error(f"Cannot match bet to zero, trivial case")
                return None
        except Exception as err:
            logging.error(f"Error calculating payout to match: {err}")
            return None
        try:
            return func(self, payout, spent, known_variables, unknown_variables[0])
        except Exception as err:
            logging.error(f"Error calculating bet ev: {err}")
            return None

    return wrapper


class Bet(ABC):
    LEFT, RIGHT = True, False
    BET, ODDS = Symbol("bet"), Symbol("odds")

    @abstractmethod
    def __init__(self, bet=None, odds=None, bonus=BonusRules()) -> None:
        self._eq = Eq(Bet.BET / Bet.ODDS, 0)
        self._bonus, self._odds, self._bet = bonus, odds, bet

    @property
    @abstractmethod
    def bet_type(self):
        pass

    @property
    def eq(self) -> Eq:
        return self._eq

    @property
    def odds(self) -> float:
        return self._odds

    @property
    def bet(self) -> float:
        return self._bet

    @property
    def bonus(self) -> BonusRules:
        return self._bonus

    @bet.setter
    def bet(self, value):
        self._bet = value

    @odds.setter
    def odds(self, value):
        self._odds = value

    def _get_known_variables(self):
        sub_ins = {}
        if self.bet:
            sub_ins[Bet.BET] = self.bet
        if self.odds:
            sub_ins[Bet.ODDS] = self.odds
        return sub_ins

    def _get_unknown_variables(self):
        result = []
        if not self.bet:
            result.append(Bet.BET)
        if not self.odds:
            result.append(Bet.ODDS)
        return result

    def add_to_ls(self, value):
        self._eq = Bet.add_to_eq(self.eq, value, Bet.LEFT)

    def add_to_rs(self, value):
        self._eq = Bet.add_to_eq(self.eq, value, Bet.RIGHT)

    @staticmethod
    def add_to_eq(eq, value, side):
        n = Symbol("n")
        # temp: n = value
        if side == Bet.LEFT:
            temp = Eq(n, value)
        else:
            temp = Eq(value, n)
        # eq:
        # self.ls is flipped since we put self.ls on the rs so it is: 0 = |self.ls|
        # flipped self.ls + temp -> n + 0 = value + |self.ls|
        eq = Eq(temp, eq)
        return Eq(solve(eq, n)[0], 0)

    @staticmethod
    def _sum_ls_rs(ls_bets: list, rs_bets: list, invert=False):
        total_payout, total_spent = 0, 0
        bet: Bet
        for idx, side in enumerate([ls_bets, rs_bets]):
            for bet in side:
                bet_payout, spent = bet.calc_bet_ev()
                # Vals on the LS should be subtracted so when idx == 0 i.e on the ls we * -1 to subtract
                total_payout += bet_payout * (1 if idx else -1)
                total_spent += spent
        return total_payout * (-1 if invert else 1), total_spent

    def solve_matching_bets(self, payout, known_variables, unknown_variable):
        eq = self.eq.subs(known_variables)
        bet_eq = Bet.add_to_eq(eq, payout, Bet.RIGHT)
        solution = solve(bet_eq, unknown_variable)[0]
        return solution

    @abstractmethod
    def _calc_bonus_payout(self, *args, **kwargs):
        pass

    @abstractmethod
    def calc_bet_ev(self, known_variables={}, unknown_variables=[]):
        pass

    @abstractmethod
    def calc_matching_bets(self, payout, spent, known_variables, unknown_variable):
        pass


class NormalBet(Bet):
    bet_type = BetType.NORMAL

    def __init__(self, bet=None, odds=None, bonus=BonusRules()) -> None:
        super().__init__(bet, odds, bonus)

    def _calc_bonus_payout(self, bet, odds):
        return self.bonus.get_bonus_payout(bet, odds)

    @verify_calc_bet_ev
    def calc_bet_ev(self, known_variables):
        # Unpack known variables
        bet, odds = known_variables[Bet.BET], known_variables[Bet.ODDS]

        base_payout = bet / odds
        bonus_payout = self._calc_bonus_payout(bet, odds)

        # Return total payout and spent
        return base_payout + bonus_payout, bet

    @verify_calc_matching_bets
    def calc_matching_bets(self, payout, spent, known_variables, unknown_variable):
        # Solve for the unknown variable
        known_variables[unknown_variable] = super().solve_matching_bets(
            payout, known_variables, unknown_variable
        )

        # Unpack variables for readability
        bet, odds = known_variables[Bet.BET], known_variables[Bet.ODDS]

        # Calculate final values
        total_spent = bet + spent
        total_payout = payout + self._calc_bonus_payout(bet, odds)

        # Return unknown variable, total payout, total spent
        return known_variables[unknown_variable], total_payout, total_spent


class FreeBet(Bet):
    BET = Symbol("free_bet")
    bet_type = BetType.FREE

    def __init__(
        self, amount_free=0, splitable=False, bet=None, odds=None, bonus=BonusRules()
    ) -> None:
        super().__init__(bet, odds, bonus)
        self._splitable = splitable
        self.add_to_ls(Eq(-FreeBet.BET, 0))
        self._amount_free = amount_free

    @property
    def amount_free(self) -> float:
        return self._amount_free

    @property
    def splitable(self) -> bool:
        return self._splitable

    def get_free_bet_wager(self, bet, amount_free=None):
        amount_free = amount_free if amount_free else self.amount_free
        return 0 if bet < amount_free and not self.splitable else min(amount_free, bet)

    def _calc_bonus_payout(self, bet, odds, amount_free):
        return self.bonus.get_bonus_payout(bet - amount_free, odds)

    # Todo: This is not correct, maybe it is, but I am not sure, I never need to do this though. I am always converting free bets never are they unknown
    @verify_calc_matching_bets
    def calc_matching_bets(self, payout, spent, known_variables, unknown_variable):
        if unknown_variable == Bet.BET:
            # Get the max amount of free bet that can be used
            temp_variables = known_variables | {Bet.BET: FreeBet.BET}
            free_bet_max = super().solve_matching_bets(
                payout, temp_variables, FreeBet.BET
            )
            # Here is the truth table for solving for FreeBet.BET given free_bet_max
            # Case 1: Splitable and free_bet_max >= amount_free -> amount_free
            # Case 2: Splitable and free_bet_max < amount_free -> free_bet_max
            # Case 3: Not splitable and free_bet_max >= amount_free -> amount_free
            # Case 4: Not splitable and free_bet_max < amount_free -> 0
            # This is just get_free_bet_wager
            free_bet_amount = self.get_free_bet_wager(free_bet_max)
        else:
            free_bet_amount = self.get_free_bet_wager(known_variables[Bet.BET])

        known_variables[FreeBet.BET] = free_bet_amount
        known_variables[unknown_variable] = super().solve_matching_bets(
            payout, known_variables, unknown_variable
        )
        bet, odds = known_variables[Bet.BET], known_variables[Bet.ODDS]

        # Calculate final values (factoring in the free bet amount)
        total_spent = bet + spent - free_bet_amount
        total_payout = payout + self._calc_bonus_payout(bet, odds, free_bet_amount)

        # Return unknown variable, total payout and total spent
        return known_variables[unknown_variable], total_payout, total_spent

    @verify_calc_bet_ev
    def calc_bet_ev(self, known_variables):
        # Determine variables
        bet, odds = known_variables[Bet.BET], known_variables[Bet.ODDS]
        free_bet_amount = self.get_free_bet_wager(bet)

        base_payout = bet / odds - free_bet_amount
        bonus_payout = self._calc_bonus_payout(bet, odds, free_bet_amount)

        # Return total payout and spent
        return base_payout + bonus_payout, bet - free_bet_amount


class ProfitBoostBet(Bet):
    bet_type = BetType.PROFIT_BOOST
    BET, ODDS = Symbol("boosted_bet"), Symbol("boosted_odds")

    def __init__(
        self, bet=None, odds=None, bonus=BonusRules(), profit_boost=ProfitBoostRules(0)
    ) -> None:
        super().__init__(bet, odds, bonus)
        self.add_to_ls(
            Eq(
                -ProfitBoostBet.BET / Bet.ODDS
                + ProfitBoostBet.BET / ProfitBoostBet.ODDS,
                0,
            )
        )
        self._profit_boost = profit_boost

    @property
    def profit_boost(self) -> ProfitBoostRules:
        return self._profit_boost

    def _calc_bonus_payout(self, bet, odds):
        return self.bonus.get_bonus_payout(bet, odds)

    @verify_calc_bet_ev
    def calc_bet_ev(self, known_variables):
        # Determine variables
        bet, odds = known_variables[Bet.BET], known_variables[Bet.ODDS]
        profit_boost_amount, profit_boost_odds = self.profit_boost.get_bonus_amount(
            odds, bet=bet
        ), self.profit_boost.get_boosted_odds(odds)

        base_payout = (
            bet - profit_boost_amount
        ) / odds + profit_boost_amount / profit_boost_odds
        # I assumed profit boosted bets will have the same bonus rules as normal bets // I am not sure this is true, dosent really matter
        bonus_payout = self._calc_bonus_payout(bet, odds)

        # Return total payout and spent
        return base_payout + bonus_payout, bet

    # Todo: This is not correct, maybe it is, but I am not sure
    @verify_calc_matching_bets
    def calc_matching_bets(self, payout, spent, known_variables, unknown_variable):
        if unknown_variable == Bet.BET:
            known_variables[ProfitBoostBet.ODDS] = self.profit_boost.get_boosted_odds(
                known_variables[Bet.ODDS]
            )
            temp_variables = known_variables | {Bet.BET: ProfitBoostBet.BET}
            odds = super().solve_matching_bets(
                payout, temp_variables, ProfitBoostBet.BET
            )
            # Same as free bet, the truth table will show that this max can be substituted for the bet amount when we want to determine the profit boost amount
            known_variables[ProfitBoostBet.BET] = self.profit_boost.get_bonus_amount(
                odds
            )
        else:
            # I dont know when this would ever be relevant, and it is way too complicated to calculate so I am going to leave it out for now
            # The best odds are obviously going to be the lowest possible odds that max out the profit boost amount
            raise NotImplementedError(
                "ProfitBoostBet.calc_matching_bets does not support solving for unknown variable ProfitBoostBet.ODDS"
            )

        # Solve for the unknown variable
        known_variables[unknown_variable] = super().solve_matching_bets(
            payout, known_variables, unknown_variable
        )
        bet, odds = known_variables[Bet.BET], known_variables[Bet.ODDS]

        total_spent = bet + spent
        total_payout = payout + self._calc_bonus_payout(bet, odds)
        return known_variables[unknown_variable], total_payout, total_spent


class InsuredBet(Bet):
    BET = Symbol("insured_bet")
    bet_type = BetType.INSURED

    def __init__(
        self, amount_insured=0, splitable=False, bet=None, odds=None, bonus=BonusRules()
    ) -> None:
        super().__init__(bet, odds, bonus)
        self._splitable = splitable
        self.add_to_ls(Eq(-InsuredBet.BET * 0.7, 0))
        self._amount_insured = amount_insured

    @property
    def amount_insured(self) -> float:
        return self._amount_insured

    @property
    def splitable(self) -> bool:
        return self._splitable

    def get_amount_insured(self, bet, amount_insured=None):
        amount_insured = amount_insured if amount_insured else self.amount_insured
        return (
            0
            if bet < amount_insured and not self.splitable
            else min(amount_insured, bet)
        )

    def _calc_bonus_payout(self, bet, odds):
        return self.bonus.get_bonus_payout(bet, odds)

    # Todo: This is not correct, maybe it is, but I am not sure
    @verify_calc_matching_bets
    def calc_matching_bets(self, payout, spent, known_variables, unknown_variable):
        if unknown_variable == Bet.BET:
            # Get the max amount of free bet that can be used
            temp_variables = known_variables | {Bet.BET: InsuredBet.BET}
            insured_bet_max = super().solve_matching_bets(
                payout, temp_variables, InsuredBet.BET
            )
            insured_bet_amount = self.get_amount_insured(insured_bet_max)
        else:
            insured_bet_amount = self.get_amount_insured(known_variables[Bet.BET])

        known_variables[InsuredBet.BET] = insured_bet_amount
        known_variables[unknown_variable] = super().solve_matching_bets(
            payout, known_variables, unknown_variable
        )
        bet, odds = known_variables[Bet.BET], known_variables[Bet.ODDS]

        # Calculate final values
        total_spent = bet + spent - insured_bet_amount * 0.7
        total_payout = payout + self._calc_bonus_payout(bet, odds)

        # Return unknown variable, total payout and total spent
        return known_variables[unknown_variable], total_payout, total_spent

    @verify_calc_bet_ev
    def calc_bet_ev(self, known_variables):
        # Determine variables
        bet, odds = known_variables[Bet.BET], known_variables[Bet.ODDS]
        insured_bet_amount = self.get_amount_insured(bet)

        base_payout = bet / odds - insured_bet_amount * 0.7
        bonus_payout = self._calc_bonus_payout(bet, odds)

        # Return total payout and spent
        return base_payout + bonus_payout, bet - insured_bet_amount * 0.7
