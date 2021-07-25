import requests
from datetime import date
from bs4 import BeautifulSoup


class Parser:
    def __init__(self):
        self.latest_comic_id = self.get_and_update_latest_comic_id()
        self._real_rus_ids = self.get_real_rus_ids()
        self._specific_comic_ids = {826, 880, 980, 1037, 1110, 1190, 1193, 1331, 1335, 1350, 1416,
                                    1506, 1525, 1525, 1608, 1663, 1975, 2067, 2131, 2198, 2288, 2445}

    def get_comic(self, comic_id):
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

            data = {
                'comic_id': comic_id,
                'title': comic_json.get('title') if comic_json.get('title') else '...',
                'img_url': comic_json.get('img'),
                'comment': comic_json.get('alt') if comic_json.get('alt') else '...',
                'public_date': date(day=int(comic_json.get('day')),
                                    month=int(comic_json.get('month')),
                                    year=int(comic_json.get('year'))),
                'is_specific': 1 if comic_id in self._specific_comic_ids else 0
            }
            return data

    @staticmethod
    def get_soup(url):
        content = requests.get(url).content
        return BeautifulSoup(content, 'lxml')

    def get_and_update_latest_comic_id(self):
        soup = self.get_soup('https://xkcd.com/archive/')
        comic_id = int(soup.find('div', {'id': 'middleContainer'}).find('a')['href'][1:-1])
        self.latest_comic_id = comic_id
        return comic_id

    def get_real_rus_ids(self):
        soup = self.get_soup('https://xkcd.ru/num')
        lis = soup.find('ul', {'class': 'list'}).find_all('li', {'class': 'real'})
        nums = []
        for li in lis:
            nums.append(int(li.text))
        return tuple(nums)

    def get_rus_version(self, comic_id):
        keys = ('rus_title', 'rus_img_url', 'rus_comment')

        if comic_id not in self._real_rus_ids:
            return dict(zip(keys, ['']*3))
        else:
            soup = self.get_soup(f'https://xkcd.ru/{comic_id}')
            img = soup.find('img', {'border': 0})
            comment = soup.find('div', {'class': 'comics_text'}).text

            values = (img['alt'], img['src'], comment)
            return dict(zip(keys, values))

    async def get_explanation(self, comic_id):
        url = f'https://www.explainxkcd.com/{comic_id}'
        attempts = 3
        for _ in range(attempts):
            try:
                soup = self.get_soup(url)
                first_p = soup.find_all('div', {'class': 'mw-parser-output'})[-1].find('p')
                text = first_p.text
                for el in first_p.find_next_siblings()[:12]:
                    if el.name in ('p', 'li'):
                        text = text + el.text + '\n'
                text = text[:1000].strip()
                return text, url
            except Exception as err:
                print(f'Something went wrong in get_explanation() for {comic_id} comic: {err}')  # TODO: in log

        return "...", url

    def get_full_comic_data(self, comic_id):
        comic_data = self.get_comic(comic_id)
        rus_data = self.get_rus_version(comic_id)
        comic_data.update(rus_data)
        return comic_data


if __name__ == "__main__":
    pass
