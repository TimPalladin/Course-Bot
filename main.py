import asyncio
import requests
from bs4 import BeautifulSoup as bs

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

import config
import json

# ====================== Настройки ======================
FILENAME = 'course.json'
last_rates = None


# ====================== Парсер ======================
def parse_course(force_update=False):
    global last_rates

    if not force_update and last_rates:
        return last_rates

    url = 'https://www.cbr.ru/currency_base/daily/'
    response = requests.get(url)

    if response.status_code != 200:
        print('Ошибка подключения!')
        return last_rates if last_rates else {}

    soup = bs(response.text, 'html.parser')
    currencies = {}

    for block in soup.find_all('tr'):
        cells = block.find_all('td')
        if len(cells) >= 5:
            code = cells[1].text.strip()
            if code:
                currencies[code] = {
                    'name': cells[3].text.strip(),
                    'value': cells[4].text.strip()
                }

    save_data(currencies)
    last_rates = currencies
    print(f"✅ Обновлено {len(currencies)} валют")
    return currencies


def save_data(data):
    with open(FILENAME, 'w', encoding="utf-8") as jf:
        json.dump(data, jf, indent=4, ensure_ascii=False)


# ====================== Бот ======================
bot = Bot(token=config.TOKEN)
dp = Dispatcher()


@dp.message(Command('start'))
async def start(message: types.Message):
    await message.answer("👋 Привет! Я бот курсов валют ЦБ РФ.\n\nНапиши /help для списка команд")


@dp.message(Command('help'))
async def cmd_help(message: types.Message):
    await message.answer(
        "📋 Доступные команды:\n"
        "/usd — Доллар США\n"
        "/eur — Евро\n"
        "/cny — Китайский юань\n"
        "/gbp — Фунт стерлингов\n"
        "/try — Турецкая лира\n"
        "/all — Первые 15 валют"
    )


@dp.message(Command('usd', 'eur', 'cny', 'gbp', 'try'))
async def cmd_currency(message: types.Message):
    code = message.text[1:].upper()
    rates = parse_course()

    if code in rates:
        info = rates[code]
        await message.answer(f"{info['name']} ({code})\n💰 Курс: {info['value']} ₽")
    else:
        await message.answer("❌ Не удалось получить курс")


@dp.message(Command('all'))
async def cmd_all(message: types.Message):
    await message.answer("⏳ Загружаю актуальные курсы...")
    rates = parse_course()
    text = "📊 Актуальные курсы ЦБ РФ:\n\n"

    for code, info in list(rates.items())[:15]:
        text += f"{info['name']} ({code}): {info['value']} ₽\n"

    await message.answer(text)


async def main():
    print("🤖 Бот успешно запущен!")
    await dp.start_polling(bot)


if __name__ == '__main__':
    print("Загружаем актуальные курсы...")
    parse_course()
    asyncio.run(main())