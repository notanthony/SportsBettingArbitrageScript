import logging
from unicodedata import category
from bs4 import BeautifulSoup as bs
from datetime import datetime
from objects.match import Match
from parsers.site_parser import SiteParser


class Site2Parser(SiteParser):
    file = "html/site_2.txt"

    site = "Site2"

    @staticmethod
    def parse_data():
        with open(Site2Parser.file) as fp:
            match_list = []
            soup = bs(fp, "html.parser")
            for match in soup.find_all(class_="[Class Name]"):
                if parsed_match := Site2Parser._parse_data(match):
                    match_list.append(parsed_match)
        return match_list

    @staticmethod
    def _parse_data(match):
        # Parses out the category
        category = Site2Parser.standardize_category(match.find(class_="[Class Name]"))

        # Parses out the date of the match
        date_time: datetime = Site2Parser.standardize_datetime(
            category, match.find(class_="[Class Name]")
        )

        # Parses out the team_names
        team_names = SiteParser.parse_team_names(
            Site2Parser.site,
            category,
            team_name_soup_=match.find_all("[HTMl Element]", {"class": "[Class Name]"}),
        )

        # Parses out the mainline bets
        bets = SiteParser.parse_bets(
            Site2Parser.site,
            category,
            bet_soup_=match.find_all("[HTMl Element]", {"class": "[Class Name]"}),
        )

        # Parses out the odds
        odds = {}

        # Bet headers for mainline non moneyline odds
        bet_headers = SiteParser.parse_bet_headers(
            Site2Parser.site,
            category,
            bet_header_soup_=match.find_all(
                "[HTMl Element]", {"class": "[Class Name]"}
            ),
        )

        if not (team_names and len(team_names) == 2 and date_time and bets):
            return None

        # Mainline bets
        num_of_bets = len(bets)
        money_line_count = 0
        main_odds = SiteParser.odds_conversion(
            odds_soup_=match.find_all("HTMl Element", {"class": "[Class Name]"})
        )
        # TODO fix this
        try:
            for idx, main_odd in enumerate(main_odds):
                if not bets[idx % num_of_bets] in odds:
                    odds[bets[idx % num_of_bets]] = {}
                if bets[idx % num_of_bets] == "moneyline":
                    odds[bets[idx % num_of_bets]][
                        team_names[idx // num_of_bets]
                    ] = main_odd
                    money_line_count += 1
                elif bets[idx % num_of_bets] == "spread":
                    odds[bets[idx % num_of_bets]][
                        team_names[idx // num_of_bets]
                        + bet_headers[idx - money_line_count]
                    ] = main_odd
                else:
                    odds[bets[idx % num_of_bets]][
                        bet_headers[idx - money_line_count]
                    ] = main_odd
        except IndexError:
            return None

        if odds:
            return Match("Site2", category, date_time, team_names, odds)

    @staticmethod
    def standardize_datetime(category, date_soup):
        date = SiteParser.parse_date_time(Site2Parser.site, date_soup_=date_soup)
        date = date.replace(category, "")
        date = SiteParser.replace_td_tmr(date)
        date = SiteParser.remove_date_suffixes(date)
        date = SiteParser.append_year(date)
        return Site2Parser.convert_date_str(date)

    @staticmethod
    def convert_date_str(date):
        return datetime.strptime(date, "[Date Format]").replace(minute=0)

    @staticmethod
    def standardize_category(category_soup):
        try:
            return SiteParser.parse_category(
                Site2Parser.site, category_soup_=category_soup.next
            )
        except:
            logging.error(f"No category found for {Site2Parser.site}")
            return None
