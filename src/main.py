from crawler import Crawler
from parser import *

if __name__ == '__main__':
    crawler = Crawler('https://cedh-decklist-database.com/')
    crawler.run()
    for link in crawler.links:
        #parser = None
        if 'moxfield' in link:
            parser = MoxfieldParser(link)
        elif 'archidekt' in link:
            parser = ArchidecktParser(link)
        parser.run()