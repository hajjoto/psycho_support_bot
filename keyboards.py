from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


start_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Почати")]
    ],
    resize_keyboard=True
)


dialog_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Завершити діалог")]
    ],
    resize_keyboard=True
)


feedback_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Стало легше"), KeyboardButton(text="Не стало легше")],
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

feedback_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Стало легше"), KeyboardButton(text="Не стало легше")],
        [KeyboardButton(text="Завершити діалог")]
    ],
    resize_keyboard=True
)


finish_or_advice_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Завершити діалог")],
        [KeyboardButton(text="Ще одна порада")]
    ],
    resize_keyboard=True
)
