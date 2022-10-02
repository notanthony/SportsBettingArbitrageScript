import logging
from bs4 import BeautifulSoup as bs
from datetime import datetime
from objects.match import Match
from parsers.site_parser import SiteParser


class Site4Parser(SiteParser):
    file = "html/site_4.txt"

    site = "Site4"

    @staticmethod
    def parse_data():
        with open(Site4Parser.file) as fp:
            matches = []
            soup = bs(fp, "html.parser")
            for section in soup.find_all("[HTML Element]", class_="[Class Name]"):
                matches = matches + Site4Parser._parse_data(section)
        return matches

    @staticmethod
    def _parse_data(section):
        match_list = []

        # Standardizes the category ex. mlb, MLB, major league baseball -> mlb
        category = Site4Parser.standardize_category(section.find(class_="[Class Name]"))

        # Gets all the match trs for a day
        days = section.find_all(class_="[Class Name]")

        if not (category and days):
            logging.error("No days found for " + Site4Parser.site)
            return []

        for day in days:

            # Parses out the date of the match
            date: str = Site4Parser.standardize_date(day.find(class_="[Class Name]"))

            # Standardize the bets ex. moneyline, ml, money line -> moneyline
            bets = SiteParser.parse_bets(
                Site4Parser.site,
                category,
                bet_soup_=day.find_all(class_="[Class Name]"),
            )

            # Skips the first row of the table
            rows = day.findChildren("[HTML Element]")[1:]

            if not (bets and date):
                logging.error("No data found for " + Site4Parser.site)
                return []

            # Matches are groups of two rows so we need to preserve the previous rows data
            counter, date_time, team_names, odds = 0, None, [], {}
            for row in rows:

                if counter != 0 and counter % 2 == 0:
                    # Checks everything is good before adding the match
                    if len(team_names) == 2 and odds and date_time:
                        try:
                            match_list.append(
                                Match("Site4", category, date_time, team_names, odds)
                            )
                        except:
                            logging.warning(
                                "Cannot create match for: "
                                + f"{team_names} {odds} {date_time} {category}"
                            )

                    counter, date_time, team_names, odds = 0, None, [], {}

                # Checks everything is good before adding another row, otherwise theres no point!
                if not (
                    counter % 2 != 0
                    and not date_time
                    or len(team_names) != counter % 2
                    or row.find(class_="[Class Name]")
                ):

                    # Standardizes the date format
                    if time := SiteParser.parse_date_time(
                        Site4Parser.site,
                        date_soup_=row.find(class_="[Class Name]"),
                    ):
                        date_time = Site4Parser.standardize_datetime(date + " " + time)

                    if team_name := SiteParser.parse_team_names(
                        Site4Parser.site,
                        category,
                        team_name_soup_=row.find(class_="[Class Name]"),
                    ):
                        team_names.append(team_name)
                    # Parses the odds
                    cols = row.find_all(
                        "[HTMl Element]", {"class": "[Class Name]"}
                    ) or row.find_all("[HTMl Element]", {"class": "[Class Name]"})

                    if not team_name or not date_time:
                        pass
                    else:
                        decrement = 0
                        for idx, col in enumerate(cols):
                            if not col.find(class_="[Class Name]"):
                                Site4Parser._add_odds(
                                    category,
                                    odds,
                                    col,
                                    idx - decrement,
                                    team_name,
                                    bets,
                                )
                            else:
                                decrement += 1
                counter += 1

        return match_list

    @staticmethod
    def _add_odds(category, odds, col, idx, team_name, bets):
        if not bets[idx] in odds:
            odds[bets[idx]] = {}
        if bets[idx] == "moneyline":
            if odd := SiteParser.odds_conversion(odds_soup_=col):
                odds[bets[idx]][team_name] = odd
        else:
            bet_header = Site4Parser.standardize_bet_header(
                category,
                col.find(class_="[Class Name]"),
            )
            odd = SiteParser.odds_conversion(odds_soup_=col.find(class_="[Class Name]"))
            if bet_header and odd:
                if bets[idx] == "spread":
                    odds[bets[idx]][team_name + bet_header] = odd
                else:
                    odds[bets[idx]][bet_header] = odd

    @staticmethod
    def standardize_bet_header(category, bet_header_soup):
        bet_header = SiteParser.parse_bet_headers(
            Site4Parser.site, category, bet_header_soup_=bet_header_soup
        )
        return bet_header

    @staticmethod
    def standardize_category(category_soup):
        category = SiteParser.parse_category(
            Site4Parser.site, category_soup_=category_soup
        )
        category = category.replace("[Unwanted Chars]", "").replace(
            "[Unwanted Chars]", ""
        )
        return SiteParser.category_dict[category]

    @staticmethod
    def standardize_date(date_soup):
        date = SiteParser.parse_date_time(Site4Parser.site, date_soup_=date_soup)
        date = SiteParser.replace_td_tmr(date)
        date = SiteParser.remove_date_suffixes(date)
        date = SiteParser.append_year(date)
        return date

    @staticmethod
    def standardize_datetime(date):
        return Site4Parser.convert_date_str(date).replace(minute=0)

    @staticmethod
    def convert_date_str(date):
        return datetime.strptime(date, "[Date Format]")
