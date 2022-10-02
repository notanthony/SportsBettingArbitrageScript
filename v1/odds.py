import logging
import re 
import os 
import wolframalpha as wa
from bets import Bet
client  = wa.Client(os.environ['WOLFRAM_ALPHA_API_KEY'])


# Will convert american/decimal odds to implied probability
def odds_conversion(odds):
    ip = -1
    if re.fullmatch(r'[\-\+]\d{3,}', odds):
        # Parse out the number 
        num = int(re.search(r'\d+', odds)[0])
        # American odds formula
        ip = num if '-' in odds else 100 / (num + 100)
        logging.info(f"American odds inputed: {odds} with implied probability = {ip}")
    elif re.fullmatch(r'[1-9]\.\d+', odds):
        #Decimal odds formula
        ip = (1/ float(odds)) 
        logging.info(f"Decimal odds inputed: {odds} with implied probability = {ip}")
    else:
        logging.error(f'Invalid odds input: {odds}')
    return ip

#Validate bets are floats or ints > 0 
def valid_bet(bet):
    # Ex. will match 123 or 12.X or X.12 
    if not re.fullmatch(r'(\d+)|(\d*\.\d+)|(\d+\.\d*)', bet):
        logging.error(f'Invalid bet input: {bet}')
        return False 
    return True

def calc_bets(ls, rs):
    total_ls, total_rs, calc_ls, calc_rs = 0,0,'', ''
    bet : Bet
    for bet in ls:
        total_ls+= float(bet.amount)
        calc_ls += bet.bet_side
        calc_rs += bet.hedge_side
    for bet in rs:
        total_rs+= float(bet.amount)
        calc_ls += bet.hedge_side
        calc_rs += bet.bet_side
    print(f'solve {total_ls}/x {calc_ls} = {total_rs}/(1-x) {calc_rs}')
    logging.info(f'solve {total_ls}/x {calc_ls} = {total_rs}/(1-x) {calc_rs}')
    query = client.query(f'solve {total_ls}/x {calc_ls} = {total_rs}/(1-x) {calc_rs}')
    return next(query.results).text
    
def match_bets(odds = 'x',bet_1 = 'y', bet_2 = 'z', free_1 = False, free_2 = False):
    ip_odds =  odds_conversion(odds) if odds != 'x' else odds
    if (bet_1 == 'y' or valid_bet(bet_1)) and (bet_2 == 'z' or valid_bet(bet_2)):
        formula = f"solve {bet_1}/(1-{ip_odds}) - {'0' if free_2 else bet_2} - {bet_1 if free_1 else '0'} = {bet_2}/{ip_odds} - {'0' if free_1 else bet_1} - {bet_2 if free_2 else '0'}"
        res = client.query(formula)
        res = next(res.results).text
    else:
        logging.info(f"Bet matching failed")
    return -1

if __name__ == "__main__":
    match_bets(bet_1 = '2500', bet_2 = '1240', free_1= True, free_2=False)