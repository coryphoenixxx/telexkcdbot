import requests
from datetime import date
from bs4 import BeautifulSoup


class Parser:
    def __init__(self):
        self.latest_comic_id = self.get_latest_comic_id()
        self.real_rus_ids = self._get_real_rus_ids()
        self._specific_comic_ids = {826, 880, 980, 1037, 1110, 1190, 1193, 1331, 1335, 1350, 1416,
                                    1506, 1525, 1525, 1608, 1663, 1975, 2067, 2131, 2198, 2288, 2445}

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
                'title': comic_json.get('title') if comic_json.get('title') else '...',
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
            return comic_data

    def _get_real_rus_ids(self):
        soup = self._get_soup('https://xkcd.ru/num')
        lis = soup.find('ul', {'class': 'list'}).find_all('li', {'class': 'real'})
        nums = []
        for li in lis:
            nums.append(int(li.text))
        return tuple(nums)

    @staticmethod
    def _get_soup(url):
        response = requests.get(url)
        if response.ok:
            content = response.content
            return BeautifulSoup(content, 'lxml')
        else:
            print(f"Error in _get_soup() for {url}")

    # TODO: make as property
    def get_latest_comic_id(self):
        soup = self._get_soup('https://xkcd.com/archive/')
        comic_id = int(soup.find('div', {'id': 'middleContainer'}).find('a')['href'][1:-1])
        self.latest_comic_id = comic_id
        return comic_id

    async def get_rus_version(self, comic_id):
        keys = ('rus_title', 'rus_img_url', 'rus_comment')

        if comic_id not in self.real_rus_ids:
            return dict(zip(keys, ['']*3))
        else:
            soup = self._get_soup(f'https://xkcd.ru/{comic_id}')
            img = soup.find('img', {'border': 0})
            comment = soup.find('div', {'class': 'comics_text'}).text

            values = (img['alt'], img['src'], comment)
            return dict(zip(keys, values))

    async def get_explanation(self, comic_id):
        url = f'https://www.explainxkcd.com/{comic_id}'
        attempts = 5
        for _ in range(attempts):
            try:
                soup = self._get_soup(url)
                first_p = soup.find_all('div', {'class': 'mw-parser-output'})[-1].find('p')
                text = first_p.text
                for el in first_p.find_next_siblings()[:12]:
                    if el.name in ('p', 'li'):
                        text = text + el.text + '\n'
                text = text[:1000].strip()
                return text, url
            except Exception as err:
                print(f'Error in get_explanation() for {comic_id}: {err}')
                await asyncio.sleep(0.1)

        return "...", url

    async def get_full_comic_data(self, comic_id):
        full_comic_data = await self.get_comic_data(comic_id)
        rus_data = await self.get_rus_version(comic_id)
        full_comic_data.update(rus_data)
        return full_comic_data


parser = Parser()

if __name__ == "__main__":
    # TEST
    import pprint
    import asyncio

    async def test():
        data = await parser.get_full_comic_data(500)
        pprint.pprint(data)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test())
