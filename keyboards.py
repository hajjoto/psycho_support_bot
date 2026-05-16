from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


start_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Почати")]
    ],
    resize_keyboard=True
)


problem_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Завершити діалог")]
    ],
    resize_keyboard=True
)


restart_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Почати нову сесію")]
    ],
    resize_keyboard=True
)