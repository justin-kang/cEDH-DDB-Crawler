import datetime
import logging
import requests
import json
import urllib.error
import urllib.request
import re
from collections import defaultdict
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode


def print_options(options):
    # Print out your options
    for i in range(len(options)):
        print(str(i + 1) + ":", options[i])
    # Take user input and get the corresponding item from the list
    while True:
        inp = int(input("Enter a number: "))
        if inp - 1 in range(len(options)):
            inp = options[inp - 1]
            break
    return inp

class Crawler:
    def __init__(
            self,
            url='https://raw.githubusercontent.com/AverageDragon/cEDH-Decklist-Database/master/_data/database.json',
            mode='CRAWL',
            category='COMPETITIVE'
    ):
        self.url = url
        self.mode = mode
        self.category = category
        self.links = []
        # Ripped wholesale from Emrakul, thanks past self
        self.valid_urls = {
            "deckstats.net": {
                "query": [("export_dec", "1")]
            },
            "tappedout.net": {
                "query": [("fmt", "txt")]
            },
            "www.mtggoldfish.com": {
                'paths': [{"value": "download", "index": 2}]
            },
            "www.hareruyamtg.com": {
                'paths': [{"value": "download", "index": 3}],
                'replace': [{"old": "/show/", "new": ""}],
            },
            "archidekt.com": {
                'paths':
                    [
                        {"value": "api", "index": 1},
                        {"value": "small/", "index": 4},
                    ],
            },
            "www.archidekt.com": {
                'paths':
                    [
                        {"value": "api", "index": 1},
                        {"value": "small/", "index": 4},
                    ],
            },
            "scryfall.com": {
                'subdomains': ["api"],
                'paths':
                    [
                        {"value": "export", "index": 4},
                        {"value": "text", "index": 5},
                    ],
                'replace': [{"old": r"\.com/@\w+/", "new": ".com/"}],
            },
            "www.moxfield.com": {
                'subdomains': ["api"],
                'paths':
                    [
                        {"value": "v1", "index": 1},
                        {"value": "all", "index": 3},
                        {"value": "download", "index": 5},
                    ],
                'replace': [{"old": "www.", "new": ""}],
                'query': [("exportId", "{{exportId}}")],
                'pre_request_paths':
                    [
                        {
                            "target": "exportId",
                            "path": "/v2/decks/all/",
                            "replace_map": [
                                {"origin_index": 4, "replace_index": 4},
                            ]
                        },
                    ]
            },
        }

        self.re_stripangle = re.compile(r"^<(.*)>$")
        # Gets count and card name from decklist line
        self.re_line = re.compile(
            r"^\s*(?:(?P<sb>SB:)\s)?\s*"
            r"(?P<count>[0-9]+)x?\s+(?P<name>.*?)\s*"
            r"(?:<[^>]*>\s*)*(?:#.*)?$")

        # Dict of card names that should be replaced due to inconsistency
        # AKA Wizards needs to errata Lim-Dûl's Vault already :(
        self.name_replacements = {
            "Lim-Dul's Vault": "Lim-Dûl's Vault"
        }

        self.card_totals = {}

    # Parses a string to get a valid url
    # Returns None if not a good url
    # MessageError unknown url if url found and not in valid urls
    def get_valid_url(self, s):
        # strip surrounding < >. This allows for non-embedding links
        strip = self.re_stripangle.match(s)
        if strip:
            s = strip[1]

        url = urlsplit(s, scheme="https")
        if (url.netloc and url.path and
                (url.scheme == "http" or url.scheme == "https")):
            valid_opts = self.valid_urls.get(url.netloc, None)
            if not valid_opts:
                logging.exception("Unknown url <{}>".format(s))
            url = list(url)

            query_n = valid_opts.get("query", None)
            if query_n:
                query_l = parse_qsl(url[3])
                query_l.extend(query_n)
                url[3] = urlencode(query_l)

            # Add subdomains to the domain, in order
            for subdomain in valid_opts.get("subdomains", []):
                url[1] = ".".join([subdomain, url[1]])

            # Add each path to the position specified by the index value
            for path in valid_opts.get("paths", []):
                current_path = url[2].split("/")
                current_path.insert(path["index"], path["value"])
                url[2] = "/".join(current_path)

            url_str = urlunsplit(url)
            # Perform replacements after getting final URL
            for replace in valid_opts.get("replace", []):
                url_str = re.sub(replace["old"], replace["new"], url_str)

            # Make any required api calls required to build URL
            # This is my shitty attempt to do so in a way that's reasonably dynamic
            # Blame Moxfield (<3 you Harry)
            # -Sick
            for pre_request_path in valid_opts.get("pre_request_paths", []):
                path = pre_request_path["path"]
                baseurl = list(urlsplit(url_str, scheme="https"))
                for replacement in pre_request_path["replace_map"]:
                    existing_path = baseurl[2].split("/")
                    new_path = path.split("/")
                    new_path.insert(replacement["replace_index"], existing_path[replacement["origin_index"]])
                    path = "/".join(new_path)

                baseurl = baseurl[0:2]
                baseurl.extend([path, '', ''])
                baseurl = urlunsplit(baseurl)

                target_result = self.get_special_query_arguments(baseurl, pre_request_path["target"])
                replace_target = '%7B%7B' + pre_request_path["target"] + '%7D%7D'
                url_str = url_str.replace(replace_target, target_result)

            return url_str
        else:
            return None

    # Handle pre-decklist url calls
    # Only used for Moxfield atm
    def get_special_query_arguments(self, url, target_key):
        url = url.rstrip(' /')
        try:
            # Should definitely split this into a few more lines
            files = (urllib.request.urlopen(
                urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            ).read().decode("utf-8", "replace"))

            data = json.loads(files)

            return data[target_key]

        except urllib.error.URLError:
            raise Exception("Failed to open url: " + url)

    # Normalizes names.
    def filter_name(self, name):
        return self.name_replacements.get(name, name)

    # Format json deck info into txt list (for archidekt only)
    def format_to_txt(self, deck):
        try:
            json_deck = json.loads(deck)  # Raise ValueError if not JSON
            mainboard = []
            sideboard = ["//Sideboard"]  # Separator line
            for card in json_deck["cards"]:
                if not card["category"]:  # No category means mainboard
                    mainboard.append(
                        "{0} {1}".format(
                            card["quantity"],
                            card["card"]["oracleCard"]["name"]
                        ))
                elif card["category"] == "Sideboard":
                    sideboard.append(
                        "{0} {1}".format(
                            card["quantity"],
                            card["card"]["oracleCard"]["name"]
                        ))
            return "\n".join(mainboard + sideboard)
        except ValueError:
            return deck  # If data is not JSON, assume it has proper format

    # Parses decklist string into a tuple of dicts for main and sideboards
    def get_list(self, deck):
        mainboard = defaultdict(int)
        sideboard = defaultdict(int)

        lst = mainboard
        for line in self.format_to_txt(deck).split("\n"):
            match = self.re_line.match(line)
            if match:
                lst[self.filter_name(match["name"])] += int(match["count"])
            elif "Sideboard" in line:
                lst = sideboard
        return mainboard, sideboard

    def browse_deck_categories(self):
        json_data = requests.get(self.url).text
        data = json.loads(json_data)

        for entry in data:
            # filter out the non-competitive lists
            entry_category = entry['section']
            if entry_category != self.category:
                continue

            for deck_list in entry['decklists']:
                deck_link = deck_list['link']
                if deck_link:
                    self.links.append(deck_link)

    def get_card_totals(self):
        urls = [m for m in (self.get_valid_url(w)
                            for w in self.links) if m]

        for u in urls:
            try:
                print(u)
                file = urllib.request.urlopen(
                    urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'})).read().decode("utf-8", "replace")
                decklist = self.get_list(file)
                for card in decklist[0]:
                    self.card_totals[card] = self.card_totals.get(card, 0) + 1
                print('done')
            except urllib.error.URLError:
                raise Exception("Failed to open url: " + u)

    def run(self):
        self.browse_deck_categories()
        if self.mode == 'CRAWL':
            for link in crawler.links:
                print(link)
        if self.mode == 'COMPILE':
            self.get_card_totals()
            with open(self.category + '_DUMP_' + datetime.date.today().strftime("%Y%m%d") + '.json', 'w') as dump_file:
                sorted_totals = {}
                sorted_totals = sorted(self.card_totals.items(), key=lambda x: x[1], reverse=True)
                json_dump = json.dumps(sorted_totals)
                print(json_dump)
                dump_file.write(json_dump)


if __name__ == '__main__':
    category = print_options(['COMPETITIVE', 'BREW', 'MEME'])
    mode = print_options(['CRAWL', 'COMPILE'])

    crawler = Crawler(
        mode=mode,
        category=category
    )
    crawler.run()
