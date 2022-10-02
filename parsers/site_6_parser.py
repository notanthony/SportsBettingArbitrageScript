from bs4 import BeautifulSoup as bs
from datetime import datetime
from objects.match import Match
from parsers.site_parser import SiteParser
import logging


class Site6Parser(SiteParser):
    file = "html/site_6.txt"

    site = "Site6"

    # Splits the categories
    @staticmethod
    def parse_data():
        match_list = []
        with open(Site6Parser.file) as fp:
            soup = bs(fp, "html.parser")
            for page in soup.find_all("[HTML Element]", class_="[Class Name]"):
                match_list = match_list + Site6Parser._parse_data(page)
        return match_list

    # Parses data from category views
    @staticmethod
    def _parse_data(page):
        match_list = []

        # Standardizes the category ex. mlb, MLB, major league baseball -> mlb
        category = Site6Parser.standardize_category(
            page.find_all("[HTML Element]", class_="[Class Name]")
        )

        # It has to break for invalid categories or it will throw a bunch of flakes
        if not category:
            return match_list

        live_sections = page.find_all(class_="[Class Name]")
        all_sections = page.find_all(class_="[Class Name]")
        section = list(set(live_sections) ^ set(all_sections))[0]

        # Standardize the bets ex. moneyline, ml, money line -> moneyline
        bets = SiteParser.parse_bets(
            Site6Parser.site,
            category,
            bet_soup_=section.find_all(class_="[Class Name]"),
        )

        # Gets all the match divs
        matches = section.find_all(class_="[Class Name]")
        if not (bets and category and matches):
            logging.error("No data found for " + Site6Parser.site)
            return []

        for match in matches:
            # Standardizes the date format
            date_time: datetime = Site6Parser.standardize_datetime(
                match.find(class_="[Class Name]")
            )

            # Standardizes the team names
            team_names = SiteParser.parse_team_names(
                Site6Parser.site,
                category,
                team_name_soup_=match.find_all(class_="[Class Name]"),
            )

            # Get the odds for the bets
            odds = {}
            try:
                # Gets the individual grid for match odds
                grid = match.find(class_="[Class Name]")
                # Gets the columns for the match odds
                cols = grid.find_all(class_="[Class Name]")
            except:
                logging.error("Error parsing out grids and cols " + Site6Parser.site)
                continue

            if not (date_time and team_names and len(team_names) == 2 and cols):
                pass
            else:
                for idx, col in enumerate(cols):
                    Site6Parser._add_odds(category, odds, col, idx, team_names, bets)

            if odds:
                match_list.append(Match("Site6", category, date_time, team_names, odds))
            else:
                logging.error(
                    f"Data for {Site6Parser.site}:\n\tdate_time : {date_time}\n\tteam_names : {team_names}\n\todds : {odds}"
                )

        return match_list

    @staticmethod
    def _add_odds(category, odds, col, idx, team_names, bets):
        cells = col.find_all(class_="[Class Name]")
        for sub_idx, cell in enumerate(cells):
            if cell.find(class_="[Class Name]") or cell.find(class_="[Class Name]"):
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
                        Site6Parser.site,
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
            Site6Parser.site, category_soup_=category_soup
        )

        if type(category) is not list:
            category = [category]

        for category_key in category:
            category_key = category_key.rsplit("[Chars]")[-1]
            if category_key in SiteParser.category_dict:
                return SiteParser.category_dict[category_key]

        logging.warning(f"Category: {category_key} not found {Site6Parser.site} ")
        return None

    @staticmethod
    def standardize_datetime(date_soup):
        date = SiteParser.parse_date_time(Site6Parser.site, date_soup_=date_soup)
        date = date.replace("[Unwanted Chars]", "").strip()
        date = SiteParser.append_year(date)
        if date.find("[Chars]") != -1:
            date = datetime.strptime(date, "[Date Format]").strftime("[Date Format]")
        elif date[0].isdigit():
            date = "today " + date
            date = SiteParser.replace_td_tmr(date)
        else:
            date = SiteParser.get_date_from_day(date)

        return Site6Parser.convert_date_str(date)

    @staticmethod
    def convert_date_str(date):
        return datetime.strptime(date, "[Date Format]").replace(minute=0)
