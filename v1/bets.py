class Bet:
    def __init__(self, site, bet, type = '', bet_side = '', hedge_side = '') -> None:
        self._site = site
        self._amount = bet
        self._bet_side = bet_side
        self._hedge_side = hedge_side
        self._type = type

    @property
    def site(self) -> str:
        return self._site

    @property
    def amount(self) -> str:
        return self._amount
    
    @property
    def type(self) -> str:
        return self._type
    
    @property
    def bet_side(self) -> str:
        return self._bet_side
    
    @property
    def hedge_side(self)-> str:
        return self._hedge_side
    
    def __str__(self) -> str:
        return f"{self.site}: {self.type} ${self.amount}"

    

class FreeBet(Bet):
    def __init__(self, site, bet) -> None:
        super().__init__(site, bet, type = 'Free', bet_side = f'- {bet}')

class InsuredBet(Bet):
    def __init__(self, site, bet, win_or_lose) -> None:
        super().__init__(site, bet, type = 'Insured', bet_side = '+'+bet+f'*.45- {bet}' if win_or_lose else f'- {bet}', hedge_side=f'- {bet}*.55')
        self._win_or_lose = win_or_lose
    
    @property
    def win_or_lose(self) -> str:
        return self._win_or_lose

class NormalBet(Bet):
    def __init__(self, site, bet) -> None:
        super().__init__(site, bet, type = 'Normal', bet_side = f'- {bet}', hedge_side = f'-{bet}')

class BonusBet(Bet):
    def __init__(self, site, bet, bonus) -> None:
        super().__init__(site, bet, type = 'Bonus', bet_side=f'+{bet}*{bonus}- {bet}', hedge_side=f'+{bet}*{bonus}- {bet}')
        self._bonus = bonus
    
    @property
    def bonus(self) -> str:
        return self._bonus