import sys
from crawler import Crawler
from parser import *
from database import Database

if __name__ == '__main__':
    database = Database()
    # additional imputs => just load the ddb from a file instead
    load = False
    if len(sys.argv) > 1:
        val = database.load()
        # we successfully loaded the database
        if val == 0:
            load = True
    if not load:
        crawler = Crawler('https://cedh-decklist-database.com/')
        crawler.run()
        for link in crawler.links:
            if 'moxfield' in link:
                parser = MoxfieldParser(link)
            # TODO
            elif 'archidekt' in link:
                parser = ArchidektParser(link)
            elif 'mtggoldfish' in link:
                parser = GoldfishParser(link)
            # sometimes doesn't read the decklist, so loop until it does
            while not parser.decklist:
                parser.run()
            for card in parser.decklist:
                database.add_card(card,link)
        database.save()
    # make sure to close the browser to avoid memory leaks
    driver.quit()
    # TODO: actual stuff with said database