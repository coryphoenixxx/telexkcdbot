import asyncio
import aiohttp
import re

from datetime import date
from aiohttp import ClientConnectorError
from bs4 import BeautifulSoup

from bot.loader import logger


class Parser:
    def __init__(self):
        self._specific_comic_ids = None

    async def create(self):
        self._specific_comic_ids: set = {826, 880, 980, 1037, 1110, 1190, 1193, 1331, 1335, 1350, 1416,
                                         1506, 1525, 1608, 1663, 1975, 2067, 2131, 2198, 2288, 2445}

    @staticmethod
    async def get_xkcd_latest_comic_id() -> int:
        url = f'https://xkcd.com/info.0.json'
        async with aiohttp.ClientSession() as session:
            comic_json = (await session.get(url)).json()
        return int((await comic_json).get('num'))

    @staticmethod
    async def _get_soup(url: str) -> BeautifulSoup:
        attempts = 10

        for _ in range(attempts):
            async with aiohttp.ClientSession() as session:
                try:
                    response = await session.get(url)
                except ClientConnectorError:
                    await asyncio.sleep(2)
                    continue
                else:
                    if response.ok:
                        content = await response.content.read()
                        return BeautifulSoup(content, 'lxml')
                    else:
                        logger.error(f"Couldn't get soup for {url}.")

        logger.error(f"Couldn't get soup for {url} after 10 attempts!")

    async def get_comic_data(self, comic_id: int) -> dict:
        if comic_id == 404:  # 404 comic doesn't exist
            return {'comic_id': comic_id,
                    'title': '404',
                    'img_url': 'https://www.explainxkcd.com/wiki/images/9/92/not_found.png',
                    'comment': 'Page not found!',
                    'public_date': date(day=1, month=4, year=2008),
                    'is_specific': 0
                    }
        else:
            url = f'https://xkcd.com/{comic_id}/info.0.json'
            async with aiohttp.ClientSession() as session:
                comic_json = await (await session.get(url)).json()

            comment = comic_json.get('alt').replace('<', '').replace('>', '').strip()

            comic_data = {
                'comic_id': comic_id,
                'title': comic_json.get('safe_title') if comic_json.get('safe_title') else '...',
                'img_url': comic_json.get('img'),
                'comment': comment if comment else '...',
                'public_date': date(day=int(comic_json.get('day')),
                                    month=int(comic_json.get('month')),
                                    year=int(comic_json.get('year'))),
                'is_specific': 1 if comic_id in self._specific_comic_ids else 0
            }

            # I don't know why telegram doesn't want to upload original image!
            if comic_id == 109:
                comic_data['img_url'] = 'https://www.explainxkcd.com/wiki/images/5/50/spoiler_alert.png'
            if comic_id == 658:
                comic_data['img_url'] = 'https://www.explainxkcd.com/wiki/images/1/1c/orbitals.png'

            return comic_data

    async def get_ru_comic_data(self, comic_id: int) -> dict:
        keys = ('ru_title', 'ru_img_url', 'ru_comment')

        url = f'https://xkcd.su/finished/{comic_id}'
        soup = await self._get_soup(url)
        finished = soup.find('div', {'class': 'finished_check'})

        if not finished:
            return dict(zip(keys, [''] * 3))
        else:
            ru_title = soup.find('div', {'class': 'finished_title'}).text
            ru_title = re.search('«(.*)»', ru_title).group(1)
            ru_img_url = soup.find('div', {'class': 'comics_img'}).find('img')['src']
            ru_comment = soup.find('div', {'class': 'finished_alt'}).text
            ru_comment = ru_comment.replace('<', '').replace('>', '').strip()
            ru_comment = ru_comment if ru_comment else '...'

            values = (ru_title, ru_img_url, ru_comment)

            return dict(zip(keys, values))

    async def get_explanation(self, comic_id: int) -> str:
        url = f'https://www.explainxkcd.com/{comic_id}'
        no_explanation_text = "❗ <b>There's no explanation yet or explainxkcd.com is unavailable. Try it later.</b>"
        attempts = 10

        try:
            for _ in range(attempts):
                soup = await self._get_soup(url)
                try:
                    first_p = soup.find_all('div', {'class': 'mw-parser-output'})[-1].find('p')
                except AttributeError:
                    pass
                else:
                    text = first_p.text + '\n'

                    for el in first_p.find_next_siblings()[:12]:
                        if el.name in ('p', 'li'):
                            text = text + el.text.strip() + '\n\n'

                    text = text[:1000].strip().replace('<', '').replace('>', '')

                    if not text:
                        text = no_explanation_text
                    else:
                        text = f"{text}...\n<a href='{url}'>[FULL TEXT]</a>"

                    return text

        except Exception as err:
            logger.error(f'Error in get_explanation() for {comic_id}: {err}')
            await asyncio.sleep(0.1)

        return no_explanation_text

    async def get_full_comic_data(self, comic_id: int) -> tuple:
        full_comic_data = await self.get_comic_data(comic_id)
        ru_comic_data = await self.get_ru_comic_data(comic_id)
        full_comic_data.update(ru_comic_data)
        return tuple(full_comic_data.values())


if __name__ == "__main__":
    pass
