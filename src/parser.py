import logging
from bs4 import BeautifulSoup as bs
# used to execute JS for webcrawling
from selenium.webdriver import Firefox

class Parser:
    def __init__(self,url=''):
        self.url = url
        self.decklist = []

    def _parse_decklist(self):
        html = ''
        with Firefox('./') as driver:
            driver.get(self.url)
            html = driver.page_source
        soup = bs(html)
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
        # TODO