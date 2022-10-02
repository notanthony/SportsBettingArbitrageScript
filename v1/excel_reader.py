import pandas as pd
from bets import FreeBet, InsuredBet, NormalBet, BonusBet

class ExcelSheet():
    def __init__(self, fileName) -> None:
        self.df = pd.read_excel(fileName)

    @staticmethod
    def convert_bets(row):
        bet, type, site = str(getattr(row, 'Bets')), getattr(row, 'Type'), getattr(row, 'Site')
        if type == 'Free':
            bet_obj = FreeBet(site, bet)
        elif type == 'Insured':
            bet_obj = InsuredBet(site, bet, win_or_lose=getattr(row, 'WL'))
        elif type == 'Normal':
            bet_obj = NormalBet(site, bet)
        elif type == 'Bonus':
            bet_obj = BonusBet(site, bet, str(getattr(row,'Bonus')))
        return bet_obj

    def parse_bets(self):
        ls = []
        for row in self.df.itertuples():
            if getattr(row, 'Remaining') > 0:
                ls.append(ExcelSheet.convert_bets(row))
        return ls