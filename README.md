# Final Version

By copy pasting in HTML data from the sites the parsers will convert it into matches with different betting lines. Then it will compare the different matches for the bets you want to place and return the best ones. I have anonymized the site data and removed the HTML. Because of this, this version will not actually run, but here is some sample output

### Insured Bet

moneyline

Site 1 - 2022-10-02 13:00:00 - nfl - 2022-10-02 13:00:00 - ['jaguars', 'eagles']:

$1000 @ +235 on jaguars

Site 2 - 2022-10-02 13:00:00 - nfl - 2022-10-02 13:00:00 - ['jaguars', 'eagles']:

$1923.97 @ -265 on eagles

Profit: 426.03

Efficency: 60.86%

### Normal Bet

moneyline

Site 1 - 2022-10-02 13:00:00 - nfl - 2022-10-02 13:00:00 - ['jaguars', 'eagles']:

$19.4 @ -260 on eagles

Site 2 - 2022-10-02 13:00:00 - nfl - 2022-10-02 13:00:00 - ['jaguars', 'eagles']:

$8.14 @ +230 on jaguars

Profit: -0.68

### Free Bet

moneyline

Site 1 - 2022-10-01 19:00:00 - ncaaf - 2022-10-01 19:00:00 - ['uab blazers', 'rice owls']:

$600 @ +330 on rice owls

Site 2 - 2022-10-01 19:00:00 - ncaaf - 2022-10-01 19:00:00 - ['uab blazers', 'rice owls']:

$1540.00000000000 @ -350 on uab blazers

Profit: 440.000000000000

Efficency: 73.33%

solve 600/0.23255813953488372 - 600 = x/0.7777777777777778

### Profit Boost

Max bet of 250 with a 100% bonus

b2_boost = ProfitBoostRules(250, bonus=1)

b2 = ProfitBoostBet(250, profit_boost=b2_boost)

spread

Site 1 - 2022-10-02 16:00:00 - mlb - 2022-10-02 16:00:00 - ['white sox', 'padres']:

$250 @ +150 on padres-1.5

Site 2 - 2022-10-02 16:00:00 - mlb - 2022-10-02 16:00:00 - ['white sox', 'padres']:

$615.38 @ -160 on white sox+1.5

Profit: 134.62

# V2 Matching

### RUN

To run this simply run site_parser.py

# Introduction

This was version 2 of my attempt to automate betting. This had a heavy focus on finding good hedges betweens scraped data while my other v1 version was primarily focused on computing the odds you need to look for.
I plan on doing a version 3 that will combine the more advanced math of v1 with the increased automation of v2

Some online gambling sites offer a deposit match with a catch, you have to be X times the deposit to release the bonus. With sports betting there are times where the odds on two seperate sites are close to equal or even greater than equal (arbitrage opportunity.)

For example, lets say Site A will offer a 100% bonus match on $100 but with a 5x playthrough to unlock the bonus.
That means one must bet $500 before they can withdraw the extra $100. Lets say they can find bets where thet only lose 5%. Then thet would lose a total of 500\*.05 = 25 and then unlock the $100 bonus meaning they made $75.

The only issue is these kinds of bets are hard to spot and it takes time

Phase 1
Planning:

MVP
-> Data
Copy paste HTML (Caveman)

-> Basic Processing - Site - Match Info (Teams, Date) - Odds (Moneyline for now)

-> Generate Bets - Minimize loss on hedges for rollover fufillment bets - Print

# Commands to periodically update the html text for others to test with :)

git update-index --skip-worktree html/site_1.txt
git update-index --skip-worktree html/site_3.txt
git update-index --skip-worktree html/site_2.txt
git update-index --skip-worktree html/site_4.txt
git update-index --skip-worktree html/site_5.txt

git update-index --no-skip-worktree html/site_1.txt
git update-index --no-skip-worktree html/site_3.txt
git update-index --no-skip-worktree html/site_2.txt
git update-index --no-skip-worktree html/site_4.txt
git update-index --no-skip-worktree html/site_5.txt

# DISCLAIMER

This automation is simply a fun educational exercise! It is against most betting sites TOS to use the place mathing bets and I would never!

Also see MIT License

MIT License

Copyright (c) 2022 notanthony

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
