import io
from datetime import datetime, timedelta

import aiohttp
from bs4 import BeautifulSoup


async def get_hirffgirth(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                return None
            else:
                heathsoup = BeautifulSoup(await response.text(), "html5lib")
                img_url = heathsoup.find_all("picture", class_="item-comic-image")[
                    0
                ].contents[0]["src"]
                async with session.get(img_url) as image:
                    return io.BytesIO(await image.read())


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
