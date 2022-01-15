import re
from string import punctuation, whitespace
from itertools import product

import pronouncing as pr
import emoji

pr.init_cmu()

HALF_SHELL = re.compile(r"^[12].{3}1.$")

def clean_text(text: str)->list:
    # Turn emojis into plain text
    text = emoji.demojize(text)
    # Turn underlines and dashes into spaces
    text = text.replace('_', ' ').replace('-',' ')
    # Turn symbols into words
    text = text.replace('&', ' and ').replace('@', ' at ').replace(' #', ' hashtag')
    # Strip punctuation surrounding words
    words = [w.strip(punctuation + whitespace) for w in text.split()]
    return words

def bio_e(word_list: list):
    return product(*[set(pr.stresses_for_word(word)) for word in word_list])

def is_turtle_power(text: str)-> bool:
    if len(text) > 60:
        return False
    words = clean_text(text)
    if len(words) > 6:
        return False
#    print(text)
    rhythms = bio_e(words)
    for r in rhythms:
        rhythm = ''.join(r)
#        print(rhythm)
        if HALF_SHELL.match(rhythm):
        # if len(rhythm) == 6 and rhythm.startswith('1') and rhythm[-2] == "1":
            return True
    return False
