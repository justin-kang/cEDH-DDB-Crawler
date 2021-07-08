import logging
# for splitting text with regex
import re
import time
from bs4 import BeautifulSoup as bs
# use selenium to have js enabled while webcrawling
from selenium import webdriver
# used for checking dropdown menus so we have a standard view
from selenium.webdriver.support.select import Select

# options we need to have selenium run firefox in the background
options = webdriver.firefox.options.Options()
options.headless = True
options.add_argument('start-maximized')
options.set_preference('browser.download.folderList',2)
options.set_preference('browser.download.manager.showWhenStarting',False)
options.set_preference('browser.helperApps.neverAsk.saveToDisk','text/*')
driver = webdriver.Firefox(executable_path='./geckodriver',options=options)

class Parser:
    _basics = {'Plains','Island','Swamp','Mountain','Forest'}

    def __init__(self,url=''):
        self.url = url
        self.decklist = set()

    def _parse_decklist(self):
        driver.get(self.url)
        soup = bs(driver.page_source,'html5lib')
        return soup

    def _add_card(self,card):
        # ignore basic lands
        if card not in self._basics and 'Snow-Covered' not in card:
            self.decklist.add(card)

    def run(self):
        try:
            return self._parse_decklist()
        except Exception:
            logging.exception(f'Failed to crawl: {self.url}')

class ArchidektParser(Parser):
    def _parse_decklist(self):
        driver.get(self.url)
        # we need to wait for archidekt to load metadata to easily get the cmdr
        time.sleep(7.5)
        soup = bs(driver.page_source,'html5lib')
        cmdr = soup.find('meta',{'data-react-helmet':True})['content']
        if 'Commander' not in cmdr:
            return
        # TODO: there's an edgecase of partners but we're ignoring b/c lazy
        cmdr = cmdr[cmdr.index('Commander:'):cmdr.index('.')]
        cmdr = re.sub('Commander:','',cmdr).strip()
        super()._add_card(cmdr)
        # load goldfishing probability as an easy way to scrape text card names
        xpath = "//i[@class='pie chart icon']"
        element = driver.find_element_by_xpath(xpath)
        element.click()
        xpath = "//a[@class='item'][contains(text(),'Probability')]"
        element = driver.find_element_by_xpath(xpath)
        element.click()
        soup = bs(driver.page_source,'html.parser')
        for table in soup.find_all('tbody',class_=''):
            cards = re.split(r'\d+\%',table.text.strip())[:-1]
            for card in cards:
                super()._add_card(card)

class GoldfishParser(Parser):
    def _parse_decklist(self):
        soup = super()._parse_decklist()
        tab = soup.find(id='tab-paper')
        for table in tab.find_all(class_='deck-view-deck-table'):
            # remove non-breaking spaces
            text = table.text.replace(u'\xa0','')
            # ignore the sideboard section
            if 'Sideboard' in text:
                text = text[:text.index('Sideboard')]
            # regex filtering
            # remove prices
            text = re.sub(r'\$\d+\,*\d*\.\d+','',text)
            # remove counts (x) for sections
            text = re.sub(r'\(\d+\)','',text)
            # remove white space
            text = re.sub(r'\n',' ',text)
            # remove section titles
            text = text.replace('  Commander  ','')
            text = text.replace('  Creatures  ','')
            text = text.replace('  Planeswalkers  ','')
            text = text.replace('  Enchantments  ','')
            text = text.replace('  Artifacts  ','')
            text = text.replace('  Spells  ','')
            text = text.replace('  Lands  ','')
            # remove white space
            text = text.strip()
            while '  ' in text:
                text = text.replace('  ',' ')
            # split text into card names
            cards = re.split(r' *\d+ ',text)[1:]
            for card in cards:
                super()._add_card(card)

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
                super()._add_card(card)