import requests
import time
from datetime import date
from bs4 import BeautifulSoup


class Parser:
    """1608, 1190, 1416, 404, 1037, 1538, 1953, 1965 - defective"""
    def __init__(self):
        self.latest_comic_id = self.get_and_update_latest_comic_id()
        self._real_rus_ids = self.get_real_rus_ids()

    def get_and_update_latest_comic_id(self):
        url = 'https://xkcd.com/archive/'
        content = requests.get(url).content
        soup = BeautifulSoup(content, 'lxml')
        comic_id = int(soup.find('div', {'id': 'middleContainer'}).find('a')['href'][1:-1])
        self.latest_comic_id = comic_id
        return comic_id

    @staticmethod
    def get_real_rus_ids():
        url = 'https://xkcd.ru/num'
        content = requests.get(url).content
        soup = BeautifulSoup(content, 'lxml')
        lis = soup.find('ul', {'class': 'list'}).find_all('li', {'class': 'real'})
        nums = []
        for li in lis:
            nums.append(int(li.text))
        return tuple(nums)

    @staticmethod
    def get_comic(comic_id):
        if comic_id == 404:
            return {'comic_id': comic_id,
                    'title': '404 ;DDD',
                    'img_url': 'https://www.explainxkcd.com/wiki/images/9/92/not_found.png',
                    'comment': 'Page not found!',
                    'public_date': date(day=1, month=4, year=2008)
                    }
        else:
            url = f'https://xkcd.com/{comic_id}/info.0.json'

            info = requests.get(url).json()

            return {
                'comic_id': comic_id,
                'title': info.get('title'),
                'img_url': info.get('img'),
                'comment': info.get('alt'),
                'public_date': date(day=int(info.get('day')),
                                    month=int(info.get('month')),
                                    year=int(info.get('year')))
            }

    def get_rus_version(self, comic_id):
        keys = ('rus_title', 'rus_img_url', 'rus_comment')

        if comic_id not in self._real_rus_ids:
            return dict(zip(keys, ['']*3))
        else:
            url = f"https://xkcd.ru/{comic_id}"
            content = requests.get(url).content
            soup = BeautifulSoup(content, 'lxml')
            img = soup.find('img', {'border': 0})
            comment = soup.find('div', {'class': 'comics_text'}).text

            values = (img['alt'], img['src'], comment)
            return dict(zip(keys, values))

    @staticmethod
    def get_explanation(comic_id):
        text, url = '', ''
        attempts = 3
        try:
            for _ in range(attempts):
                url = f'https://www.explainxkcd.com/{comic_id}'
                content = requests.get(url).content
                soup = BeautifulSoup(content, 'lxml')
                first_p = soup.find_all('div', {'class': 'mw-parser-output'})[-1].find('p')
                text = first_p.text
                for el in first_p.find_next_siblings()[:12]:
                    if el.name in ('p', 'li'):
                        text = text + el.text + '\n'
                text = text[:1000].strip()
                time.sleep(0.1)
                break
        except Exception as err:
            print(f'Something went wrong in get_explanation() for {comic_id} comic: {err}')

        return text, url

    def get_full_comic_data(self, comic_id):
        comic_data = self.get_comic(comic_id)
        rus_data = self.get_rus_version(comic_id)
        comic_data.update(rus_data)
        return comic_data


if __name__ == "__main__":
    pass



