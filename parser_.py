import requests
from bs4 import BeautifulSoup


BASE_URL = 'https://xkcd.com/'


def get_comic(number):
    url = BASE_URL + str(number)
    content = requests.get(url).content
    soup = BeautifulSoup(content, 'lxml')
    img = soup.find('div', {'id': 'comic'}).find_next('img')

    data = {
        'num': number,
        'title': soup.find('div', {'id': 'ctitle'}).text,
        'img_url': 'https:' + img.get('src'),
        'comment': img.get('title')
    }
    print(data)

    # img_url_html = soup.find('div', {'id': 'comic'}).find_all_next('br')[1].next
    # img_url_real = img_url_html.split()[-1]
    # img = soup.find('div', {'id': 'comic'}).find_next('img')

    return data


if __name__ == "__main__":
    import random

    num = random.randint(1, 2800)
    get_comic(num)
