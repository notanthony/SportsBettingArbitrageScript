from calendar import weekday
import re
import datetime as dt
from datetime import datetime
import logging
from abc import ABC, abstractmethod
import time
from bs4 import ResultSet

"""
The standard form for spread is +X.X and -X.X
The standard form for total is UX.X and OX.X
"""


def catch_parsing_error(func):
    def wrapper(*args, **kwargs):
        site, category = "no site", "no category"
        try:
            site = args[0]
            category = args[1]
        except IndexError:
            pass
        if not kwargs:
            logging.error(f"No inputs from {site} in {category}: {len(kwargs)}")
            return None
        try:
            return func(*args, **kwargs)
        except Exception as err:
            logging.error(f"Error parsing data from {site} in {category} : {err}")
            return None

    return wrapper


# Wrapper for cleaning soup inputs
def parse_soup_input(func):
    @catch_parsing_error
    def wrapper(*args, **kwargs):
        length = None
        try:
            for key, value in kwargs.items():
                if not (type(value) is list or type(value) is ResultSet):
                    value, length = [value], 1
                if not length:
                    length = len(value)
                # Check all inputs are the same length
                elif length != len(value):
                    raise ValueError(f"Input lists are not the same length for {key}")
                if key.find("_soup") != -1:
                    kwargs[key] = [
                        SiteParser.clean_str(element.text) for element in value
                    ]
                else:
                    kwargs[key] = value
        except Exception as err:
            raise RuntimeError(f"Error converting data into a str: {err}")
        return func(length == 1, *args, **kwargs)

    return wrapper


def clean_and_unpack_soup(func):
    @parse_soup_input
    def wrapper(singular, *args, **kwargs):
        func_args = []

        # Unpack the seperate kwargs lists and repack them together for function calls
        # I cant be sure the dictionary will be in the same order each time so its better to unpack as kwargs even if its a bit clunky
        for key, input in kwargs.items():
            if not func_args:
                # Intialize the each set of kwargs with an empty dict
                for _ in range(len(input)):
                    func_args.append({})
            for idx, element in enumerate(input):
                func_args[idx][key] = element
        results = []

        # Run the function with each set of kwargs
        for kwarg in func_args:
            result = func(*args, **kwarg)
            if result:
                results.append(result)

        return results[0] if singular else results

    return wrapper


class SiteParser(ABC):
    # TODO Low Priority
    # @staticmethod
    # @abstractmethod
    # def site():
    #     pass

    @staticmethod
    @abstractmethod
    def file(self):
        pass

    @staticmethod
    @abstractmethod
    def convert_date_str(cls, date):
        pass

    @clean_and_unpack_soup
    @staticmethod
    def parse_date_time(site, date=None, date_soup_=None):
        if date or date_soup_:
            return date if date else date_soup_
        else:
            logging.error(f"Error parsing date from {site}")
            return None

    category_dict = {
        "mlb": "mlb",
        "college football": "ncaaf",
        "ncaa": "ncaaf",
        "nfl": "nfl",
    }

    @clean_and_unpack_soup
    @staticmethod
    def parse_category(site, category=None, category_soup_=None):
        if category or category_soup_:
            return category if category else category_soup_
        else:
            logging.error(f"Error parsing category from {site}")
            return None

    #####################
    ### GENERIC UTILS ###
    #####################

    @staticmethod
    def clean_str(str):
        return str.lower().replace("\xa0", " ").strip()

    @staticmethod
    def ip_to_american(ip):
        if ip < 0.5:
            return f"+{int(round(-((ip-1))/ip*100, 0))}"
        else:
            return f"-{int(round(-((ip))/(ip-1)*100, 0))}"

    # Will convert american/decimal odds to implied probability
    @clean_and_unpack_soup
    @staticmethod
    def odds_conversion(odds=None, odds_soup_=None):
        odds = odds if odds else odds_soup_
        ip = -1
        if re.fullmatch(r"[\-−\+]\d{3,}", odds):
            # Parse out the number
            num = int(re.search(r"\d+", odds)[0])
            # American odds formula
            ip = (num if "-" in odds or "−" in odds else 100) / (num + 100)
            logging.info(
                f"American odds inputed: {odds} with implied probability = {ip}"
            )
        elif re.fullmatch(r"[1-9]\.\d+", odds):
            # Decimal odds formula
            ip = 1 / float(odds)
            logging.info(
                f"Decimal odds inputed: {odds} with implied probability = {ip}"
            )
        else:
            logging.error(f"Invalid odds input: {odds}")
            return None
        return ip

    #################################
    ### METHODS FOR CLEANING BETS ###
    #################################
    bet_dict = {
        "mlb": {
            "run line (action)": "spread",
            "run line": "spread",
            "total runs over/under (action)": "total",
            "money line (action)": "moneyline",
            "moneyline": "moneyline",
            "money": "moneyline",
            "ml": "moneyline",
            "spread": "spread",
            "total": "total",
            "total runs": "total",
            "run spread": "spread",
            "money line": "moneyline",
        },
        "ncaaf": {
            "total points": "total",
            "moneyline": "moneyline",
            "money": "moneyline",
            "spread": "spread",
            "spread (2 way)": "spread",
            "total": "total",
            "money line": "moneyline",
            "total points over/under": "total",
        },
        "nfl": {
            "total points": "total",
            "moneyline": "moneyline",
            "money": "moneyline",
            "spread": "spread",
            "spread (2 way)": "spread",
            "total": "total",
            "money line": "moneyline",
            "total points over/under": "total",
        },
    }

    @clean_and_unpack_soup
    @staticmethod
    def parse_bets(site, category, bet=None, bet_soup_=None):
        bet = bet if bet else bet_soup_
        if result := SiteParser._parse_bets(category, bet):
            return result
        elif result == "":
            logging.warning(f"Empty bet from {site} in {category}")
        else:
            logging.error(f"Error parsing bets from {site} in {category}")

    @staticmethod
    def _parse_bets(category, bet):
        if category in SiteParser.bet_dict:
            if bet in SiteParser.bet_dict[category]:
                return SiteParser.bet_dict[category][bet]
            elif bet == "":
                return ""
            else:
                logging.error(f"{category} does not support '{bet}' parsing")
        else:
            logging.error("Category not supported")
        return bet

    ########################################
    ### METHODS FOR CLEANING BET HEADERS ###
    ########################################
    bet_header = {
        "point_based": {
            "ov": "o",
            "un": "u",
            "o": "o",
            "u": "u",
            "O": "o",
            "U": "u",
            "over": "o",
            "under": "u",
        }
    }

    @clean_and_unpack_soup
    @staticmethod
    def parse_bet_headers(site, category, bet_header=None, bet_header_soup_=None):
        bet_header = bet_header if bet_header else bet_header_soup_
        if result := SiteParser._parse_bet_headers(category, bet_header):
            return result
        else:
            logging.error(f"Error parsing bet header from {site} in {category}")

    @staticmethod
    def _parse_bet_headers(category, bet_header):
        if category == "mlb" or category == "nfl" or category == "ncaaf":
            return SiteParser._pt_parse_bet_headers(bet_header)
        else:
            logging.error(f"{category} not supported for bet header parsing")
            return None

    @staticmethod
    def _pt_parse_bet_headers(bet_header: str):
        if found := re.search(r"([a-z]+)\s*(\d+\.?\d*)", bet_header):
            if found.group(1) in SiteParser.bet_header["point_based"]:
                bet_header = (
                    SiteParser.bet_header["point_based"][found.group(1)]
                    + " "
                    + found.group(2)
                )
            else:
                logging.error(
                    f"Point based games does not support parsing '{bet_header}'"
                )
                return None
        return re.sub(r".0$", "", bet_header)

    #######################################
    ### METHODS FOR CLEANING TEAM NAMES ###
    #######################################

    ncaaf_team_name_dict = {}

    @clean_and_unpack_soup
    @staticmethod
    def parse_team_names(site, category, team_name=None, team_name_soup_=None):
        team_name = team_name if team_name else team_name_soup_
        if result := SiteParser._parse_team_names(category, team_name, site=site):
            return result
        else:
            logging.error(f"Error parsing team names from {site} in {category}")

    @staticmethod
    def _parse_team_names(category, team_name, site=None):
        # TODO : Low Priority, hacky but works
        # I would say which site (site_1, site_2, etc..) but better safe than sorry
        if site and site == "SOME SITE":
            team_name = team_name.replace("[Unwanted Chars]", "")
            team_name = re.sub("[Unwanted Chars]", "", team_name)
        if category == "mlb":
            return SiteParser._mlb_parse_team_names(team_name)
        elif category == "nfl":
            return SiteParser._nfl_parse_team_names(team_name)
        elif category == "ncaaf":
            if not SiteParser.ncaaf_team_name_dict:
                SiteParser._intialize_ncaaf_dict()
            if team_name in SiteParser.ncaaf_team_name_dict:
                return SiteParser.ncaaf_team_name_dict[team_name]
            else:
                vals = SiteParser.ncaaf_team_name_dict.values()
                if team_name in vals:
                    print(f'"{team_name}" : "{team_name}",')
                    return team_name
                for key, value in SiteParser.ncaaf_team_name_dict.items():
                    for tn in [
                        team_name,
                        team_name.split(" ", 1)[0],
                        team_name.rsplit(" ", 1)[0],
                    ]:
                        if value.find(team_name) != -1:
                            print(f"Potential Match: {value} contains {tn}")
                            print(f'"{team_name}" : "{value}",')
                        elif key.find(team_name) != -1:
                            print(f"Potential Match: {key} contains {tn}")
                            print(f'"{team_name}" : "{value}",')

                print(f'"{team_name}" : "",')
                print(f'"{team_name}" : "{team_name}",')
                print(team_name)
                logging.error(f"Team name '{team_name}' not found in ncaaf dict")
                return None
        else:
            logging.error(f"{category} not supported for team name parsing")
            return None

    @staticmethod
    def _mlb_parse_team_names(team_name: str):
        team_name = team_name.replace("@ ", "")
        if "sox" in team_name or "jay" in team_name:
            return team_name.split(" ", 1)[1].strip()
        else:
            return team_name.split(" ")[-1].strip()

    @staticmethod
    def _nfl_parse_team_names(team_name: str):
        return team_name.split(" ")[-1].strip()

    ##################################
    ### METHODS FOR CLEANING DATES ###
    ##################################

    DATE_SUFFIXES = ["rd", "st", "nd", "th"]

    @staticmethod
    # Replaces today and tommorow with the correct date
    def replace_td_tmr(date):
        # Standardizes the date format
        date = date.replace("today", datetime.today().strftime("%a %b %d"))
        date = date.replace(
            "tomorrow", (datetime.today() + dt.timedelta(days=1)).strftime("%a %b %d")
        )
        return date

    @staticmethod
    def remove_date_suffixes(date):
        for suffix in SiteParser.DATE_SUFFIXES:
            number = re.search(rf"(\d+){suffix}", date)
            if number:
                date = re.sub(rf"(\d+){suffix}", number.group(1), date)
        return date

    @staticmethod
    def append_year(date):
        return date + datetime.today().strftime(" %Y")

    @staticmethod
    def remove_at_symbol(date):
        date = date.replace("@", "")
        return date

    @staticmethod
    def remove_periods_from_am_pm(date):
        date = date.replace("p.m.", "PM")
        date = date.replace("a.m.", "AM")
        return date

    @staticmethod
    def remove_garbage_chars(date):
        date = date.replace("[Chars]", "")
        return date

    @staticmethod
    # Gets the numerical day from the name of the day of the week
    def get_date_from_day(date):
        todays_day = datetime.today().weekday()
        split_input = date.split(" ", 1)
        other_day = time.strptime(split_input[0], "%a").tm_wday
        if todays_day > other_day:
            delta = (other_day + 7) - todays_day
        else:
            delta = other_day - todays_day
        return (
            (datetime.today() + dt.timedelta(days=delta)).strftime("%a %b %d")
            + " "
            + split_input[1]
        )

    # Bandaid fix for ncaaf team names, if no teams have overlaps no need to put them into site specific dictionaries :)
    @staticmethod
    def _intialize_ncaaf_dict():
        for dict in [xyz_ncaaf, zy_ncaaf, wx_ncaaf, zz_ncaaf, zy_ncaaf]:
            for key, value in dict.items():
                if key in SiteParser.ncaaf_team_name_dict:
                    if SiteParser.ncaaf_team_name_dict[key] != value:
                        raise RuntimeError(
                            "Collision detected cannot initialize ncaaf dict"
                        )
                SiteParser.ncaaf_team_name_dict[key] = value


# Changed the names of the dicts to anonymize the sites I am scraping from
# I would say which site (site_1, site_2, etc..) but better safe than sorry
xyz_ncaaf = {
    "western carolina": "western carolina catamounts",
    "minnesota": "minnesota golden gophers",
    "portland state": "portland state vikings",
    "eastern kentucky": "eastern kentucky colonels",
    "wagner": "wagner seahawks",
    "norfolk state": "norfolk state spartans",
    "weber state": "weber state wildcats",
    "indiana state": "indiana state sycamores",
    "samford": "samford bulldogs",
    "alabama state": "alabama state hornets",
    "furman": "furman paladins",
    "robert morris": "robert morris colonials",
    "eastern michigan": "eastern michigan eagles",
    "rutgers": "rutgers scarlet knights",
    "gardner-webb": "gardner-webb runnin' bulldogs",
    "holy cross": "holy cross crusaders",
    "alabama a&m": "alabama a&m bulldogs",
    "uiw": "incarnate word cardinals",
    "purdue": "purdue boilermakers",
    "louisiana tech": "louisiana tech bulldogs",
    "tcu": "tcu horned frogs",
    "buffalo": "buffalo bulls",
    "central arkansas": "central arkansas bears",
    "lamar": "lamar cardinals",
    "southern university": "southern university jaugars",
    "idaho state": "idaho state bengals",
    "tarleton state": "tarleton state texans",
    "eastern washington": "eastern washington eagles",
    "northern colorado": "northern colorado bears",
    "western illinois": "western illinois leathernecks",
    "charleston southern": "charleston southern football",
    "temple": "temple owls",
    "southern utah": "southern utah thunderbirds",
    "alabama": "alabama crimson tide",
    "kennesaw state": "kennesaw state owls",
    "idaho": "idaho vandals",
    "lafayette": "lafayette leopards",
    "louisiana-lafayette": "louisiana ragin' cajuns",
    "uconn": "connecticut huskies",
    "pittsburgh": "pittsburgh panthers",
    "indiana": "indiana hoosiers",
    "mcneese": "mcneese state cowboys",
    "alcorn": "alcorn state braves",
    "san jose state": "san jose state spartans",
    "ucf": "ucf knights",
    "fiu": "fiu panthers",
    "sfa": "stephen f. austin lumberjacks",
    "north carolina state": "north carolina state wolfpack",
    "north carolina": "north carolina tar heels",
    "appalachian state": "appalachian state mountaineers",
    "sam houston": "sam houston state bearkats",
    "texas a&m": "texas a&m aggies",
    "uni": "northern iowa panthers",
    "air force": "air force falcons",
    "southeast missouri state": "southeast missouri state",
    "iowa state": "iowa state cyclones",
    "bowling green": "bowling green falcons",
    "ucla": "ucla bruins",
    "oregon": "oregon ducks",
    "georgia": "georgia bulldogs",
    "arizona": "arizona wildcats",
    "san diego state": "san diego state aztecs",
    "houston": "houston cougars",
    "utsa": "utsa roadrunners",
    "tulsa": "tulsa golden hurricane",
    "wyoming": "wyoming cowboys",
    "utep": "utep miners",
    "oklahoma": "oklahoma sooners",
    "north dakota": "north dakota fighting hawks",
    "nebraska": "nebraska cornhuskers",
    "bethune-cookman": "bethune-cookman wildcats",
    "miami fl": "miami hurricanes",
    "cincinnati": "cincinnati bearcats",
    "arkansas": "arkansas razorbacks",
    "troy": "troy trojans",
    "ole miss": "ole miss rebels",
    "byu": "byu cougars",
    "south florida": "south florida bulls",
    "uc davis": "uc davis aggies",
    "california": "california golden beavers",
    "nicholls state": "nicholls state colonels",
    "south alabama": "south alabama jaguars",
    "texas state": "texas state bobcats",
    "nevada": "nevada wolfpack",
    "rice": "rice owls",
    "usc": "usc trojans",
    "florida atlantic": "florida atlantic owls",
    "ohio": "ohio bobcats",
    "middle tennessee": "middle tennessee blue raiders",
    "james madison": "james madison dukes",
    "morgan state": "morgan state bears",
    "georgia southern": "georgia southern eagles",
    "utah": "utah utes",
    "florida": "florida gators",
    "miami oh": "miami (oh) redhawks",  # or miami redhawks
    "kentucky": "kentucky wildcats",
    "army west point": "army black knights",
    "coastal carolina": "coastal carolina chanticleers",
    "liberty": "liberty flames",
    "southern mississippi": "southern miss golden eagles",
    "elon": "elon phoenix",
    "vanderbilt": "vanderbilt commodores",
    "albany ny": "albany great danes",
    "baylor": "baylor bears",
    "mercer": "mercer bears",
    "auburn": "auburn tigers",
    "southeastern louisiana": "southeastern louisiana lions",
    "louisiana-lafayette": "louisiana ragin' cajuns",
    "illinois state": "illinois state redbirds",
    "wisconsin": "wisconsin badgers",
    "south dakota": "south dakota coyotes",
    "kansas state": "kansas state wildcats",
    "massachusetts": "umass minutemen",
    "tulane": "tulane green wave",
    "grambling": "grambling state tigers",
    "arkansas state": "arkansas state red wolves",
    "notre dame": "notre dame fighting irish",
    "ohio state": "ohio state buckeyes",
    "memphis": "memphis tigers",
    "mississippi state": "mississippi state bulldogs",
    "georgia state": "georgia state panthers",
    "south carolina": "south carolina gamecocks",
    "utah state": "utah state aggies",
    "alabama": "alabama crimson tide",
    "smu": "smu mustangs",
    "north texas": "north texas mean green",
    "louisville": "louisville cardinals",
    "syracuse": "syracuse orange",
    "ulm": "ul monroe warhawks",  # or louisiana-monroe warhawsk
    "texas": "texas longhorns",
    "maine": "maine black bears",
    "new mexico": "new mexico lobos",
    "murray state": "murray state racers",
    "texas tech": "texas tech red raiders",
    "colgate": "colgate raiders",
    "stanford": "stanford cardinal",
    "idaho": "idaho vandals",
    "washington state": "washington state cougars",
    "boise state": "boise state broncos",
    "oregon state": "oregon state beavers",
    "kent state": "kent state golden flashes",
    "washington": "washington huskies",
    "western kentucky": "western kentucky hilltoppers",
    "hawaii": "hawaii rainbow warriors",  # or hawai'i warriors
    "florida state": "florida state seminoles",
    "lsu": "lsu tigers",
    "clemson": "clemson tigers",
    "georgia tech": "georgia tech yellow jackets",
}

zy_ncaaf = {
    "miami florida": "miami hurricanes",
    "villanova": "villanova wildcats",
    "bowling green": "bowling green falcons",
    "ucla": "ucla bruins",
    "oregon": "oregon ducks",
    "long island": "long island sharks",
    "georgia": "georgia bulldogs",
    "fordham": "fordham rams",
    "monmouth": "monmouth hawks",
    "tulsa": "tulsa golden hurricane",
    "morehead st": "morehead state eagles",
    "wyoming": "wyoming cowboys",
    "arizona": "arizona wildcats",
    "san diego state": "san diego state aztecs",
    "houston": "houston cougars",
    "utsa": "utsa roadrunners",
    "utep": "utep miners",
    "oklahoma": "oklahoma sooners",
    "cincinnati": "cincinnati bearcats",
    "arkansas": "arkansas razorbacks",
    "troy": "troy trojans",
    "mississippi": "ole miss rebels",
    "byu": "byu cougars",
    "south florida": "south florida bulls",
    "nicholls state": "nicholls state colonels",
    "south alabama": "south alabama jaguars",
    "texas state": "texas state bobcats",
    "nevada": "nevada wolfpack",
    "rice": "rice owls",
    "usc": "usc trojans",
    "middle tennessee state": "middle tennessee blue raiders",
    "james madison": "james madison dukes",
    "florida atlantic": "florida atlantic owls",
    "ohio": "ohio bobcats",
    "morgan state": "morgan state bears",
    "georgia southern": "georgia southern eagles",
    "towson": "towson tigers",
    "bucknell": "bucknell bison",
    "wofford": "wofford terriers",
    "chattanooga": "chattanooga mocs",
    "howard": "howard bison",
    "hampton": "hampton pirates",
    "utah": "utah utes",
    "florida": "florida gators",
    "miami ohio": "miami (oh) redhawks",
    "kentucky": "kentucky wildcats",
    "liberty": "liberty flames",
    "southern miss": "southern miss golden eagles",
    "army": "army black knights",
    "coastal carolina": "coastal carolina chanticleers",
    "massachusetts": "umass minutemen",
    "tulane": "tulane green wave",
    "elon": "elon phoenix",
    "vanderbilt": "vanderbilt commodores",
    "albany": "albany great danes",
    "baylor": "baylor bears",
    "illinois st": "illinois state redbirds",
    "wisconsin": "wisconsin badgers",
    "mercer": "mercer bears",
    "auburn": "auburn tigers",
    "south dakota": "south dakota coyotes",
    "kansas state": "kansas state wildcats",
    "grambling": "grambling state tigers",
    "arkansas state": "arkansas state red wolves",
    "se louisiana": "southeastern louisiana lions",
    "ul lafayette": "lafayette leopards",
    "stephen f.austin": "stephen f. austin lumberjacks",
    "alcorn st": "alcorn state braves",
    "so illinois": "southern illinois salukis",
    "incarnate word": "incarnate word cardinals",
    "texas southern": "texas southern tigers",
    "prairie view": "prairie view a&m panthers",
    "presbyterian": "presbyterian blue hose",
    "austin peay": "austin peay governors",
    "utah state": "utah state aggies",
    "alabama": "alabama crimson tide",
    "smu": "smu mustangs",
    "north texas": "north texas mean green",
    "memphis": "memphis tigers",
    "mississippi state": "mississippi state bulldogs",
    "notre dame": "notre dame fighting irish",
    "ohio state": "ohio state buckeyes",
    "georgia state": "georgia state panthers",
    "south carolina": "south carolina gamecocks",
    "n. carolina a & t": "north carolina a&t aggies",
    "nc central": "north carolina central eagles",
    "ul monroe": "louisiana-monroe warhawks",
    "texas": "texas longhorns",
    "louisville": "louisville cardinals",
    "syracuse": "syracuse orange",
    "maine": "maine black bears",
    "new mexico": "new mexico lobos",
    "murray st": "murray state racers",
    "texas tech": "texas tech red raiders",
    "colgate": "colgate raiders",
    "stanford": "stanford cardinal",
    "mcneese st": "mcneese state cowboys",
    "montana state": "montana state bobcats",
    "idaho": "idaho vandals",
    "washington state": "washington state cougars",
    "boise state": "boise state broncos",
    "oregon state": "oregon state beavers",
    "kent state": "kent state golden flashes",
    "washington": "washington huskies",
    "utah tech": "dixie state trailblazers",  # or utah tech trailblazers
    "sacramento st": "sacramento state hornets",
    "western kentucky": "western kentucky hilltoppers",
    "hawaii": "hawaii rainbow warriors",
    "florida state": "florida state seminoles",
    "lsu": "lsu tigers",
    "clemson": "clemson tigers",
    "georgia tech": "georgia tech yellow jackets",
}

wx_ncaaf = {
    "florida international": "florida international golden panthers",
    "bowling green state falcons": "bowling green state falcons",
    "cincinnati bearcats": "cincinnati bearcats",
    "ucla bruins": "ucla bruins",
    "arkansas razorbacks": "arkansas razorbacks",
    "oregon ducks": "oregon ducks",
    "georgia bulldogs": "georgia bulldogs",
    "houston cougars": "houston cougars",
    "utsa roadrunners": "utsa roadrunners",
    "tulsa golden hurricane": "tulsa golden hurricane",
    "wyoming cowboys": "wyoming cowboys",
    "arizona wildcats": "arizona wildcats",
    "san diego state aztecs": "san diego state aztecs",
    "utep miners": "utep miners",
    "oklahoma sooners": "oklahoma sooners",
    "troy trojans": "troy trojans",
    "ole mississippi rebels": "ole miss rebels",
    "brigham young cougars": "byu cougars",
    "south florida bulls": "south florida bulls",
    "texas state bobcats": "texas state bobcats",
    "nevada wolf pack": "nevada wolfpack",
    "middle tennessee state blue raiders": "middle tennessee blue raiders",
    "james madison dukes": "james madison dukes",
    "florida atlantic owls": "florida atlantic owls",
    "ohio bobcats": "ohio bobcats",
    "rice owls": "rice owls",
    "usc trojans": "usc trojans",
    "army black knights": "army black knights",
    "coastal carolina chanticleers": "coastal carolina chanticleers",
    "utah utes": "utah utes",
    "florida gators": "florida gators",
    "miami redhawks": "miami (oh) redhawks",
    "kentucky wildcats": "kentucky wildcats",
    "liberty flames": "liberty flames",
    "southern mississippi golden eagles": "southern miss golden eagles",
    "massachusetts minutemen": "umass minutemen",
    "tulane green wave": "tulane green wave",
    "utah state aggies": "utah state aggies",
    "alabama crimson tide": "alabama crimson tide",
    "memphis tigers": "memphis tigers",
    "mississippi state bulldogs": "mississippi state bulldogs",
    "southern methodist mustangs": "smu mustangs",
    "north texas mean green": "north texas mean green",
    "notre dame fighting irish": "notre dame fighting irish",
    "ohio state buckeyes": "ohio state buckeyes",
    "georgia state panthers": "georgia state panthers",
    "south carolina gamecocks": "south carolina gamecocks",
    "louisville cardinals": "louisville cardinals",
    "syracuse orange": "syracuse orange",
    "louisiana-monroe warhawks": "louisiana-monroe warhawks",
    "texas longhorns": "texas longhorns",
    "boise state broncos": "boise state broncos",
    "oregon state beavers": "oregon state beavers",
    "kent state golden flashes": "kent state golden flashes",
    "washington huskies": "washington huskies",
    "western kentucky hilltoppers": "western kentucky hilltoppers",
    "hawaii rainbow warriors": "hawaii rainbow warriors",
    "florida state seminoles": "florida state seminoles",
    "lsu tigers": "lsu tigers",
    "clemson tigers": "clemson tigers",
    "georgia tech yellow jackets": "georgia tech yellow jackets",
}

zz_ncaaf = {
    "weber state wildcats": "weber state wildcats",
    "mcneese state cowboys": "mcneese state cowboys",
    "san jose state spartans": "san jose state spartans",
    "western carolina catamounts": "western carolina catamounts",
    "howard bison": "howard bison",
    "lamar cardinals": "lamar cardinals",
    "toledo rockets": "toledo rockets",
    "northern illinois huskies": "northern illinois huskies",
    "stephen f. austin lumberjacks": "stephen f. austin lumberjacks",
    "louisiana tech bulldogs": "louisiana tech bulldogs",
    "connecticut huskies": "connecticut huskies",
    "kennesaw state owls": "kennesaw state owls",
    "maryland terrapins": "maryland terrapins",
    "charlotte 49ers": "charlotte 49ers",
    "navy midshipmen": "navy midshipmen",
    "akron zips": "akron zips",
    "eastern kentucky colonels": "eastern kentucky colonels",
    "indiana state sycamores": "indiana state sycamores",
    "purdue boilermakers": "purdue boilermakers",
    "colorado state rams": "colorado state rams",
    "norfolk state spartans": "norfolk state spartans",
    "northern colorado bears": "northern colorado bears",
    "portland state vikings": "portland state vikings",
    "samford bulldogs": "samford bulldogs",
    "unlv rebels": "unlv rebels",
    "illinois fighting illini": "illinois fighting illini",
    "wagner seahawks": "wagner seahawks",
    "rutgers scarlet knights": "rutgers scarlet knights",
    "alabama state hornets": "alabama state hornets",
    "incarnate word cardinals": "incarnate word cardinals",
    "gardner-webb runnin' bulldogs": "gardner-webb runnin' bulldogs",
    "holy cross crusaders": "holy cross crusaders",
    "buffalo bulls": "buffalo bulls",
    "texas southern tigers": "texas southern tigers",
    "boston college eagles": "boston college eagles",
    "idaho state bengals": "idaho state bengals",
    "tarleton state texans": "tarleton state texans",
    "eastern washington eagles": "eastern washington eagles",
    "new mexico state aggies": "new mexico state aggies",
    "fresno state bulldogs": "fresno state bulldogs",
    "southern university jaguars": "southern university jaguars",
    "old dominion monarchs": "old dominion monarchs",
    "east carolina pirates": "east carolina pirates",
    "robert morris colonials": "robert morris colonials",
    "uab blazers": "uab blazers",
    "alabama a&m bulldogs": "alabama a&m bulldogs",
    "alcorn state braves": "alcorn state braves",
    "central arkansas bears": "central arkansas bears",
    "eastern michigan eagles": "eastern michigan eagles",
    "florida international golden panthers": "",
    "florida international golden panthers": "florida international golden panthers",
    "central michigan chippewas": "central michigan chippewas",
    "southern utah thunderbirds": "southern utah thunderbirds",
    "lafayette leopards": "lafayette leopards",
    "temple owls": "temple owls",
    "western michigan broncos": "western michigan broncos",
    "ball state cardinals": "ball state cardinals",
    "marshall thundering herd": "marshall thundering herd",
    "appalachian state mountaineers": "appalachian state mountaineers",
    "colorado buffaloes": "colorado buffaloes",
    "furman paladins": "furman paladins",
    "air force falcons": "air force falcons",
    "duke blue devils": "duke blue devils",
    "northwestern wildcats": "northwestern wildcats",
    "western illinois leathernecks": "western illinois leathernecks",
    "minnesota golden gophers": "minnesota golden gophers",
    "charleston southern buccaneers": "charleston southern buccaneers",
    "ucf knights": "ucf knights",
    "sam houston state bearkats": "sam houston state bearkats",
    "texas a&m aggies": "texas a&m aggies",
    "bowling green falcons": "bowling green falcons",
    "ucla bruins": "ucla bruins",
    "arizona wildcats": "arizona wildcats",
    "san diego state aztecs": "san diego state aztecs",
    "bethune-cookman wildcats": "bethune-cookman wildcats",
    "miami florida hurricanes": "miami hurricanes",
    "houston cougars": "houston cougars",
    "utsa roadrunners": "utsa roadrunners",
    "oregon ducks": "oregon ducks",
    "georgia bulldogs": "georgia bulldogs",
    "tulsa golden hurricane": "tulsa golden hurricane",
    "wyoming cowboys": "wyoming cowboys",
    "utep miners": "utep miners",
    "oklahoma sooners": "oklahoma sooners",
    "cincinnati bearcats": "cincinnati bearcats",
    "arkansas razorbacks": "arkansas razorbacks",
    "north dakota fighting hawks": "north dakota fighting hawks",
    "nebraska cornhuskers": "nebraska cornhuskers",
    "brigham young cougars": "byu cougars",
    "south florida bulls": "south florida bulls",
    "troy trojans": "troy trojans",
    "ole miss rebels": "ole miss rebels",
    "uc davis aggies": "uc davis aggies",
    "california golden bears": "california golden bears",
    "nicholls state colonels": "nicholls state colonels",
    "south alabama jaguars": "south alabama jaguars",
    "texas state bobcats": "texas state bobcats",
    "nevada wolf pack": "nevada wolfpack",
    "florida atlantic owls": "florida atlantic owls",
    "ohio bobcats": "ohio bobcats",
    "middle tennessee state blue raiders (fbs)": "middle tennessee blue raiders",
    "james madison dukes": "james madison dukes",
    "morgan state bears": "morgan state bears",
    "georgia southern eagles": "georgia southern eagles",
    "rice owls": "rice owls",
    "usc trojans": "usc trojans",
    "albany great danes": "albany great danes",
    "baylor bears": "baylor bears",
    "army black knights": "army black knights",
    "coastal carolina chanticleers": "coastal carolina chanticleers",
    "elon phoenix": "elon phoenix",
    "vanderbilt commodores": "vanderbilt commodores",
    "grambling state tigers": "grambling state tigers",
    "arkansas state red wolves": "arkansas state red wolves",
    "illinois state redbirds": "illinois state redbirds",
    "wisconsin badgers": "wisconsin badgers",
    "liberty flames": "liberty flames",
    "southern mississippi golden eagles": "southern miss golden eagles",
    "massachusetts minutemen": "umass minutemen",
    "tulane green wave": "tulane green wave",
    "mercer bears": "mercer bears",
    "auburn tigers": "auburn tigers",
    "miami ohio redhawks": "miami (oh) redhawks",
    "kentucky wildcats": "kentucky wildcats",
    "south dakota coyotes": "south dakota coyotes",
    "kansas state wildcats": "kansas state wildcats",
    "southeastern louisiana lions": "southeastern louisiana lions",
    "louisiana-lafayette ragin' cajuns": "louisiana ragin' cajuns",
    "utah utes": "utah utes",
    "florida gators": "florida gators",
    "georgia state panthers": "georgia state panthers",
    "south carolina gamecocks": "south carolina gamecocks",
    "memphis tigers": "memphis tigers",
    "mississippi state bulldogs": "mississippi state bulldogs",
    "notre dame fighting irish": "notre dame fighting irish",
    "ohio state buckeyes": "ohio state buckeyes",
    "southern methodist university mustangs": "smu mustangs",
    "north texas mean green": "north texas mean green",
    "utah state aggies": "utah state aggies",
    "alabama crimson tide": "alabama crimson tide",
    "colgate raiders": "colgate raiders",
    "stanford cardinal": "stanford cardinal",
    "louisiana-monroe warhawks": "louisiana-monroe warhawks",
    "texas longhorns": "texas longhorns",
    "louisville cardinals": "louisville cardinals",
    "syracuse orange": "syracuse orange",
    "maine black bears": "maine black bears",
    "new mexico lobos": "new mexico lobos",
    "murray state racers": "murray state racers",
    "texas tech red raiders": "texas tech red raiders",
    "idaho vandals": "idaho vandals",
    "washington state cougars": "washington state cougars",
    "boise state broncos": "boise state broncos",
    "oregon state beavers": "oregon state beavers",
    "kent state golden flashes": "kent state golden flashes",
    "washington huskies": "washington huskies",
    "western kentucky hilltoppers": "western kentucky hilltoppers",
    "hawaii rainbow warriors": "hawaii rainbow warriors",
    "florida state seminoles": "florida state seminoles",
    "lsu tigers": "lsu tigers",
    "georgia tech yellow jackets": "georgia tech yellow jackets",
    "clemson tigers": "clemson tigers",
    "tennessee volunteers": "tennessee volunteers",
    "pittsburgh panthers": "pittsburgh panthers",
    "iowa state cyclones": "iowa state cyclones",
    "iowa hawkeyes": "iowa hawkeyes",
    "kansas jayhawks": "kansas jayhawks",
    "west virginia mountaineers": "west virginia mountaineers",
    "arizona state sun devils": "arizona state sun devils",
    "oklahoma state cowboys": "oklahoma state cowboys",
    "penn state nittany lions": "penn state nittany lions",
    "michigan state spartans": "michigan state spartans",
    "virginia tech hokies": "virginia tech hokies",
    "virginia cavaliers": "virginia cavaliers",
    "wake forest demon deacons": "wake forest demon deacons",
    "indiana hoosiers": "indiana hoosiers",
    "missouri tigers": "missouri tigers",
    "north carolina tar heels": "north carolina tar heels",
    "michigan wolverines": "michigan wolverines",
    "north carolina state wolfpack": "north carolina state wolfpack",
    "tcu horned frogs": "tcu horned frogs",
}

zy_ncaaf = {
    "nc state": "north carolina state wolfpack",
    "north dakota state": "north dakota state bison",
    "bethune cookman": "bethune-cookman wildcats",
    "so carolina state": "south carolina state bulldogs",
    "east tennessee state": "east tennessee state buccaneers",
    "st francispa": "saint francis red flash",
    "youngstown state": "youngstown state penguins",
    "dayton": "dayton flyers",
    "morehead state": "morehead state eagles",
    "montana": "montana grizzlies",
    "san diego": "san diego toreros",
    "cincinnati u": "cincinnati bearcats",
    "richmond": "richmond spiders",
    "the citadel": "the citadel bulldogs",
    "lehigh": "lehigh mountain hawks",
    "no. colorado": "northern colorado bears",
    "gardner webb": "gardner-webb runnin' bulldogs",
    "georgetown": "georgetown hoyas",
    "mcneese state": "mcneese state cowboys",
    "miss. valley st": "mississippi valley state delta devils",
    "cal poly": "cal poly mustangs",
    "vmi": "vmi keydets",
    "louisiana": "louisiana ragin' cajuns",
    "florida state": "florida state seminoles",
    "miamioh": "miami (oh) redhawks",
    "northern iowa": "northern iowa panthers",
    "buffalo u": "buffalo bulls",
    "lsu": "lsu tigers",
    "clemson": "clemson tigers",
    "georgia tech": "georgia tech yellow jackets",
    "louisville": "louisville cardinals",
    "central florida": "ucf knights",
    "boise state": "boise state broncos",
    "new mexico": "new mexico lobos",
    "north carolina a and t": "north carolina a&t aggies",
    "stephen f. austin": "stephen f. austin lumberjacks",
    "alabama": "alabama crimson tide",
    "southern": "georgia southern eagles",
    "texas": "texas longhorns",
    "iowa state": "iowa state cyclones",
    "iowa": "iowa hawkeyes",
    "kentucky": "kentucky wildcats",
    "florida": "florida gators",
    "tennessee": "tennessee volunteers",
    "pittsburgh u": "pittsburgh panthers",
    "arkansas state": "arkansas state red wolves",
    "ohio state": "ohio state buckeyes",
    "north carolina": "north carolina tar heels",
    "georgia state": "georgia state panthers",
    "ohio": "ohio bobcats",
    "penn state": "penn state nittany lions",
    "utsa": "utsa roadrunners",
    "army": "army black knights",
    "southern miss": "southern miss golden eagles",
    "miamifl": "miami hurricanes",
    "east washington": "eastern washington eagles",
    "duke": "duke blue devils",
    "northwestern": "northwestern wildcats",
    "missouri": "missouri tigers",
    "kansas state": "kansas state wildcats",
    "south carolina": "south carolina gamecocks",
    "arkansas": "arkansas razorbacks",
    "wake forest": "wake forest demon deacons",
    "vanderbilt": "vanderbilt commodores",
    "south alabama": "south alabama jaguars",
    "central michigan": "central michigan chippewas",
    "western michigan": "western michigan broncos",
    "ball state": "ball state cardinals",
    "marshall": "marshall thundering herd",
    "notre dame": "notre dame fighting irish",
    "maryland": "maryland terrapins",
    "charlotte": "charlotte 49ers",
    "memphis": "memphis tigers",
    "navy": "navy midshipmen",
    "colorado": "colorado buffaloes",
    "air force": "air force falcons",
    "appalachian state": "appalachian state mountaineers",
    "texas a&m": "texas a&m aggies",
    "washington state": "washington state cougars",
    "wisconsin": "wisconsin badgers",
    "middle tenn state": "middle tennessee blue raiders",
    "colorado state": "colorado state rams",
    "akron": "akron zips",
    "michigan state": "michigan state spartans",
    "virginia": "virginia cavaliers",
    "illinois": "illinois fighting illini",
    "unlv": "unlv rebels",
    "california": "california golden beavers",
    "houston": "houston cougars",
    "texas tech": "texas tech red raiders",
    "old dominion": "old dominion monarchs",
    "east carolina": "east carolina pirates",
    "kansas": "kansas jayhawks",
    "west virginia": "west virginia mountaineers",
    "uab": "uab blazers",
    "liberty": "liberty flames",
    "massachusetts": "umass minutemen",
    "toledo": "toledo rockets",
    "syracuse": "syracuse orange",
    "connecticut": "uconn huskies",
    "kent state": "kent state golden flashes",
    "oklahoma": "oklahoma sooners",
    "northern illinois": "northern illinois huskies",
    "tulsa": "tulsa golden hurricane",
    "florida intl": "fiu panthers",
    "texas state": "texas state bobcats",
    "san jose st": "san jose state spartans",
    "auburn": "auburn tigers",
    "georgia southern": "georgia southern eagles",
    "nebraska": "nebraska cornhuskers",
    "usc": "usc trojans",
    "stanford": "stanford cardinal",
    "arizona state": "arizona state sun devils",
    "oklahoma state": "oklahoma state cowboys",
    "hawaii": "hawaii rainbow warriors",
    "michigan": "michigan wolverines",
    "boston college": "boston college eagles",
    "virginia tech": "virginia tech hokies",
    "new mexico state": "new mexico state aggies",
    "utep": "utep miners",
    "baylor": "baylor bears",
    "byu": "byu cougars",
    "oregon state": "oregon state beavers",
    "fresno state": "fresno state bulldogs",
    "mississippi state": "mississippi state bulldogs",
    "arizona": "arizona wildcats",
}
