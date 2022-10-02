from heapq import heappush
import logging
from objects.match import Match
from comparators.match_comparator import MatchComparer
from objects.bets import (
    FreeBet,
    InsuredBet,
    NormalBet,
)
from functools import wraps
import time

from parsers.site_parser import SiteParser


def timeit(func):
    @wraps(func)
    def timeit_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time
        print(f"Function {func.__name__}{args} {kwargs} Took {total_time:.4f} seconds")
        return result

    return timeit_wrapper


# Best bets given a set of matches
class BetComparer:
    def __init__(self, scale=100) -> None:
        self.match_comparers = {}
        self._scale = scale

    @property
    def scale(self) -> int:
        return self._scale

    def add_match(self, match: Match):
        if match not in self.match_comparers:
            self.match_comparers[match] = MatchComparer()
        self.match_comparers[match].add_match(match)

    # @timeit
    # Finds the best [num_returned] hedges for the given matches for both sides of the match
    def _get_best_given_matches(self, bet1, matches: list):
        heap_return = []
        for match in matches:
            items = match.odds.items()
            try:
                match_comparer: MatchComparer = self.match_comparers[match]
            except KeyError:
                logging.error(f"Match {match} not found in match_comparers")
                items = []
            for bet, values in items:
                for result, odds1 in values.items():
                    bet1.odds = odds1
                    for other_result in values.keys():
                        if result != other_result:
                            heap = match_comparer.get_best_for_bet_result(
                                match.site, bet, other_result
                            )
                            for x in heap:
                                b2 = NormalBet(odds=x[0])
                                sol = b2.calc_matching_bets([], [bet1])
                                if sol:
                                    bet_needed, payout, spent = sol
                                    ev = payout - spent
                                    output = f"{bet}\n{str(match)}:\n${round(bet1.bet,2)} @ {SiteParser.ip_to_american(odds1)} on {result}\n{str(x[1])}:\n${round(bet_needed,2)} @ {SiteParser.ip_to_american(x[0])} on {other_result}\nProfit: {round(ev,2)}"
                                    if type(bet1) == FreeBet:
                                        output += f"\nEfficency: {round(round(ev,2)/round(bet1.bet,2)*100, 2)}%"
                                        output += f"\nsolve {bet1.bet}/{odds1} - {bet1.bet} = x/{x[0]}"
                                    elif type(bet1) == InsuredBet:
                                        output += f"\nEfficency: {round(round(ev,2)/round(bet1.bet*.7,2)*100, 2)}%"

                                        # Output that can be plugged into wolfram alpha (just to double check)
                                        # Free API requests are very limited so I did not bother using the API
                                        output += f"\nsolve {bet1.bet}/{odds1} = x/{x[0]} + {bet1.bet} * .7"
                                        output += f"\n{bet_needed}/{x[0]} - {bet1.bet} - {bet_needed} + {bet1.bet} * .7"

                                    heappush(heap_return, (ev, output))
                                else:
                                    logging.debug(f"No match for {bet1} and {b2}")
        return heap_return
