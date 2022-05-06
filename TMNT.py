import re
from string import punctuation, whitespace
from itertools import product

import pronouncing as pr
import emoji

pr.init_cmu()

HALF_SHELL = re.compile(r"^[12].{3}1.$")
TURTLE = chr(int("1f422", 16))
POWER = chr(int("1f50b", 16))


def clean_text(text: str) -> list:
    # Turn emojis into plain text
    text = emoji.demojize(text)
    # Turn underlines and dashes into spaces
    text = text.replace("_", " ").replace("-", " ")
    # Turn symbols into words
    text = text.replace("&", " and ").replace("@", " at ").replace(" #", " hashtag")
    # Strip punctuation surrounding words
    words = [w.strip(punctuation + whitespace) for w in text.split()]
    return words


def bio_e(word_list: list):
    return product(*[set(pr.stresses_for_word(word)) for word in word_list])


def how_turtle_power(text: str) -> str:
    """
    text: the string to examine for turtle power

    returns: a string of possible rhythms for text, indicating turtle power with
        turtle and battery emojis.
    """
    reply = " "
    for i, r in enumerate(bio_e(clean_text(text))):
        if i:
            reply += "\nOr "
        rhythm = "".join(r)
        reply += rhythm
        if HALF_SHELL.match(rhythm):
            reply += " " + TURTLE + POWER
    return reply


def is_turtle_power(text: str) -> bool:
    """
    text: the string to examine for turtle power

    returns: a bool indicating True if it is, in fact, turtle power
    """
    if len(text) > 60:
        return False
    words = clean_text(text)
    if len(words) > 6:
        return False
    rhythms = bio_e(words)
    for r in rhythms:
        rhythm = "".join(r)
        if HALF_SHELL.match(rhythm):
            return True
    return False
