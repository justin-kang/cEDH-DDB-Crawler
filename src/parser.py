import logging
# for splitting text with regex
import re
from bs4 import BeautifulSoup as bs
# used to execute JS for webcrawling, needed for moxfield
from selenium.webdriver import Firefox, firefox

options = firefox.options.Options()
options.add_argument('--headless')
driver = Firefox(executable_path='./geckodriver',options=options)

class Parser:
    def __init__(self,url=''):
        self.url = url
        self.decklist = set()

    def _parse_decklist(self):
        driver.get(self.url)
        html = driver.page_source
        soup = bs(html,'html.parser')
        return soup

    def run(self):
        try:
            return self._parse_decklist()
        except Exception:
            logging.exception(f'Failed to crawl: {self.url}')

class ArchidektParser(Parser):
    def _parse_decklist(self):
        soup = super()._parse_decklist()
        # TODO

class MoxfieldParser(Parser):
    def _parse_decklist(self):
        soup = super()._parse_decklist()
        types = {'Commander','Creatures','Planeswalkers','Enchantments',
                'Artifacts','Sorceries','Instants','Lands','Sideboard'}
        for table in soup.find_all('table'):
            if table.has_attr('class'):
                if 'table-deck' in table['class']:
                    # split up card name from type
                    text = table.text.strip().split(maxsplit=1)
                    # ignore non-type categories like considering
                    if text[0] not in types:
                        continue
                    # use regex to filter card names
                    cards = text[1].split(')',1)[1]
                    if 'Lands' in text[0]:
                        if 'mdfc' in text[1]:
                            cards = text[1].split('mdfc',1)[1]
                    cards = re.split(r'[\d+]',cards)[1:]
                    # check for companions in sideboard
                    if 'Sideboard' in text[0]:
                        for i,row in enumerate(table.tbody.find_all('tr')):
                            if row.select('#companion-icon'):
                                self.decklist.add(cards[i])
                                break
                        continue
                    for card in cards:
                        if card:
                            self.decklist.add(card)