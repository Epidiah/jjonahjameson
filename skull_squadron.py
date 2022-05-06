import re

from random import choices, randint

SKULL_SQUADRON = chr(int("2620", 16))
SKULL_CHECKER = re.compile(r"s.{0,1}k.{0,1}u.{0,1}l.{0,18}s.{0,1}[q|kw]")


def skull_squadron_SKULL_SQUADRON(text: str):
    """
    text: the string to check for the presence of a Skull Squadron.

    returns: either an empty string, if no Skull Squardon, or a string containing
        an appropriate response.
    """
    chorus = ""
    if SKULL_CHECKER.search(text.lower()):
        skull = choices(
            ["Skull", "SKULL", ":skull:", ":skull_crossbones:"], [49, 49, 1, 1]
        )[0]
        squad = choices(["Squadron", "SQUADRON", "squadron"], [66, 33, 1])[0]
        font = "*" * randint(0, 3)
        chorus += (
            font + skull + " " * randint(0, 1) + squad + "!" * randint(1, 6) + font
        )
    return chorus
