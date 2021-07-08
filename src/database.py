import pickle
from os.path import exists

class Database:
    def __init__(self):
        self.db = {}

    # create a database of [card]->[frequency,decklists]
    def add_card(self,card,deck):
        if card in self.db:
            val = self.db[card]
            val[0] += 1
            val[1].append(deck)
            self.db[card] = val
        else:
            self.db[card] = [1,[deck]]

    # sort the cards by their frequency, [frequency]->[cards]
    def rank_cards(self):
        ranks = {}
        for card in self.db.keys():
            count = self.db[card][0]
            if count in ranks:
                ranks[count].append(card)
            else:
                ranks[count] = [card]
        return ranks

    # return which decks contain a certain card
    def decks_with_card(self,card):
        if card in self.db:
            return self.db[card][1]
        else:
            return []

    # save the database to a pickled file
    def save(self,path='database.pkl'):
        with open(path,'wb') as file:
            pickle.dump(self.db,file)

    # load the database from a pickled file
    def load(self,path='database.pkl'):
        try:
            with open(path,'rb') as file:
                self.db = pickle.load(file)
            return 0
        except:
            return -1