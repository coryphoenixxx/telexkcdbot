import asyncio

from aiogram.types import Message
from aiogram import Bot, Dispatcher, executor

from parser_ import get_comic
from config import Config


loop = asyncio.get_event_loop()
bot = Bot(Config.API_TOKEN)
dp = Dispatcher(bot, loop=loop)


async def notify_admin(dp):
    await bot.send_message(chat_id=Config.ADMIN_ID, text="Bot in Your Power, My Lord!")


@dp.message_handler(commands=['start', 'help'])
async def hello(message: Message):
    await message.answer('Hi! I\'m TeleXKCDbot')
    await asyncio.sleep(1)
    await message.answer('Write the xkcd-comic\'s number')


@dp.message_handler()
async def echo(message: Message):
    user_input = message.text
    if user_input.isdigit():
        img_url = get_comic(user_input)
        await message.answer_photo(photo=img_url)
    else:
        await message.answer('Please, write a number!')


if __name__ == "__main__":
    executor.start_polling(dp, on_startup=notify_admin)
