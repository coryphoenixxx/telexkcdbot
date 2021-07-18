import requests
from datetime import date
from bs4 import BeautifulSoup


# 1608, 1190, 1416, 404, 1037, 1538, 1953, 1965(div) - defective

class Parser:
    def __init__(self):
        self.last_comic_number = self.get_last_comic_number()
        self.real_rus_numbers = self.get_real_rus_numbers()

    @staticmethod
    def get_last_comic_number():
        url = 'https://xkcd.com/archive/'
        content = requests.get(url).content
        soup = BeautifulSoup(content, 'lxml')
        number = int(soup.find('div', {'id': 'middleContainer'}).find('a')['href'][1:-1])
        return number

    @staticmethod
    def get_real_rus_numbers():
        url = 'https://xkcd.ru/num'
        content = requests.get(url).content
        soup = BeautifulSoup(content, 'lxml')
        li = soup.find('ul', {'class': 'list'}).find_all('li', {'class': 'real'})
        nums = []
        for i in li:
            nums.append(int(i.text))
        return tuple(nums)

    @staticmethod
    def get_comic(number):

        url = f'https://xkcd.com/{number}/info.0.json'
        response = requests.get(url)

        if not response.ok:
            pass

        info = response.json()

        return {
            'number': number,
            'title': info.get('title'),
            'img_url': info.get('img'),
            'comment': info.get('alt'),
            'public_date': date(day=int(info.get('day')), month=int(info.get('month')), year=int(info.get('year')))
        }

    def get_rus_version(self, number):
        keys = ('rus_title', 'rus_img_url', 'rus_comment')

        if number not in self.real_rus_numbers:
            return dict(zip(keys, ['']*3))
        else:
            url = f"https://xkcd.ru/{number}/"
            content = requests.get(url).content
            soup = BeautifulSoup(content, 'lxml')
            img = soup.find('img', {'border': 0})
            comment = soup.find('div', {'class': 'comics_text'}).text

            values = (img['alt'], img['src'], comment)
            return dict(zip(keys, values))

    @staticmethod
    def get_explain(number):
        first_p = ''
        for _ in range(3):
            try:
                url = f'https://www.explainxkcd.com/{number}'
                content = requests.get(url).content
                soup = BeautifulSoup(content, 'lxml')
                first_p = soup.find_all('div', {'class': 'mw-parser-output'})[-1].find('p').text
                break
            except Exception as err:
                print(f'Something went wrong in get_explain for {number} comic: {err}')
        return first_p

    def get_full_comic_data(self, number):
        try:
            full_data = self.get_comic(number)
            rus_data = self.get_rus_version(number)
            explain_text = self.get_explain(number)
            if not explain_text:
                raise Exception('Incorrect getting explain_text!!!')
            full_data.update(rus_data)
            full_data['explain_text'] = explain_text

            return full_data
        except Exception as e:
            print(f'Something went wrong with {number} comic handling...: ', e)


if __name__ == "__main__":
    p = Parser()
    data = p.get_full_comic_data(666)
    print(data)

