import io
import re
from datetime import datetime, timedelta

import aiohttp
from bs4 import BeautifulSoup

DATE_MATCH = re.compile(
    r"[\d]{4}[/|-][\d]{1,2}[/|-][\d]{1,2}|[\d]{1,2}[/|-][\d]{1,2}[/|-][\d]{4}"
)


async def get_hirffgirth(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                return None
            else:
                heathsoup = BeautifulSoup(await response.text(), "html5lib")
                try:
                    img_url = heathsoup.find_all("picture", class_="item-comic-image")[
                        0
                    ].contents[0]["src"]
                except:
                    return None
                async with session.get(img_url) as image:
                    return io.BytesIO(await image.read())


async def whichcliff(request: str):
    request = request.lower()
    if "today" in request:
        yield await todays_hirffgirth()
    if "yesterday" in request:
        yield await hirffgirth_by_days_ago(1)
    if "random" in request:
        yield await random_hirffgirth()
    for d_m in DATE_MATCH.findall(request):
        yield await hirffgirth_by_date(d_m)


def urlizer(date):
    return "https://www.gocomics.com/heathcliff/" + date.strftime("%Y/%m/%d")


async def todays_hirffgirth():
    url = urlizer(datetime.today())
    return await get_hirffgirth(url)


async def random_hirffgirth():
    url = "https://www.gocomics.com/random/heathcliff"
    return await get_hirffgirth(url)


async def hirffgirth_by_date(date_str):
    if "/" in date_str:
        date_str = date_str.replace("/", "-")
    date_list = date_str.split("-")
    if len(date_list[-1]) == 4:
        m, d, y = date_list
    else:
        y, m, d = date_list
    date_str = "-".join([y, m.zfill(2), d.zfill(2)])
    url = urlizer(datetime.fromisoformat(date_str))
    return await get_hirffgirth(url)


async def hirffgirth_by_days_ago(days_ago):
    url = urlizer(datetime.today() - timedelta(days=days_ago))
    return await get_hirffgirth(url)
