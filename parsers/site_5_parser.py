from bs4 import BeautifulSoup as bs
from datetime import datetime
from objects.match import Match
from parsers.site_parser import SiteParser
import logging
import datetime as dt
import re


class Site5Parser(SiteParser):
    file = "html/site_5.txt"

    site = "Site5"

    # Splits the categories
    @staticmethod
    def parse_data():
        match_list = []
        with open(Site5Parser.file) as fp:
            soup = bs(fp, "html.parser")
            for section in soup.find_all("[HTML Element]", class_="[Class Name]"):
                match_list = match_list + Site5Parser._parse_data(section)
        return match_list

    # Parses data from category views
    @staticmethod
    def _parse_data(section):
        match_list = []

        # Standardizes the category ex. mlb, MLB, major league baseball -> mlb
        category = Site5Parser.standardize_category(section.find(class_="[Class Name]"))

        # It has to break for invalid categories or it will throw a bunch of flakes
        if not category:
            return match_list

        # Standardize the bets ex. moneyline, ml, money line -> moneyline
        bets = SiteParser.parse_bets(
            Site5Parser.site,
            category,
            bet_soup_=section.find_all(class_="[Class Name]"),
        )

        # Gets all the match divs
        matches = section.find_all(class_="[Class Name]")
        if not (bets and category and matches):
            logging.error("No data found for " + Site5Parser.site)
            return []

        for match in matches:
            # Wont parse if the match if it is live or empty
            if not match.find(class_="[Class Name]") and not match.find(
                class_="[Class Name]"
            ):

                # Standardizes the date format
                date_time: datetime = Site5Parser.standardize_datetime(
                    match.find(class_="[Class Name]")
                )

                # Standardizes the team names
                team_names = SiteParser.parse_team_names(
                    Site5Parser.site,
                    category,
                    team_name_soup_=match.find_all(class_="[Class Name]"),
                )

                # Get the odds for the bets
                odds = {}
                try:
                    # Gets the larger grid of odds
                    grids = match.find(class_="[HTML Element]")
                    # Gets the individual grid for match odds
                    grid = grids.find("[HTML Element]")
                    # Gets the columns for the match odds
                    cols = grid.find_all(class_="[HTML Element]")
                except:
                    logging.error(
                        "Error parsing out grids and cols " + Site5Parser.site
                    )
                    continue

                if not (date_time and team_names and len(team_names) == 2 and cols):
                    pass
                else:
                    for idx, col in enumerate(cols):
                        if not col.find(class_="[Class Name]"):
                            Site5Parser._add_odds(
                                category, odds, col, idx, team_names, bets
                            )

                if odds:
                    match_list.append(
                        Match("Site5", category, date_time, team_names, odds)
                    )
                else:
                    logging.error(
                        f"Data for {Site5Parser.site}:\n\tdate_time : {date_time}\n\tteam_names : {team_names}\n\todds : {odds}"
                    )

        return match_list

    @staticmethod
    def _add_odds(category, odds, col, idx, team_names, bets):
        cells = col.find_all("[HTML Element]", class_="[Class Name]")
        for sub_idx, cell in enumerate(cells):
            if cell.find(class_="[Class Name]"):
                # This would be handled by odds_conversion but the flakes are ugly
                continue
            elif odd := SiteParser.odds_conversion(
                odds_soup_=cell.find(class_="[Class Name]")
            ):
                if not bets[idx] in odds:
                    odds[bets[idx]] = {}
                if bets[idx] == "moneyline":
                    odds[bets[idx]][team_names[sub_idx]] = odd
                else:
                    if bet_header := SiteParser.parse_bet_headers(
                        Site5Parser.site,
                        category,
                        bet_header_soup_=cell.find(class_="[Class Name]"),
                    ):
                        if bets[idx] == "spread":
                            odds[bets[idx]][team_names[sub_idx] + bet_header] = odd
                        else:
                            odds[bets[idx]][bet_header] = odd

    @staticmethod
    def standardize_category(category_soup):
        category = SiteParser.parse_category(
            Site5Parser.site, category_soup_=category_soup
        )
        category = category.rsplit("[Chars]")[-1]
        try:
            category = SiteParser.category_dict[category]
        except KeyError:
            logging.warning(f"Category: {category} not found {Site5Parser.site} ")
            return None
        return category

    @staticmethod
    def standardize_datetime(date_soup):
        date = SiteParser.parse_date_time(Site5Parser.site, date_soup_=date_soup)
        if date.find("[chars]") != -1:
            return None
        if re_search := re.search(
            r"[REGEX Trust me it was a very nice regex, I am nice with it :)]", date
        ):
            date = datetime.now() + dt.timedelta(minutes=int(re_search.group(1)))
            date = date.strftime("[Date Format]")
        elif re_search := re.match(r"[REGEX]", date):
            date = datetime.now().strftime("[Date Format]") + " " + re_search.group(0)
        date = SiteParser.replace_td_tmr(date)
        date = SiteParser.remove_garbage_chars(date)
        date = SiteParser.append_year(date)

        return Site5Parser.convert_date_str(date)

    @staticmethod
    def convert_date_str(date):
        # TODO : Low Priority, hacky but works
        try:
            return datetime.strptime(date, "[Date Format]").replace(minute=0)
        except ValueError:
            return datetime.strptime(date, "[Date Format]")
