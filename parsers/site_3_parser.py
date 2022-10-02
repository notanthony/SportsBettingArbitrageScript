import logging
from bs4 import BeautifulSoup as bs
from datetime import datetime
from objects.match import Match
from parsers.site_parser import SiteParser


class Site3Parser(SiteParser):
    file = "html/site_3.txt"

    site = "Site3"

    @staticmethod
    def parse_data():
        with open(Site3Parser.file) as fp:
            match_list = []
            soup = bs(fp, "html.parser")
            for section in soup.find_all("[Class Name]"):
                match_list = match_list + Site3Parser._parse_data(section)
        return match_list

    @staticmethod
    def _parse_data(section):
        match_list = []

        category = Site3Parser.standardize_category(section.find(class_="[Class Name]"))

        bets = SiteParser.parse_bets(
            Site3Parser.site,
            category,
            bet_soup_=section.find_all(class_="[Class Name]"),
        )

        # Gets all the match divs
        matches = section.find_all(class_="[Class Name]")

        if not (bets and category and matches):
            logging.error("No data found for " + Site3Parser.site)
            return []

        for match in matches:
            if match.find(class_="[Class Name]"):
                # Standardizes the date format
                date_time: datetime = Site3Parser.standardize_date(
                    match.find(class_="[Class Name]")
                )

                # Parses out the team_names
                team_names = SiteParser.parse_team_names(
                    Site3Parser.site,
                    category,
                    team_name_soup_=match.find(
                        "[HTMl Element]", {"class": "[Class Name]"}
                    ).find_all("[HTMl Element]", {"class": "[Class Name]"}),
                )

                # Parses out the odds
                odds = {}
                cols = match.find_all(class_="[Class Name]")

                if len(cols) != len(bets):
                    logging.warning("Number of bets does not match number of columns")
                if not (date_time and team_names and len(team_names) == 2):
                    pass
                else:
                    for idx, col in enumerate(cols):
                        if col.findChildren():
                            try:
                                Site3Parser._add_odds(
                                    category, odds, col, idx, team_names, bets
                                )
                            # TODO Fix this
                            except Exception as e:
                                logging.error(
                                    "Error parsing odds for "
                                    + Site3Parser.site
                                    + " "
                                    + str(e)
                                )

                if date_time and team_names and odds:
                    match_list.append(
                        Match("Site3", category, date_time, team_names, odds)
                    )

        return match_list

    @staticmethod
    def _add_odds(category, odds, col, idx, team_names, bets):
        odd_soup = SiteParser.odds_conversion(
            odds_soup_=col.find_all(class_="[Class Name]")
        )

        if not odd_soup:
            return None

        if not bets[idx] in odds:
            odds[bets[idx]] = {}

        if bets[idx] == "moneyline":
            for idx2, odd in enumerate(odd_soup):
                odds[bets[idx]][team_names[idx2]] = odd
        else:
            if bet_headers := SiteParser.parse_bet_headers(
                Site3Parser.site,
                category,
                bet_header_soup_=col.find_all(class_="[Class Name]"),
            ):
                for idx2, bet_header in enumerate(bet_headers):
                    if bets[idx] == "spread":
                        odds[bets[idx]][team_names[idx2] + bet_header] = odd_soup[idx2]
                    else:
                        odds[bets[idx]][bet_header] = odd_soup[idx2]

    @staticmethod
    def standardize_date(date_soup):
        date = SiteParser.parse_date_time(Site3Parser.site, date_soup_=date_soup)
        date = SiteParser.remove_at_symbol(date)
        date = SiteParser.remove_periods_from_am_pm(date)
        date = SiteParser.append_year(date)
        # TODO - Fix this
        try:
            date = SiteParser.get_date_from_day(date)
        except ValueError:
            return None
        return Site3Parser.convert_date_str(date)

    @staticmethod
    def convert_date_str(date):
        return datetime.strptime(date, "[Date Format]").replace(minute=0)

    @staticmethod
    def standardize_category(category_soup):
        category = SiteParser.parse_category(
            Site3Parser.site, category_soup_=category_soup
        )
        split = category.split("/ ")
        category = split[len(split) - 1]
        return category
