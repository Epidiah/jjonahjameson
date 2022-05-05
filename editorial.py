import asyncio
import io
import re
import aiohttp
from datetime import date
from random import randint

from PIL import Image, ImageChops, ImageFilter, ImageFont, ImageDraw, ImageOps
from lorem.text import TextLorem
import requests

# HEADLINE_FONT = ImageFont.truetype("DejaVuSansCondensed-Bold", size=36)
DAILY_BUGLE_FONT = ImageFont.truetype(".fonts/Chomsky.otf", size=72)
HEADER_FONT = ImageFont.truetype("DejaVuSansCondensed-Bold", size=14)
HEADLINE_FONT = ImageFont.truetype(".fonts/NewsflashBB.ttf", size=64)
BYLINE_FONT = ImageFont.truetype("DejaVuSerifCondensed-Bold", size=16)
BODY_FONT = ImageFont.truetype("DejaVuSerif", size=14)


def parse_attribution(columnist):
    columnist = columnist.split("#")[0]
    words = columnist.split(' ')
    lines = []
    line = ""
    for word in words:
        if len(line) + len(word) <= 12:
            line += word + " "
        else:
            lines.append(line[:-1])
            line = word + " "
    lines.append(line[:-1])
    return "\n".join(lines) + "\n \n"


def filler(lorem_list):
    lorem = TextLorem(srange=(12, 24), words=lorem_list)
    return lorem.text()


def layout_headline(text):
    words = text.split(' ')
    lines = []
    line = ""
    for word in words:
        if not word.isupper():
            word = word.capitalize()
        if len(line) + len(word) <= 38:
            line += word + " "
        else:
            lines.append(line[:-1] + "\n")
            line = word + " "
    lines.append(line[:-1] + "\n")
    return "".join(lines)

# TODO: Check against multiline_textbbox to see if you are within margins.
def layout_body(text, lorem_list, byline_bottom):
    prewords = text.split(' ')
    words = []
    for word in prewords:
        if '\n' in word:
            break_words = word.split('\n')
            for bw in break_words[:-1]:
                words.append(bw + '\n')
                words.append('\n')
            if word.endswith('\n'):
                words.append(break_words[-1] + '\n')
                words.append('\n')
            else:
                words.append(break_words[-1])
        else:
            words.append(word)
    lines = []
    line = ""
    margin = 72
    long_break = byline_bottom // 32
    long_margin = 90
    for word in words:
        if word == '\n':
            if line:
                lines.append(line[:-1] + '\n')
                line = ""
            lines.append(line)
        elif len(line) + len(word) <= margin:
            line += word + " "
        else:
            lines.append(line[:-1] + "\n")
            if len(lines) >= long_break:
                margin = long_margin
            line = word + " "
    lines.append(line[:-1] + "\n")
    lines.append('\n')
    if len(lines) < 21:
        ipsum = filler(lorem_list).split()
        line = ""
        for word in ipsum:
            if len(line) + len(word) <= margin:
                line += word + " "
            else:
                lines.append(line[:-1] + "\n")
                if len(lines) >= long_break:
                    margin = long_margin
                line = word + " "
        lines.append(line[:-1] + "\n\n")
    return "".join(lines[:13]), "".join(lines[13:25])


def layout_options(text):
    layouts = []
    # Find first sentence
    first = re.match(r".{5,}?[!?.…]", text)
    if first:
        end = first.span()[1]
        headline = first[0].strip(" .")
        body = text[end:].strip()
    else:
        lines = text.split('\n')
        if len(lines) <= 3:
            headline = text
            body = text
        else:
            headline = "\n".join(lines[:3])
            body = "\n".join(lines[3:])
    if '"' in headline:
        headline += '…"'
        body = '"…' + body
    layouts.append({"headline": headline, "body": body})
    # Add new layout algorithms here.
    return layouts


async def get_illo(illo_url):
    if illo_url ==None:
        return None
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(illo_url) as response:
                if response.status != 200:
                    return None
                else:
                    async with session.get(illo_url) as image:
                        return io.BytesIO(await image.read())
    except:
        return None


async def take_photo(photo_url):
    if photo_url == "test":
        with open("test.webp", "rb") as image:
            return  io.BytesIO(image.read())
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(photo_url) as response:
                if response.status != 200:
                    with open("test.webp", "rb") as image:
                        return  io.BytesIO(image.read())
                else:
                    async with session.get(photo_url) as image:
                        return io.BytesIO(await image.read())
    except:
        with open("test.webp", "rb") as image:
            return  io.BytesIO(image.read())


def typeset_byline(typeset, byline, top):
    dim = typeset.multiline_textbbox(
        (120, top),
        byline,
        anchor="ma",
        align="center",
        font=BYLINE_FONT,
    )
    typeset.multiline_text(
        (120, top),
        byline,
        fill="dimgray",
        anchor="ma",
        align="center",
        font=BYLINE_FONT,
    )
    return dim

def typeset_header(typeset):
    dim = typeset.multiline_textbbox(
        (400, 2),
        "The Daily Bugle",
        anchor="ma",
        align="center",
        font=DAILY_BUGLE_FONT,
    )
    line_width = 10
    top = dim[1]
    bottom = dim[3] - line_width//2
    typeset.line((0, top, 800, top), fill="gray", width=line_width)
    typeset.line((0, bottom, 800, bottom), fill="gray", width=line_width)
    typeset.multiline_text(
        (400, 0),
        "The Daily Bugle",
        fill="silver",
        anchor="ma",
        align="center",
        font=DAILY_BUGLE_FONT,
    )
    typeset.multiline_text(
        (400, 4),
        "The Daily Bugle",
        fill="silver",
        anchor="ma",
        align="center",
        font=DAILY_BUGLE_FONT,
    )
    typeset.multiline_text(
        (400, 2),
        "The Daily Bugle",
        fill="dimgray",
        anchor="ma",
        align="center",
        font=DAILY_BUGLE_FONT,
    )
    typeset.multiline_text(
        (780, dim[-1] // 2 + 5),
        date.today().strftime("%A\n%B %d, %Y"),
        fill="dimgray",
        anchor="rm",
        align="right",
        font=HEADER_FONT,
    )
    r = requests.get('http://wttr.in/NewYork?format=%C\n+%t')
    if r.status_code == 200:
        left_text = "\n".join((t.strip(' +') for t in r.text.split('\n')))
    else:
        left_text = "SPIDER-MENACE?\nSee page E-2"
    typeset.multiline_text(
        (20, dim[-1] // 2 + 5),
        left_text,
        fill="dimgray",
        anchor="lm",
        align="left",
        font=HEADER_FONT,
    )
    return dim

def typeset_headline(typeset, headline, top):
    dim = typeset.multiline_textbbox(
        (400, top),
        headline,
        spacing=2,
        anchor="ma",
        align="center",
        font=HEADLINE_FONT,
    )
    typeset.multiline_text(
        (400, top),
        headline,
        fill="red",
        spacing=2,
        anchor="ma",
        align="center",
        font=HEADLINE_FONT,
    )
    return dim


def typeset_body(typeset, body, left, top):
    dim = typeset.multiline_textbbox(
        (left, top),
        body,
        spacing=1.5,
        align="left",
        font=BODY_FONT,
    )
    typeset.multiline_text(
        (left, top),
        body,
        fill="dimgray",
        spacing=1.5,
        align="left",
        font=BODY_FONT,
    )
    return dim


async def stop_the_presses(columnist, column, photo_url, lorem_list):
    # Preprocess text for paper
    byline = parse_attribution(columnist)
    page_layout = layout_options(column)[0]
    headline = layout_headline(page_layout["headline"])

    # Create base paper image and texture
    paper = Image.new("RGBA", (800, 450), color="Gainsboro")
    profile_mask = Image.new("RGBA", (120, 120), color=(0, 0, 0, 0))
    texture = Image.effect_noise((800, 450), randint(6, 24))
    texture = ImageOps.autocontrast(texture, (0, 50)).convert("RGBA")
    paper = ImageChops.darker(paper, texture.filter(ImageFilter.BLUR))
    texture = ImageOps.grayscale(paper.copy())

    typeset = ImageDraw.Draw(paper)

    # Add Daily Bugle Header to the paper
    dim = typeset_header(typeset)
    top = dim[-1] + 12

    # Add headline to the paper
    dim = typeset_headline(typeset, headline, top)
    top = dim[-1] + 22

    # Add columnist photo to paper
    profile_stream = await take_photo(photo_url)
    with Image.open(profile_stream) as profile_pic:
        pp_converted = profile_pic.convert("RGB")
    pp_resized = ImageOps.contain(pp_converted, (120, 120))
    pp_autoconstrasted = ImageOps.autocontrast(pp_resized, (0, 30))
    pp = pp_autoconstrasted.convert("RGBA")

    mask_draw = ImageDraw.Draw(profile_mask)
    mask_draw.ellipse(
        ((0, 0), (120, 120)), fill="white", outline=(255, 255, 255, 64), width=6
    )
    paper.paste(pp, (60, top), profile_mask)

    # Add byline to the paper
    dim = typeset_byline(typeset, byline, top + 124)
    left = max(194, dim[-2] + 20)
    byline_bottom = dim[-1] - 1

    # TODO: Add illo

    # Add text to paper
    body = layout_body(page_layout["body"], lorem_list, byline_bottom)
    dim = typeset_body(typeset, body[0], left, top + 4)
    dim = typeset_body(typeset, body[1], 60, dim[-1] - 1)

    # Pulp it all and return the paper image
    paper = ImageOps.grayscale(paper)
    paper = ImageChops.darker(paper, texture)
    return paper.filter(ImageFilter.BoxBlur(1)).filter(ImageFilter.DETAIL)

# Testing Zone
async def main():
    columnist =  "Epidiah Ravachol (he/him)"
    column = "If this works, I'll be a genius in these parts tomorrow! But if it doesn't,\nI'll just keep plugging away."
    photo_url = "test"
    with open("loremipsum.txt", "r") as fp:
        lorem_list = fp.read().split()
    im = await stop_the_presses(columnist, column, photo_url, lorem_list)
    im.show()

if __name__ == "__main__":
    asyncio.run(main())
