"""
The app does not use the script while it is running.
It was used to parse xkcd.su and add new russian comics data to csv and download images.
Saved for history.
"""

import asyncio
import csv
import re
from pathlib import Path

import aiofiles
import aiofiles.os
import aiohttp
from bs4 import BeautifulSoup
from tqdm import tqdm

sem = asyncio.Semaphore(64)  # Limits simultaneous connections on Windows
comics_data = []

PATH_TO_CSV = Path('')
IMG_DIR = Path('')


def cut_into_chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


async def get_all(comic_id):
    async with sem:
        comic_data = await get_ru_comic_data_from_xkcd_su(comic_id)
        if comic_data:
            await download_image(comic_data['ru_img_url'], comic_id)
            comics_data.append({'comic_id': comic_id,
                                'ru_title': comic_data['ru_title'],
                                'ru_comment': comic_data['ru_comment']})


async def get_ru_comic_data_from_xkcd_su(comic_id):
    url = f'https://xkcd.su/finished/{comic_id}'

    async with aiohttp.ClientSession(trust_env=True) as session:
        response = await session.get(url,  ssl=False)
        content = await response.content.read()
        soup = BeautifulSoup(content, 'lxml')

        finished = soup.find('div', {'class': 'finished_check'})

        if finished:
            ru_title = soup.find('div', {'class': 'finished_title'}).text
            ru_title = re.search('«(.*)»', ru_title).group(1)

            ru_img_url = soup.find('div', {'class': 'comics_img'}).find('img')['src']

            ru_comment = soup.find('div', {'class': 'finished_alt'}).text
            ru_comment = ru_comment.replace('<', '').replace('>', '').strip()
            ru_comment = ru_comment if ru_comment else '...'

            if comic_id == 384:
                ru_img_url = 'https://xkcd.ru/i/384_v1.png'  # Image from .su is broken

            return dict(zip(('ru_title', 'ru_img_url', 'ru_comment'), (ru_title, ru_img_url, ru_comment)))


async def write_to_csv():
    global comics_data
    with open(PATH_TO_CSV, 'a', encoding='utf-8', newline='') as csv_file:
        csv_writer = csv.DictWriter(csv_file, fieldnames=['comic_id', 'ru_title', 'ru_comment'])
        csv_writer.writerows(comics_data)
    comics_data = []


async def download_image(img_url, comic_id):
    filepath = IMG_DIR / f'{comic_id}.jpg'
    async with aiohttp.ClientSession() as session:
        response = await session.get(img_url, ssl=False)
        async with aiofiles.open(filepath, mode='wb') as f:
            await f.write(await response.read())


async def get_current_csv_ru_comics_ids():
    comics_ids = set()
    with open(PATH_TO_CSV, 'r', encoding='utf-8') as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter=',')
        for row in csv_reader:
            comics_ids.add(int(row['comic_id']))

    return comics_ids


async def gather(chunk):
    tasks = []
    for comic_id in chunk:
        task = asyncio.create_task(get_all(comic_id))
        tasks.append(task)

    await asyncio.gather(*tasks)


async def main():
    current_csv_ru_comics_ids = await get_current_csv_ru_comics_ids()
    residuary = list(set(range(1, 2500)).symmetric_difference(current_csv_ru_comics_ids))

    chunk = 10
    for chunk in tqdm(list(cut_into_chunks(residuary, chunk))):
        await gather(chunk)
        await write_to_csv()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
