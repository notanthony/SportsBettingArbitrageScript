from heapq import heappush, nsmallest
import logging
from objects.match import Match


# Best odds for a match
class MatchComparer:
    def __init__(self) -> None:
        self._heaps = {}
        # heap {
        #   bet: {
        #       result: odds
        #       }
        #   }
        #

    @property
    def heaps(self) -> list:
        return self._heaps

    # @property
    # def n(self) -> int:
    #     return self._n

    def get_best_for_bet_result(self, site, bet, result, n=None) -> list[Match]:
        if bet in self.heaps:
            if not n:
                if not result in self.heaps[bet]:
                    logging.error(
                        f"Result {result} not found in heaps for bet {bet} from site {site}"
                    )
                    return []
                ls = self.heaps[bet][result]
                n = len(ls)
            else:
                # Will never try to get more than the heap has but tries to get a redundant one in case one of the top n is filtered out
                ls = nsmallest(
                    min(n + 1, len(self.heaps[bet][result])), self.heaps[bet][result]
                )
            # Filter out the odds for the site, that is why we grab 1 more just in case (if possible)
            return self._filter(ls, site)[: min(n, len(ls))]
        else:
            return []

    def _filter(self, ls, site):
        return [bet for bet in ls if bet[1].site != site]

    def add_match(self, match: Match):
        values: dict
        for bet, values in match.odds.items():
            if not bet in self.heaps:
                self.heaps[bet] = {}
            for result, ip in values.items():
                if not result in self.heaps[bet]:
                    self.heaps[bet][result] = []
                heappush(self.heaps[bet][result], (ip, match))
