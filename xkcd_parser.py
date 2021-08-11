import requests
import asyncio

from datetime import date
from bs4 import BeautifulSoup

from loader import logger


class Parser:
    def __init__(self):
        self.real_ru_ids = self._get_real_ru_ids()
        self._specific_comic_ids = {826, 880, 980, 1037, 1110, 1190, 1193, 1331, 1335, 1350, 1416,
                                    1506, 1525, 1525, 1608, 1663, 1975, 2067, 2131, 2198, 2288, 2445}

    @property
    def actual_latest_comic_id(self):
        url = f'https://xkcd.com/info.0.json'
        comic_json = requests.get(url).json()
        return int(comic_json.get('num'))

    @staticmethod
    def _get_soup(url):
        response = requests.get(url)
        if response.ok:
            content = response.content
            return BeautifulSoup(content, 'lxml')

    def _get_real_ru_ids(self):
        soup = self._get_soup('https://xkcd.ru/num')
        lis = soup.find('ul', {'class': 'list'}).find_all('li', {'class': 'real'})
        nums = []
        for li in lis:
            nums.append(int(li.text))
        return tuple(nums)

    async def get_comic_data(self, comic_id):
        if comic_id == 404:
            return {'comic_id': comic_id,
                    'title': '404',
                    'img_url': 'https://www.explainxkcd.com/wiki/images/9/92/not_found.png',
                    'comment': 'Page not found!',
                    'public_date': date(day=1, month=4, year=2008),
                    'is_specific': 0
                    }
        else:
            url = f'https://xkcd.com/{comic_id}/info.0.json'
            comic_json = requests.get(url).json()

            comic_data = {
                'comic_id': comic_id,
                'title': comic_json.get('safe_title') if comic_json.get('safe_title') else '...',
                'img_url': comic_json.get('img'),
                'comment': comic_json.get('alt') if comic_json.get('alt') else '...',
                'public_date': date(day=int(comic_json.get('day')),
                                    month=int(comic_json.get('month')),
                                    year=int(comic_json.get('year'))),
                'is_specific': 1 if comic_id in self._specific_comic_ids else 0
            }

            # I don't know why telegram don't want to upload original image!
            if comic_id == 109:
                comic_data['img_url'] = 'https://www.explainxkcd.com/wiki/images/5/50/spoiler_alert.png'
            if comic_id == 658:
                comic_data['img_url'] = 'https://www.explainxkcd.com/wiki/images/1/1c/orbitals.png'
            return comic_data

    async def get_ru_version(self, comic_id):
        keys = ('ru_title', 'ru_img_url', 'ru_comment')

        if comic_id not in self.real_ru_ids:
            return dict(zip(keys, ['']*3))
        else:
            soup = self._get_soup(f'https://xkcd.ru/{comic_id}')
            img = soup.find('img', {'border': 0})
            comment = soup.find('div', {'class': 'comics_text'}).text
            comment = comment if comment else '...'

            values = (img['alt'], img['src'], comment)
            return dict(zip(keys, values))

    async def get_explanation(self, comic_id):
        url = f'https://www.explainxkcd.com/{comic_id}'
        attempts = 10
        for _ in range(attempts):
            try:
                soup = self._get_soup(url)
                first_p = soup.find_all('div', {'class': 'mw-parser-output'})[-1].find('p')
                text = first_p.text
                for el in first_p.find_next_siblings()[:12]:
                    if el.name in ('p', 'li'):
                        text = text + el.text + '\n'
                text = text[:1000].strip().replace('<', '').replace('>', '')
                text = f"{text}...\n<a href='{url}'>[FULL TEXT]</a>"
                return text, url
            except AttributeError:
                pass
            except Exception as err:
                logger.error(f'Error in get_explanation() for {comic_id}: {err}')
                await asyncio.sleep(0.1)

        return "❗ <b>There's no explanation yet. Try it later.</b>", url

    async def get_full_comic_data(self, comic_id):
        full_comic_data = await self.get_comic_data(comic_id)
        ru_data = await self.get_ru_version(comic_id)
        full_comic_data.update(ru_data)
        return full_comic_data


parser = Parser()


if __name__ == "__main__":
    pass
