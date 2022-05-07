#!/usr/bin/env python3

import datetime
import io
import json
import logging
import os
import re
from functools import partial
from pathlib import Path
from random import choice, choices, randint

import discord
from dotenv import load_dotenv

from editorial import stop_the_presses
from hirffgirth import whichcliff
from skull_squadron import SKULL_SQUADRON, skull_squadron_SKULL_SQUADRON
from superherodb import load_shdb
from TMNT import how_turtle_power, is_turtle_power, TURTLE, POWER

#############
# CONSTANTS #
#############

CUR_DIR = Path(os.getcwd())
SHDB = {}

# Personality
with open(Path(CUR_DIR, "emojjjis.txt"), "r") as file:
    mjs = file.read().split("\n")
EMOJJJIS = [chr(int(mj, 16)) for mj in mjs]
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


async def random_reactions(message):
    reactions = 1
    while randint(0, 9) >= reactions**2:
        reactions += 1
    for emoji in choices(EMOJJJIS, k=reactions):
        await message.add_reaction(emoji)


# Juicy Secrets
load_dotenv()
TOKEN = os.getenv("JJJ_TOKEN")
NSM = discord.Game("Get Me Spider-Man!")
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

# Utility Functions
def get_lorem_list(guild_id, current_dir):
    with open("loremipsum.txt", "r") as loremdoc:
        lorems = loremdoc.read().split()
    shdb = load_shdb(guild_id, current_dir)
    return list(shdb.get_raw_text()) + lorems


async def collect_neighbors(message, leeway=20):
    """
    Looks for continuous messages around the target message that are by the same
    author and within `leeway` minutes of each other.

    message: the target message to search around

    returns a tuple:
        a string of all continuous messages in range,
        a string of the url of the first image to be attached to the messages
    """
    nearby_msgs = await message.channel.history(
        limit=6, around=message, oldest_first=True
    ).flatten()
    too_old = message.created_at - datetime.timedelta(minutes=leeway)
    too_new = message.created_at + datetime.timedelta(minutes=leeway)
    target_msg_found = False
    content = ""
    illo_url = None
    # Review the nearby messages
    for n_m in nearby_msgs:
        # Ignore messages more than 20 mintues older than target
        if n_m.created_at < too_old:
            continue
        # Stop when messages are more than 20 minutes younger than target
        if n_m.created_at > too_new:
            break
        if n_m.author != message.author:
            # Stop at first message after target not by target's author
            if target_msg_found:
                break
            # Otherwise, reset content
            else:
                content = ""
                illo_url = None
        else:
            # Signal that the target message is in this run of messages
            if n_m == message:
                target_msg_found = True
            # Message within time zone and by target message's author, so add
            # it to the content
            content += n_m.clean_content + "\n"
            # if illo_url hasn't been found, check attachments for image
            if not illo_url and n_m.attachments:
                for a in n_m.attachments:
                    if not a.is_spoiler() and "image" in a.content_type.lower():
                        illo_url = a.url
    return content[:-1], illo_url


@JJJ.event
async def on_ready():
    print(f"{datetime.datetime.now()}: {JJJ.user} has connected to:")
    for guild in JJJ.guilds:
        print(f"  --{guild}")


@JJJ.event
async def on_message(message):
    chnl = message.channel

    # Ignore messages from JJJ himself.
    if message.author == JJJ.user:
        return

    # Skull Squadron SKULL SQUADRON!
    sksq = skull_squadron_SKULL_SQUADRON(message.content)
    if sksq:
        await message.add_reaction(SKULL_SQUADRON)
        await message.reply(sksq)

    # Important Heathcliff Discourse!
    if JJJ.user in message.mentions and chnl.name == "important-heathcliff-discourse":
        async for heathcliff in whichcliff(message.content):
            if heathcliff:
                await chnl.send(
                    choice(HMG_COMMENTS), file=discord.File(heathcliff, "hrfgrf.gif")
                )
        else:
            await chnl.send(choice(HMG_REJECTS))
        return

    # Stop the Presses!
    if (
        JJJ.user in message.mentions
        and message.reference
        and "print" in message.content.lower()
    ):
        await random_reactions(message)
        headline = await chnl.fetch_message(message.reference.message_id)
        columnist = headline.author.name
        photo_url = str(headline.author.avatar_url)
        lorem_list = get_lorem_list(message.guild.id, CUR_DIR)
        column, illo_url = await collect_neighbors(headline)
        daily_bugle = await stop_the_presses(
            columnist, headline.clean_content, column, photo_url, illo_url, lorem_list
        )
        daily_bugle.save(f"DailyBugle{message.guild.id}.jpg", format="JPEG")
        with open(f"DailyBugle{message.guild.id}.jpg", "rb") as fp:
            await message.channel.send(
                "STOP THE PRESSES!",
                file=discord.File(fp, f"DailyBugle{datetime.datetime.now()}.jpg"),
            )
        return

    msg = message.clean_content
    msg = msg.replace("@" + JJJ.user.display_name, "")

    # Turtle Power!
    # Avoid conflict with Get Me Spider-Man by forbiding how_turtle_power in
    # the daily-bugle channel
    if JJJ.user in message.mentions and chnl.name != "daily-bugle":
        await message.reply(how_turtle_power(msg))
    elif is_turtle_power(msg):
        await message.add_reaction(TURTLE)
        await message.add_reaction(POWER)

    # Get Me Spider-Man!
    # Confine game to the daily-bugle channel
    if chnl.name not in ["daily-bugle", "the-robot-testing-zone"]:
        return
    # You must tag JJJ in the daily-bugle channel to begin
    if not JJJ.user in message.mentions:
        return
    # Load the game state
    SHDB[message.guild.id] = load_shdb(message.guild.id, CUR_DIR)
    # Get a report from JJJ on all the superheros in the database
    if "who's who" in message.content.lower():
        heroes = sorted(list(SHDB[message.guild.id].get_answers()))
        boast = "Oh, I know them all! I've got dossiers on "
        for hero in heroes:
            if hero == "SPIDER-MAN":
                continue
            boast += f"{hero}, "
        boast += "and that menace SPIDER-MAN!"
        await chnl.send(boast)
        return
    # Just a little insight into JJJ's love life
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
    # The game begins
    await random_reactions(message)
    await chnl.send("get me spider-man!".upper())
    input_func = partial(JJJ.wait_for, "message", check=lambda m: m.author != JJJ.user)
    msg = await input_func()
    if "spide" in msg.content.lower():
        await JJJ.change_presence(activity=NSM)
        await chnl.send("I see...")
        SHDB[message.guild.id] = await SHDB[message.guild.id].play(
            chnl.send, input_func
        )
        # When the game is over, save the database
        with open(Path(CUR_DIR, f"shdb_{message.guild.id}.json"), "w") as fp:
            json.dump(SHDB[message.guild.id].to_dict(), fp)
        await JJJ.change_presence(activity=NG)


if __name__ == "__main__":
    print("Running...")
    JJJ.run(TOKEN)
