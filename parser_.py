import requests
from bs4 import BeautifulSoup


def get_comic(number):
    url = f"https://xkcd.com/{number}"
    content = requests.get(url).content
    soup = BeautifulSoup(content, 'lxml')
    img_html = soup.find('div', {'id': 'comic'}).find_all_next('br')[1].next
    img_url = img_html.split()[-1]
    return img_url


if __name__ == "__main__":
    import random
    last = 2485
    num = random.randint(1, last)
    print(get_comic(num))
