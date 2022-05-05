#!/usr/bin/env python3

import datetime
import io
import json
import logging
import os
from pathlib import Path
from random import choice, choices, randint
import re

from TMNT import HALF_SHELL, bio_e, clean_text, is_turtle_power
from editorial import stop_the_presses
import discord
from dotenv import load_dotenv
import hirffgirth as hg

#############
# CONSTANTS #
#############

CUR_DIR = Path(os.getcwd())
SHDICT = {}

# regexy
SKULL_SQUADRON = re.compile(r"s.{0,1}k.{0,1}u.{0,1}l.{0,18}s.{0,1}[q|kw]")
DATE_MATCH = re.compile(
    r"[\d]{4}[/|-][\d]{1,2}[/|-][\d]{1,2}|[\d]{1,2}[/|-][\d]{1,2}[/|-][\d]{4}"
)

# Personality
with open(Path(CUR_DIR, "emojjjis.txt"), "r") as file:
    mjs = file.read().split("\n")
EMOJJJIS = [chr(int(mj, 16)) for mj in mjs]
TURTLE = chr(int("1f422", 16))
POWER = chr(int("1f50b", 16))
HMG_COMMENTS = [
    "This one's a beaut.",
    "Damn funny, I'd say!",
    "Hahahahhaha, this is why we cut Gallagher those fat checks!",
    """My nephew says this one's "too real," whatever the heck that means.""",
    "We need more helmet content.",
    "This'll teach Davis to sue me.",
    "Have Parker explain this one to you. I don't get it.",
    "I'm the editor-in-chief, damn it, not an errand—oh, here it is.",
    "Heathcliff, you rascal.",
]
HMG_REJECTS = [
    "Yeah, yeah, you want Heathcliff and I want Spider-Man. We can't all get what we want!",
    "Parker hasn't come back with those photos yet. WHERE'S PARKER?!?",
    "You want cat pictures, waste Parker's time, not mine!",
    "Check the archives yourself: https://www.gocomics.com/heathcliff \nI have a newspaper to run here!",
]

# Juicy Secrets
load_dotenv()
TOKEN = os.getenv("JJJ_TOKEN")
NSM = discord.Game("Not Spider-Man")
NG = discord.Game("?!? I've got deadlines!")

# JJonahJameson is born
JJJ = discord.Client(activity=NG)

# Logger Setup
logger = logging.getLogger("discord")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(
    filename=Path(CUR_DIR, "jjjdiscord.log"), encoding="utf-8", mode="w"
)
handler.setFormatter(
    logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
)
logger.addHandler(handler)


async def ask(chnl, q):
    while True:
        await chnl.send(q)
        rsp = await JJJ.wait_for("message", check=lambda x: x.author != JJJ.user)
        if (
            rsp.content.lower().startswith("yes")
            or rsp.content.lower().startswith("yup")
            or rsp.content.lower() == "y"
        ):
            return True
        elif rsp.content.lower().startswith("no") or rsp.content.lower() == "n":
            return False
        else:
            await chnl.send("Come on, YES or NO! This ain't a tough question!\n")


async def new_super(old_super, chnl):
    await chnl.send("Who are you, then?")
    new_name = await JJJ.wait_for("message")
    new_name = new_name.content
    await chnl.send(
        f"How am I supposed to keep track of you all?\nIf I were you and you were me, what yes or no question would you ask to tell me apart from {old_super.text}?"
    )
    new_question = await JJJ.wait_for("message")
    print(new_question.content)
    new_question = new_question.content
    ans = await ask(chnl, "And you would answer...?")
    await chnl.send("That's what I thought! Now, go get me that menace, SPIDER-MAN!")
    if ans:
        return Question(new_question, Answer(new_name), old_super)
    else:
        return Question(new_question, old_super, Answer(new_name))


class Knowledge:
    def to_dict(self):
        return self.__dict__

    @staticmethod
    def from_dict(know_dict):
        if "if_yes" in know_dict:
            return Question(**know_dict)
        else:
            return Answer(**know_dict)


class Question(Knowledge):
    def __init__(self, text, if_yes, if_no):
        self.text, self.if_yes, self.if_no = text, if_yes, if_no
        for k, v in self.__dict__.items():
            if type(v) == dict:
                self.__dict__[k] = self.from_dict(v)

    async def play(self, chnl):
        ans = await ask(chnl, self.text)
        if ans:
            self.if_yes = await self.if_yes.play(chnl)
        else:
            self.if_no = await self.if_no.play(chnl)
        return self

    def __repr__(self):
        return f"Question({self.text}, {self.if_yes}, {self.if_no})"

    def get_answers(self):
        yield from self.if_no.get_answers()
        yield from self.if_yes.get_answers()

    def get_raw_text(self):
        yield self.text
        yield from self.if_no.get_raw_text()
        yield from self.if_yes.get_raw_text()

    def to_dict(self):
        return {
            "text": self.text,
            "if_yes": self.if_yes.to_dict(),
            "if_no": self.if_no.to_dict(),
        }


class Answer(Knowledge):
    def __init__(self, text):
        self.text = text

    async def play(self, chnl):
        ans = await ask(chnl, f"Are you {self.text}?")
        if ans:
            if self.text == "SPIDER-MAN":
                await chnl.send("NO YOU'RE NOT! QUIT WASTING MY TIME, PARKER!")
            else:
                await chnl.send(
                    "That's what I thought! Now, go get me that menace, SPIDER-MAN!"
                )
            return self
        else:
            return await new_super(self, chnl)

    def __repr__(self):
        return f"Answer({self.text})"

    def get_answers(self):
        yield self.text

    def get_raw_text(self):
        yield self.text


def load_shdb(guild_id, verbose=False):
    jpath = Path(CUR_DIR, f"shdb_{guild_id}.json")
    if jpath.is_file():
        if verbose:
            print(f"{datetime.datetime.now()}: Loading shdb_{guild_id}.json...")
        with open(jpath, "r") as json_file:
            shjson = json.load(json_file)
            SHDICT[guild_id] = Knowledge.from_dict(shjson)
        if verbose:
            print(f"{datetime.datetime.now()}: Loaded shdb_{guild_id}.json.")
    else:
        if verbose:
            print(
                f"{datetime.datetime.now()}: Could not find shdb_{guild_id}.json. Starting from scratch."
            )
        SHDICT[guild_id] = Question(
            "Do you wear a cape?",
            Question(
                "Is that the Eye of Agamotto around your neck?",
                Answer("Doctor Strange"),
                Answer("Storm"),
            ),
            Answer("SPIDER-MAN"),
        )


def get_lorem_list(guild_id):
    with open("loremipsum.txt", "r") as loremdoc:
        lorems = loremdoc.read().split()
    load_shdb(guild_id)
    return list(SHDICT[guild_id].get_raw_text()) + lorems

async def collect_posts(message):
    nearby_msgs = await message.channel.history(limit=6, around=message, oldest_first=True).flatten()
    # past = message.created_at - datetime.timedelta(minutes=20)
    # future = message.created_at + datetime.timedelta(minutes=20)
    column_content = ""
    original_msg_found = False
    illo_url = None
    for n_m in nearby_msgs:
        # if past < n_m.created_at < future:
        #     continue
        if n_m.author != message.author:
            if original_msg_found:
                break
            else:
                column_content = ""
                illo_url = None
        else:
            if not original_msg_found and n_m == message:
                original_msg_found = True
            column_content += n_m.clean_content + '\n'
            if not illo_url and n_m.attachments:
                for a in n_m.attachments:
                    if not a.is_spoiler() and 'image' in a.content_type.lower():
                        illo_url = a.url
    return column_content[:-1], illo_url


@JJJ.event
async def on_ready():
    print(f"{datetime.datetime.now()}: {JJJ.user} has connected to:")
    for guild in JJJ.guilds:
        print(f"  --{guild}")


@JJJ.event
async def on_message(message):
    chnl = message.channel

    if message.author == JJJ.user:
        return

    # Skull Squadron SKULL SQUADRON!!!
    if SKULL_SQUADRON.search(message.content.lower()):
        await message.add_reaction(chr(int("2620", 16)))
        skull = choices(
            ["Skull", "SKULL", ":skull:", ":skull_crossbones:"], [49, 49, 1, 1]
        )[0]
        squad = choice(["Squadron", "SQUADRON"])
        wrap = "*" * randint(0, 3)
        chorus = wrap + skull + " " * randint(0, 1) + squad + "!" * randint(1, 6) + wrap
        await chnl.send(chorus)

    # Important Heathcliff Discourse
    if JJJ.user in message.mentions and chnl.name == "important-heathcliff-discourse":
        check_archives = True
        if "today" in message.content:
            check_archives = False
            hmg = await hg.todays_hirffgirth()
            if hmg:
                await chnl.send(
                    choice(HMG_COMMENTS), file=discord.File(hmg, "hrfgrf.gif")
                )
            else:
                await chnl.send(choice(HMG_REJECTS))
        if "yesterday" in message.content:
            check_archives = False
            hmg = await hg.hirffgirth_by_days_ago(1)
            if hmg:
                await chnl.send(
                    choice(HMG_COMMENTS), file=discord.File(hmg, "hrfgrf.gif")
                )
            else:
                await chnl.send(choice(HMG_REJECTS))
        if "random" in message.content:
            check_archives = False
            hmg = await hg.random_hirffgirth()
            if hmg:
                await chnl.send(
                    choice(HMG_COMMENTS), file=discord.File(hmg, "hrfgrf.gif")
                )
            else:
                await chnl.send(choice(HMG_REJECTS))

        for d_m in DATE_MATCH.findall(message.content):
            check_archives = False
            hmg = await hg.hirffgirth_by_date(d_m)
            if hmg:
                await chnl.send(
                    choice(HMG_COMMENTS), file=discord.File(hmg, "hrfgrf.gif")
                )
        if check_archives:
            await chnl.send(choice(HMG_REJECTS))
        return

    # Editorial Page
    if (
        JJJ.user in message.mentions
        and message.reference
        and "print" in message.content.lower()
    ):
        column = await chnl.fetch_message(message.reference.message_id)
        columnist = column.author.name
        photo_url = str(column.author.avatar_url)
        lorem_list = get_lorem_list(message.guild.id)
        words, illo_url = await collect_posts(column)
        headline = await stop_the_presses(
            columnist, words, photo_url, lorem_list
        )
        headline.save(f"DailyBugle{message.guild.id}.jpg", format="JPEG")
        with open(f"DailyBugle{message.guild.id}.jpg", "rb") as fp:
            await message.channel.send("STOP THE PRESSES!", file=discord.File(fp, f"DailyBugle{datetime.datetime.now()}.jpg"))
        return

    msg = message.clean_content
    msg = msg.replace("@" + JJJ.user.display_name, "")

    if JJJ.user in message.mentions and chnl.name != "daily-bugle":
        reply = " "
        for i, r in enumerate(bio_e(clean_text(msg))):
            if i:
                reply += "\nOr "
            rhythm = "".join(r)
            reply += rhythm
            if HALF_SHELL.match(rhythm):
                reply += " " + TURTLE + POWER
        await message.reply(reply)

    elif is_turtle_power(msg):
        await message.add_reaction(TURTLE)
        await message.add_reaction(POWER)

    chnls = [x.name for x in message.guild.channels]
    if "daily-bugle" in chnls and chnl.name not in [
        "daily-bugle",
        "the-robot-testing-zone",
    ]:
        return
    if not JJJ.user in message.mentions:
        return
    print(f'{message.author} said "{message.content}" on {message.guild}.')
    load_shdb(message.guild.id)
    if "who's who" in message.content.lower():
        heroes = sorted(list(SHDICT[message.guild.id].get_answers()))
        boast = "Oh, I know them all! I've got dossiers on "
        for hero in heroes:
            if hero == "SPIDER-MAN":
                continue
            boast += f"{hero}, "
        boast += "and that menace SPIDER-MAN!"
        await chnl.send(boast)
        return
    if "love" in message.content.lower():
        await chnl.send(
            choices(
                [
                    "What's 'love' got to do with it?",
                    "I'd love a photo of that menace SPIDER-MAN caught in the act for my front page!",
                    "I'd love a scotch!",
                    "I have a deadline to meet and you're babbling on about love?",
                    "Not since...",
                    "Give me 300 words on the topic for the Wednesday edition and we'll see what we can print.",
                ],
                weights=[1, 5, 5, 5, 1, 5],
            )[0]
        )
        rcts = 1
        while randint(0, 9) >= rcts**2:
            emj = choice(EMOJJJIS)
            await message.add_reaction(emj)
            rcts += 1
        return
    await chnl.send("get me spider-man!".upper())
    rcts = 1
    while randint(0, 9) >= rcts**2:
        emj = choice(EMOJJJIS)
        await message.add_reaction(emj)
        rcts += 1
    msg = await JJJ.wait_for("message", check=lambda m: m.author != JJJ.user)
    if "spider" in msg.content.lower():
        await JJJ.change_presence(activity=NSM)
        await chnl.send("I see...")
        SHDICT[message.guild.id] = await SHDICT[message.guild.id].play(chnl)
        with open(Path(CUR_DIR, f"shdb_{message.guild.id}.json"), "w") as fp:
            json.dump(SHDICT[message.guild.id].to_dict(), fp)
        print(f"{datetime.datetime.now()}: Saved new shdb_{message.guild.id}.json")
        await JJJ.change_presence(activity=NG)


if __name__ == "__main__":
    JJJ.run(TOKEN)
