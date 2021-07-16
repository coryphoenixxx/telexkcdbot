import requests
from bs4 import BeautifulSoup


# 1608, 1190, 1416, 404, 1037, 1538, 1953, 1965(div) - defective


def get_comic(number):
    url = f'https://xkcd.com/{number}/info.0.json'
    info = requests.get(url).json()

    num = str(number)
    title = info['title']
    img_url = info['img']
    comment = info['alt']
    day = str(info['day'])
    month = str(info['month'])
    year = str(info['year'])

    headline = f"<b>{num}. \"<a href='{'https://xkcd.com/' + num}'>{title}</a>\"</b>   <i>({day}-{month}-{year})</i>"

    data = {
        'headline': headline,
        'img_url': img_url,
        'comment': comment,
    }

    return data


def get_rus_version(number):
    """MUST CALL ONCE OR IN SCHEDULER"""
    content = requests.get('https://xkcd.ru/num').content
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


def get_explanation(number):
    url = f'https://www.explainxkcd.com/{number}'
    content = requests.get(url).content
    soup = BeautifulSoup(content, 'lxml')
    first_p = soup.find('span', {'id': 'Explanation'}).parent.findNext('p').text
    text = f"{first_p}<i><b><a href='{url}'>...continue</a></b></i>"
    return text


if __name__ == "__main__":
    print(get_comic(500))
