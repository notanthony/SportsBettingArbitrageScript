from excel_reader import ExcelSheet
import logging
import odds 
import os
def main():
    sheet = ExcelSheet(os.getcwd() + '/v1/Sample.xlsx')
    bets = sheet.parse_bets()
    ls, rs = [], []
    while True:
        cmd = input('Please enter a command (-h for help):')
        if cmd == '-h':
            print('-b for bets \n-ls to add bets to the ls\n-rs to add bets to the rs\n-f to see the current ls rs\n-calc to calculate')
        if cmd == '-b':
            for idx, bet in enumerate(bets):
                print(idx, str(bet), f"Remaining: {sheet.df.at[idx, 'Remaining']}")
        if cmd == '-ls' or cmd == '-rs':
            arr = ls if cmd == '-ls' else rs 
            while True:
                cmd = input('Bet to add/remove (/b to exit): ')
                if cmd == '/b':
                    break
                try:
                    idx = int(cmd)
                except:
                    pass
                if bets[idx] in arr:
                    arr.remove(bets[idx]) 
                    sheet.df.at[idx, 'Remaining'] += 1
                else:
                    if sheet.df.at[idx, 'Remaining'] > 0:
                        arr.append(bets[idx]) 
                        sheet.df.at[idx, 'Remaining'] -= 1
                    else:
                        logging.error('No bets remaining')
        if cmd == '-f':
            print('LS:','\n'.join(str(p) for p in ls),'\nRS:','\n'.join(str(p) for p in rs))
        if cmd == '-calc':
            print(odds.calc_bets(ls, rs))

if __name__ == "__main__":
    main()