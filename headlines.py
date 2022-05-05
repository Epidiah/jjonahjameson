import json
import os
from pathlib import Path

import pycorpora
import tracery

CUR_DIR = Path(os.getcwd())


def get_hero_set(guild_id):
    jpath = Path(CUR_DIR, f"shdb_{guild_id}.json")
    if jpath.is_file():
        with open(jpath, "rb") as json_file:
            shjson = json.load(json_file)

        def pluck_heroes(h_dict):
            if "if_yes" in h_dict:
                yield pluck_heroes(h_dict["if_yes"])
                yield pluck_heroes(h_dict["if_no"])
            else:
                yield h_dict["text"]

        return set(list(pluck_heroes(shjson)))
    else:
        return set(("SPIDER-MAN", "Doctor Strange", "Storm"))
