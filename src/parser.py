import logging
# for splitting text with regex
import re
import time
from bs4 import BeautifulSoup as bs
# use selenium to have js enabled while webcrawling
from selenium.webdriver import Firefox, firefox
# used for checking dropdown menus so we have a standard view
from selenium.webdriver.support.select import Select

# options we need to have selenium run firefox in the background
options = firefox.options.Options()
options.headless = True
options.add_argument('start-maximized')
driver = Firefox(executable_path='./geckodriver',options=options)

class Parser:
    _basics = {'Plains','Island','Swamp','Mountain','Forest'}

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

class GoldfishParser(Parser):
    def _parse_decklist(self):
        soup = super()._parse_decklist()
        # TODO

class MoxfieldParser(Parser):
    def _parse_decklist(self):
        soup = super()._parse_decklist()
        # use dropdowns to guarantee we always default to table view
        try:
            select = Select(driver.find_element_by_id('viewMode'))
        # in case moxfield doesn't properly load the page
        # we return None here, relying on main.py to retry this until it works
        except:
            return
        # option 0 = view mode as a table, if visual view is on instead
        if select.all_selected_options[0] != select.options[0]:
            # when opening moxfield links w/ visual view in headless, 
            # 'deck-footer ' will obscure the dropdown that lets you change
            # use javascript to hide the div 'deck-footer '
            e = driver.find_element_by_xpath("//div[@class='deck-footer ']")
            driver.execute_script("arguments[0].style.visibility='hidden'",e)
            try:
                select.select_by_value('table')
            except:
                return
            # refresh the soup for the updated html
            html = driver.page_source
            soup = bs(html,'html.parser')
        for table in soup.find_all(class_='table-deck'):
            # split up card name from type
            text = table.text.strip().split(maxsplit=1)
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
                # ignore basic lands
                if card not in super()._basics and 'Snow-Covered' not in card:
                    self.decklist.add(card)