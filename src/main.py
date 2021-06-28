from crawler import Crawler
from parser import *

if __name__ == '__main__':
    crawler = Crawler('https://cedh-decklist-database.com/')
    crawler.run()
    for link in crawler.links:
        if 'moxfield' in link:
            parser = MoxfieldParser(link)
        elif 'archidekt' in link:
            parser = ArchidektParser(link)
        # sometimes doesn't read the decklist, so loop until it does
        while not parser.decklist:
            parser.run()
        # TODO
    # make sure to close the browser to avoid mem leaks
    driver.quit()