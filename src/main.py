from crawler import Crawler
from parser import *

if __name__ == '__main__':
    crawler = Crawler('https://cedh-decklist-database.com/')
    crawler.run()
    counts = {}
    for link in ['https://www.moxfield.com/decks/1t0Cpm1xqUeyA-6xi2TrGQ']: #crawler.links[:5]:
        print(link)
        if 'moxfield' in link:
            parser = MoxfieldParser(link)
        elif 'archidekt' in link:
            parser = ArchidektParser(link)
            continue
        elif 'mtggoldfish' in link:
            parser = GoldfishParser(link)
            continue
        # sometimes doesn't read the decklist, so loop until it does
        while not parser.decklist:
            parser.run()
        # TODO
        print(len(parser.decklist))
    # make sure to close the browser to avoid mem leaks
    driver.quit()