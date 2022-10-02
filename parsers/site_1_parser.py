from bs4 import BeautifulSoup as bs
from datetime import datetime
from objects.match import Match
from parsers.site_parser import SiteParser
import logging


class Site1Parser(SiteParser):
    file = "html/site_1.txt"

    site = "SITE_1"

    # Splits the categories
    @staticmethod
    def parse_data():
        match_list = []
        with open(Site1Parser.file) as fp:
            soup = bs(fp, "html.parser")
            for section in soup.find_all(
                "[HTMl Element]",
                class_="[Class Name]",
            ):
                match_list = match_list + Site1Parser._parse_data(section)
        return match_list

    # Parses data from category views
    @staticmethod
    def _parse_data(section):
        match_list = []

        # Standardizes the category ex. mlb, MLB, major league baseball -> mlb
        category = Site1Parser.standardize_category(section.find(class_="[Class Name]"))

        # Standardize the bets ex. moneyline, ml, money line -> moneyline
        bets = SiteParser.parse_bets(
            Site1Parser.site,
            category,
            bet_soup_=section.find_all(class_="[Class Name]"),
        )

        # Gets all the match divs
        matches = section.find_all(class_="[Class Name]")
        if not (bets and category and matches):
            logging.error("No data found for " + Site1Parser.site)
            return []

        for match in matches:
            # Wont parse if the match if it is live
            if not match.find(class_="[Class Name]") and not match.find(
                class_="[Class Name]"
            ):

                # Standardizes the date format
                date_time: datetime = Site1Parser.standardize_datetime(
                    match.find(class_="[Class Name]")
                )

                # Standardizes the team names
                team_names = SiteParser.parse_team_names(
                    Site1Parser.site,
                    category,
                    team_name_soup_=match.find(
                        "[HTMl Element]",
                        {"class": "[Class Name]"},
                    ).find_all("[HTMl Element]"),
                )

                # Get the odds for the bets
                odds = {}
                cols = match.find_all(class_="[Class Name]")

                if not cols or len(cols) != len(bets):
                    logging.warning(
                        "Number of odds does not match number of bets "
                        + Site1Parser.site
                    )
                if not (date_time and team_names and len(team_names) == 2):
                    pass
                else:
                    for idx, col in enumerate(cols):
                        if not col.find(class_="[Class Name]"):
                            Site1Parser._add_odds(
                                category, odds, col, idx, team_names, bets
                            )

                if odds:
                    match_list.append(
                        Match("SITE_1", category, date_time, team_names, odds)
                    )

        return match_list

    @staticmethod
    def _add_odds(category, odds, col, idx, team_names, bets):
        odds_soup = SiteParser.odds_conversion(
            odds_soup_=col.find_all(class_="[Class Name]")
        )

        if not odds_soup:
            return None

        if not bets[idx] in odds:
            odds[bets[idx]] = {}

        if bets[idx] == "moneyline":
            for idx2, odd in enumerate(odds_soup):
                odds[bets[idx]][team_names[idx2]] = odd
        else:
            if bet_headers := SiteParser.parse_bet_headers(
                Site1Parser.site,
                category,
                bet_header_soup_=col.find_all(class_="[Class Name]"),
            ):
                for idx2, bet_header in enumerate(bet_headers):
                    if bets[idx] == "spread":
                        odds[bets[idx]][team_names[idx2] + bet_header] = odds_soup[idx2]
                    else:
                        odds[bets[idx]][bet_header] = odds_soup[idx2]

    @staticmethod
    def standardize_datetime(date_soup):
        date = SiteParser.parse_date_time(Site1Parser.site, date_soup_=date_soup)
        if not date:
            return None
        # This will not work for new years but I am not sure how sites even handle that so for now I leave in this warning to future me
        if datetime.now().month == 12 and datetime.now().day > 29:
            logging.error("Datetime maybe broken by new years")
        date = SiteParser.append_year(date)
        return Site1Parser.convert_date_str(date)

    @staticmethod
    def standardize_category(category_soup):
        category = SiteParser.parse_category(
            Site1Parser.site, category_soup_=category_soup
        )
        return SiteParser.category_dict[category]

    @staticmethod
    def convert_date_str(date):
        return datetime.strptime(date, "[Date Format]").replace(minute=0)
