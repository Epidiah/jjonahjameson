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
    words = columnist.split(" ")
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
    words = text.split(" ")
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


def layout_body(typeset, text, lorem_list, top, byline_bottom, illo):
    prewords = (text + "\n" + filler(lorem_list)).split(" ")
    words = []
    for word in prewords:
        if "\n" in word:
            break_words = word.split("\n")
            for bw in break_words[:-1]:
                words.append(bw + "\n")
                words.append("\n")
            if word.endswith("\n"):
                words.append(break_words[-1] + "\n")
                words.append("\n")
            else:
                words.append(break_words[-1])
        else:
            words.append(word)
    positions = []  # list of tuples (left, top, right, bottom)
    if illo:
        illo_bottom = top + illo.size[1]
        # First body: between byline and illustration
        positions.append((188, top, 482, byline_bottom))
        if illo_bottom >= 450:
            # Illo will run the length of the article, only 1 more body
            # Second body: between left margin and illustration
            positions.append((60, byline_bottom + 1, 482, illo_bottom))
        elif illo_bottom > byline_bottom + 1:
            # Illo ends between byline bottom and bottom of page, 2 more bodies
            # Second body: between left margin and illustration
            positions.append((60, byline_bottom + 1, 482, illo_bottom))
            # Third body: between left margin and right margin
            positions.append((60, illo_bottom + 1, 740, 460))
        elif illo_bottom <= byline_bottom:
            # Illo ends before byline bottom, 2 more bodies
            # Second body: between byline and right margin
            positions.append((188, illo_bottom + 1, 740, byline_bottom))
            # Third body: between left margin and right margin
            positions.append((60, byline_bottom + 1, 740, 460))
    else:
        # No illo, 2 bodies
        # First body: between byline and right margin
        positions.append((188, top, 740, byline_bottom))
        # Second body: between left and right margin
        positions.append((60, byline_bottom + 1, 740, 460))
    bodies = []
    bookmark = 0
    for position in positions:
        text = ""
        while bookmark < len(words):
            dim = typeset.multiline_textbbox(
                (position[0], position[1]),
                text + words[bookmark],
                spacing=1.5,
                align="left",
                font=BODY_FONT,
            )
            if dim[3] > position[3]:
                bodies.append({"text": text, "left": position[0], "top": position[1]})
                break
            # top = dim[3]
            if words[bookmark] != "\n" and dim[2] < position[2]:
                text += words[bookmark] + " "
                bookmark += 1
            else:
                text = text[:-1] + "\n"
                if words[bookmark] == "\n":
                    bookmark += 1
            if text[-3:] == "\n\n\n":
                text = text[:-1]
    return bodies


def layout_options(text, header):
    layouts = []
    # Parse out a quote or the first sentence
    quote = re.match(r'".*"', header)
    first_sentence = re.match(r"^.{5,}?[!?.…]", header)
    # If there's a discernable sentence at the beginning of the message
    # make that sentence the headline
    if first_sentence:
        # If there is a quotation contained in the first sentence, preserve it.
        if quote and quote.start() < first_sentence.end():
            headline = header[: quote.end()]
        else:
            # Remove period at end of headline if it is not ellipses
            if (
                len(header) > first_sentence.end()
                and header[first_sentence.end() + 1] != "."
            ):
                headline = first_sentence[0].strip(" .")
            # Otherwise, construct ellipses
            else:
                headline = first_sentence[0] + ".."
    # If there's no discernable sentence, take the first line
    else:
        headline = header.split("\n")[0]
    body = text
    layouts.append({"headline": headline, "body": body})
    # Add new layout algorithms here.
    return layouts


async def get_illo(illo_url):
    if illo_url == None:
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
            return io.BytesIO(image.read())
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(photo_url) as response:
                if response.status != 200:
                    with open("test.webp", "rb") as image:
                        return io.BytesIO(image.read())
                else:
                    async with session.get(photo_url) as image:
                        return io.BytesIO(await image.read())
    except:
        with open("test.webp", "rb") as image:
            return io.BytesIO(image.read())


def pulp_photo(photo_stream, width, height):
    with Image.open(photo_stream) as photo:
        photo_converted = photo.convert("RGB")
    photo_resized = ImageOps.contain(photo_converted, (width, height))
    photo_autocontrasted = ImageOps.autocontrast(photo_resized, (0, 30))
    return photo_autocontrasted.convert("RGBA")


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
    bottom = dim[3] - line_width // 2
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
    r = requests.get("http://wttr.in/NewYork?format=%C\n+%t")
    if r.status_code == 200 and "unknown" not in r.text.lower():
        left_text = "\n".join((t.strip(" +") for t in r.text.split("\n")))
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


def typeset_body(typeset, bodies):
    for body in bodies:
        typeset.multiline_text(
            (body["left"], body["top"]),
            body["text"],
            fill="dimgray",
            spacing=1.5,
            align="left",
            font=BODY_FONT,
        )
    return None


async def stop_the_presses(
    columnist, headline, column, photo_url, illo_url, lorem_list
):
    # Preprocess text for paper
    byline = parse_attribution(columnist)
    page_layout = layout_options(column, headline)[0]
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
    pp = pulp_photo(profile_stream, 120, 120)

    mask_draw = ImageDraw.Draw(profile_mask)
    mask_draw.ellipse(
        ((0, 0), (120, 120)), fill="white", outline=(255, 255, 255, 64), width=6
    )
    paper.paste(pp, (60, top), profile_mask)

    # Add byline to the paper
    dim = typeset_byline(typeset, byline, top + 124)
    left = max(194, dim[-2] + 20)
    byline_bottom = dim[-1] - 1

    # Grap Photo
    illo_stream = await get_illo(illo_url)
    if illo_stream:
        illo = pulp_photo(illo_stream, 250, 250)
        paper.paste(illo, (490, top))
        typeset.rectangle(
            (490, top, 490 + illo.width, top + illo.height),
            fill=None,
            outline="dimgray",
            width=4,
        )
    else:
        illo = None

    # Add text to paper
    bodies = layout_body(
        typeset, page_layout["body"], lorem_list, top, byline_bottom, illo
    )
    typeset_body(typeset, bodies)

    # Pulp it all and return the paper image
    paper = ImageOps.grayscale(paper)
    paper = ImageChops.darker(paper, texture)
    return paper.filter(ImageFilter.BoxBlur(1)).filter(ImageFilter.DETAIL)


# Testing Zone
async def main():
    columnist = "Epidiah Ravachol (he/him)"
    headline = "I'll be a genius in these parts tomorrow! But"
    column = "If this works, I'll be a genius in these parts tomorrow! But if it doesn't,\nI'll just keep plugging away."
    photo_url = "test"
    illo_url = "https://pbs.twimg.com/media/FSFLgIVX0AIJTEf?format=png&name=900x900"
    with open("loremipsum.txt", "r") as fp:
        lorem_list = fp.read().split()
    im = await stop_the_presses(
        columnist, headline, column, photo_url, illo_url, lorem_list
    )
    im.show()


if __name__ == "__main__":
    asyncio.run(main())
