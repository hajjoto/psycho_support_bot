import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart, Command

from config import BOT_TOKEN, ADMIN_ID
from database import init_db, save_request, get_all_requests


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Тривога"), KeyboardButton(text="Стрес")],
        [KeyboardButton(text="Самотність"), KeyboardButton(text="Проблеми у відносинах")],
        [KeyboardButton(text="Написати звернення")],
        [KeyboardButton(text="Допомога")]
    ],
    resize_keyboard=True
)


user_categories = {}

CRISIS_WORDS = [
    "хочу умереть",
    "хочу померти",
    "покончить с собой",
    "накласти на себе руки",
    "суицид",
    "самогубство",
    "не хочу жить",
    "не хочу жити",
    "убить себя",
    "вбити себе"
]


CRISIS_TEXT = (
    "Мені дуже шкода, що вам зараз настільки важко.\n\n"
    "Я не можу допомагати з діями, які можуть нашкодити вам.\n\n"
    "Зараз важливо не залишатися наодинці. "
    "Зателефонуйте до служби екстреної допомоги або зверніться до близької людини поруч.\n\n"
    "Україна:\n"
    "Екстрена допомога: 112 або 103\n"
    "Lifeline Ukraine: 7333\n\n"
    "Якщо є негайна небезпека — телефонуйте 112 прямо зараз."
)


def is_crisis_message(text: str) -> bool:
    text = text.lower()
    return any(word in text for word in CRISIS_WORDS)

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "Вытаю. Це анонімний бот психологічної підтримки.\n\n"
        "Оберіть тему або натисніть «Написати звернення».\n\n"
        "Важливо: бот не замінює психолога або лікаря, але він допомагає. "
        "Якщо є загроза життю чи здоровʼю зверніться до екстрених служб.",
        reply_markup=main_keyboard
    )

@dp.message()
async def save_user_message(message: Message):
    if is_crisis_message(message.text):
        await message.answer(CRISIS_TEXT)
        return

    user_id = message.from_user.id
    category = user_categories.get(user_id, "Без категорії")

    save_request(
        user_id=user_id,
        category=category,
        message=message.text
    )

    await message.answer(
        "Ваше звернення збережено.\n\n"
        "Спробуйте зараз зробити коротку паузу: "
        "повільний вдих на 4 секунди, видих на 6 секунд, повторити 5 разів.\n\n"
        "Якщо ситуація критична або є ризик нашкодити собі — зверніться до екстреної допомоги."
    )

@dp.message(F.text.in_(["Тривога", "Стрес", "Самотність", "Проблеми у відносинах"]))
async def choose_category(message: Message):
    user_categories[message.from_user.id] = message.text

    await message.answer(
        f"Категорія обрана: {message.text}\n\n"
        "Тепер напишіть, що вас турбує. "
        "Не вказуйте імʼя, адресу, телефон або інші особисті дані."
    )


@dp.message(F.text == "Написати звернення")
async def write_request(message: Message):
    user_categories[message.from_user.id] = "Загальне звернення"

    await message.answer(
        "Напишіть ваше звернення одним повідомленням.\n\n"
        "Не вказуйте персональні дані."
    )


@dp.message(F.text == "Допомога")
async def help_message(message: Message):
    await message.answer(
        "Як користуватися ботом:\n\n"
        "1. Оберіть категорію проблеми.\n"
        "2. Напишіть звернення.\n"
        "3. Бот збереже його анонімно.\n"
        "4. Адміністратор зможе переглянути звернення.\n\n"
        "У кризовій ситуації звертайтесь до екстрених служб."
    )


@dp.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("У вас немає доступу.")
        return

    requests = get_all_requests()

    if not requests:
        await message.answer("Звернень поки немає.")
        return

    text = "Останні звернення:\n\n"

    for request in requests[:10]:
        request_id, category, user_message, created_at = request
        text += (
            f"ID: {request_id}\n"
            f"Категорія: {category}\n"
            f"Дата: {created_at}\n"
            f"Текст: {user_message}\n\n"
        )

    await message.answer(text)


@dp.message()
async def save_user_message(message: Message):
    user_id = message.from_user.id
    category = user_categories.get(user_id, "Без категорії")

    save_request(
        user_id=user_id,
        category=category,
        message=message.text
    )

    await message.answer(
        "Ваше звернення збережено.\n\n"
        "Спробуйте зараз зробити коротку паузу: "
        "повільний вдих на 4 секунди, видих на 6 секунд, повторити 5 разів.\n\n"
        "Якщо ситуація критична або є ризик нашкодити собі — зверніться до екстреної допомоги."
    )


async def main():
    init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())