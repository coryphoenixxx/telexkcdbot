import json
import requests
from bs4 import BeautifulSoup


BASE_URL = 'https://xkcd.com/'
RUS_URL = "https://xkcd.ru/num/"
EXPLAIN_URL = "https://www.explainxkcd.com"

def get_comic(number):
    url = f"{BASE_URL}/{number}/info.0.json"
    info = requests.get(url).json()

    data = {
        'num': number,
        'title': info['title'],
        'img_url': info['img'],
        'comment': info['alt'],
    }
    return data


def get_rus_version(number):

    content = requests.get(RUS_URL).content
    soup = BeautifulSoup(content, 'lxml')
    li = soup.find('ul', {'class': 'list'}).find_all('li', {'class': 'real'})
    nums = []
    for i in li:
        nums.append(int(i.text))

    if number in nums:
        content = requests.get(f"https://xkcd.ru/{number}/").content
        soup = BeautifulSoup(content, 'lxml')
        img = soup.find('img', {'border': 0})
        comment = soup.find('div', {'class': 'comics_text'}).text

        data = {
            'num': number,
            'title': img['alt'],
            'img_url': img['src'],
            'comment': comment,
        }

        return data
    else:
        return None


def get_eng_explanation(number):
    url = f"{EXPLAIN_URL}/{number}/"
    content = requests.get(url).content
    soup = BeautifulSoup(content, 'lxml')
    first_p = soup.find('span', {'id': 'Explanation'}).parent.findNext('p').text
    return f"{first_p}\n<b>\"<a href='{url}'>...full text</a>\"</b>"


if __name__ == "__main__":
    print(get_eng_explanation(355))
