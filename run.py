from heapq import heappop
from parsers.site_5_parser import Site5Parser
from parsers.site_2_parser import Site2Parser
from parsers.site_4_parser import Site4Parser
from parsers.site_1_parser import Site1Parser
from parsers.site_3_parser import Site3Parser
from parsers.site_6_parser import Site6Parser
from comparators.bet_comparator import BetComparer
from objects.bets import (
    NormalBet,
    BonusRules,
    InsuredBet,
    FreeBet,
    InsuredBet,
    ProfitBoostBet,
    ProfitBoostRules,
)


if __name__ == "__main__":
    site_1 = Site1Parser()
    site_1_parsed = site_1.parse_data()
    site_2 = Site2Parser()
    site_2_parsed = site_2.parse_data()
    site_3 = Site3Parser()
    site_3_parsed = site_3.parse_data()
    site_4 = Site4Parser()
    site_4_parsed = site_4.parse_data()
    site_5 = Site5Parser()
    site_5_parsed = site_5.parse_data()
    site_6 = Site6Parser()
    site_6_parsed = site_6.parse_data()

    bet_comparer = BetComparer()

    for x in [site_1_parsed, site_2_parsed]:
        for y in x:
            bet_comparer.add_match(y)
    for bet, site in {
        NormalBet(bet=5000): site_1_parsed,
        NormalBet(
            bet=5000, bonus=BonusRules(bonus=1.0 / 6.0, min_odds="-200")
        ): site_1_parsed,
        FreeBet(bet=600, amount_free=600): site_2_parsed,
        ProfitBoostBet(250, profit_boost=ProfitBoostRules(250, bonus=1)): site_3_parsed,
        InsuredBet(bet=1000, amount_insured=1000): site_4_parsed,
    }.items():
        val = bet_comparer._get_best_given_matches(bet, site)
        while val:
            x = heappop(val)
            print(x[1])
        pass
