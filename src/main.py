from crawler import Crawler
from parser import *

if __name__ == '__main__':
    crawler = Crawler('https://cedh-decklist-database.com/')
    crawler.run()
    counts = {}
    for link in crawler.links:
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
        print(len(parser.decklist))
        # TODO
        
    # make sure to close the browser to avoid mem leaks
    driver.quit()