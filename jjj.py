# bot.py
import csv
import os
import pickle
import discord
import datetime
import re
from pathlib import Path
from random import randint, choice, choices
from dotenv import load_dotenv
import logging

from TMNT import is_turtle_power, bio_e, clean_text, HALF_SHELL

TURTLE = chr(int('1f422',16))
POWER = chr(int('1f50b', 16))

CUR_DIR = Path('/home/pi/Desktop/jjj')

logger = logging.getLogger("discord")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename=Path(CUR_DIR, "jjjdiscord.log"), encoding="utf-8", mode="w")
handler.setFormatter(
    logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
)
logger.addHandler(handler)

load_dotenv()
TOKEN = os.getenv("JJJ_TOKEN")
NSM = discord.Game("Not Spider-Man")
NG = discord.Game("?!? I've got deadlines!")

client = discord.Client(activity=NG)

with open(Path(CUR_DIR, "jjjemojis.txt"), "r") as file:
    mjs = file.read().split("\n")
emjs = [chr(int(mj, 16)) for mj in mjs]


async def ask(chnl, q):
    while True:
        await chnl.send(q)
        rsp = await client.wait_for("message", check=lambda x: x.author != client.user)
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
    new_name = await client.wait_for("message")
    new_name = new_name.content
    await chnl.send(
        f"How am I supposed to keep track of you all?\nIf I were you and you were me, what yes or no question would you ask to tell me apart from {old_super.text}?"
    )
    new_question = await client.wait_for("message")
    print(new_question.content)
    new_question = new_question.content
    ans = await ask(chnl, "And you would answer...?")
    await chnl.send("That's what I thought! Now, go get me that menace, SPIDER-MAN!")
    if ans:
        return Query(new_question, AlterEgo(new_name), old_super)
    else:
        return Query(new_question, old_super, AlterEgo(new_name))


class Knowledge:
    pass


class Question(Knowledge):
    def __init__(self, text, if_yes, if_no):
        self.text, self.if_yes, self.if_no = text, if_yes, if_no

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


class Query(Question):
    pass


class AlterEgo(Answer):
    pass


shdict = {}


@client.event
async def on_ready():
    print(f"{datetime.datetime.now()}: {client.user} has connected to:")
    for guild in client.guilds:
        print(f"  --{guild}")


@client.event
async def on_message(message):
    chnl = message.channel

    if message.author == client.user:
        return

    if re.search(r"s.{0,1}k.{0,1}u.{0,1}l.{0,18}s.{0,1}q", message.content, flags=re.IGNORECASE):
        await message.add_reaction(chr(int('2620', 16)))
        skull = choices(['Skull', 'SKULL', ':skull:', ':skull_crossbones:'], [49, 49, 1, 1])[0]
        squad = choice(['Squadron', 'SQUADRON'])
        wrap = '*' * randint(0,3)
        chorus = wrap + skull + ' ' * randint(0,1) + squad + '!' * randint(1,6) + wrap
        if datetime.datetime(2021, 2, 1, 1, 0, 0) > datetime.datetime.now() > datetime.datetime(2021, 1, 29, 23, 00, 37):
            with open(Path(CUR_DIR, 'shouts.csv'), 'a+', newline='') as shouts:
                shout_writer = csv.writer(shouts, delimiter=' ', quotechar='|', quoting=csv.QUOTE_MINIMAL)
                shout_writer.writerow([str(datetime.datetime.now()), message.author, message.content, chorus])
        await chnl.send(chorus)
    
    msg = message.clean_content
    msg = msg.replace('@' + client.user.display_name, '')
    if client.user in message.mentions and chnl.name != "daily-bugle":
        reply = " "
        for i, r in enumerate(bio_e(clean_text(msg))):
            if i:
                reply += "\nOr "
            rhythm = ''.join(r)
            reply += rhythm #.replace("1","●").replace("2","◒").replace("0","○")
            if HALF_SHELL.match(rhythm):
                reply += " " + TURTLE + POWER
        await message.reply(reply)

    elif is_turtle_power(msg):
        # await message.reply("Turtle Power!")
        await message.add_reaction(TURTLE)
        await message.add_reaction(POWER)

        
    chnls = [x.name for x in message.guild.channels]
    if "daily-bugle" in chnls and chnl.name not in [
        "daily-bugle",
        "the-robot-testing-zone",
    ]:
        return
    if not client.user in message.mentions:
        return
    print(f'{message.author} said "{message.content}" on {message.guild}.')
    try:
        print(f"{datetime.datetime.now()}: Loading shdb_{message.guild.id}.kb...")
        file = open(Path(CUR_DIR, f"shdb_{message.guild.id}.kb"), "rb")
        shdict[message.guild.id] = pickle.load(file)
        file.close()
        print(f"{datetime.datetime.now()}: Loaded shdb_{message.guild.id}.kb.")
    except FileNotFoundError:
        print(
            f"{datetime.datetime.now()}: Could not load shdb_{message.guild.id}.kb. Starting from scratch."
        )
        shdict[message.guild.id] = Query(
            "Do you wear a cape?",
            Query(
                "Is that the Eye of Agamotto around your neck?",
                AlterEgo("Doctor Strange"),
                AlterEgo("Storm"),
            ),
            AlterEgo("SPIDER-MAN"),
        )
    if "who's who" in message.content.lower():
        heroes = sorted(list(shdict[message.guild.id].get_answers()))
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
        while randint(0, 9) >= rcts ** 2:
            emj = choice(emjs)
            print(emj)  # Not needed anymore?
            await message.add_reaction(emj)
            rcts += 1
        return
    await chnl.send("get me spider-man!".upper())
    rcts = 1
    while randint(0, 9) >= rcts ** 2:
        emj = choice(emjs)
        print(emj)  # Not needed anymore?
        await message.add_reaction(emj)
        rcts += 1
    msg = await client.wait_for("message", check=lambda m: m.author != client.user)
    if "spider" in msg.content.lower():
        await client.change_presence(activity=NSM)
        await chnl.send("I see...")
        shdict[message.guild.id] = await shdict[message.guild.id].play(chnl)
        file = open(Path(CUR_DIR, f"shdb_{message.guild.id}.kb"), "wb")
        pickle.dump(shdict[message.guild.id], file)
        file.close()
        print(f"{datetime.datetime.now()}: Saved new shdb_{message.guild.id}.kb.")
        await client.change_presence(activity=NG)


client.run(TOKEN)
