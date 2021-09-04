# This file not use in app
# it's only for parse xkcd_ru_tg_channel.html
# and create json with comics data

import re
import json
from bs4 import BeautifulSoup
from bs4.element import NavigableString


with open("xkcd_ru_tg_channel.html", 'rb') as fp:
    soup = BeautifulSoup(fp, 'lxml')

footers = soup.find_all('div', {'class': 'tgme_widget_message_text'})

messages = soup.find_all('div', class_='tgme_widget_message js-widget_message')

ru_data_dict = {}

for msg in messages:
    footer = msg.find_all('div', {'class': 'tgme_widget_message_text'})
    contents = footer[0].contents

    try:
        ru_title = contents[0].text
    except Exception as err:
        print(err)
        continue

    if ru_title.endswith('.'):
        ru_title = ru_title[:-1]

    nav_tags = list(filter(lambda x: type(x) == NavigableString, contents))

    ru_comment = ' '.join(nav_tags[:-1])
    ru_comment = ru_comment.replace('>', '')

    comic_id = nav_tags[-1].strip()[1:]

    style_text = msg.find_next('a', class_='tgme_widget_message_photo_wrap')['style']
    ru_img_url = re.search('\(\'(.*)\'\)', style_text).group(1)

    ru_data_dict[comic_id] = {'ru_title': ru_title,
                              'ru_img_url': ru_img_url,
                              'ru_comment': ru_comment}


with open('ru_data_from_xkcd_ru_tg_channel.json', 'w', encoding='utf8') as f:
    json.dump(ru_data_dict, f, ensure_ascii=False, indent=4)

