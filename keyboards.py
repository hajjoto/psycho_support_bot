from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


start_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="▶️ Почати")]
    ],
    resize_keyboard=True
)


start_time_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✅ Так, маю пару хвилини")],
        [KeyboardButton(text="⚡ Ні, потрібно швидше")]
    ],
    resize_keyboard=True
)


urgent_protocol_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="⚡ Терміновий протокол")],
        [KeyboardButton(text="🧘 Повний варіант")]
    ],
    resize_keyboard=True
)


dialog_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="⛔ Завершити діалог")]
    ],
    resize_keyboard=True
)


restart_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔄 Почати нову сесію")]
    ],
    resize_keyboard=True
)


scale_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔴 9–10")] ,
        [KeyboardButton(text="🟠 6–8")] ,
        [KeyboardButton(text="🟡 1–5")] ,
        [KeyboardButton(text="⛔ Завершити діалог")]
    ],
    resize_keyboard=True
)


yes_no_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="✅ Так"),
            KeyboardButton(text="❌ Ні")
        ],
        [KeyboardButton(text="⛔ Завершити діалог")]
    ],
    resize_keyboard=True
)


protocol_choice_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="⚡ Коротка вправа")],
        [KeyboardButton(text="🧘 Повна вправа")],
        [KeyboardButton(text="⛔ Завершити діалог")]
    ],
    resize_keyboard=True
)


protocol_next_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➡️ Далі")],
        [KeyboardButton(text="⛔ Завершити діалог")]
    ],
    resize_keyboard=True
)


protocol_feedback_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="✅ Стало легше"),
            KeyboardButton(text="❌ Не стало легше")
        ],
        [KeyboardButton(text="🔄 Спробувати іншу вправу")],
        [KeyboardButton(text="⛔ Завершити діалог")]
    ],
    resize_keyboard=True
)


done_next_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➡️ Далі")],
        [KeyboardButton(text="⛔ Завершити діалог")]
    ],
    resize_keyboard=True
)


scenario_choice_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🧠 Зрозуміти свій стан")],
        [KeyboardButton(text="🧘 Перейти до вправ")],
        [KeyboardButton(text="📌 Поради на день")],
        [KeyboardButton(text="⛔ Завершити діалог")]
    ],
    resize_keyboard=True
)

keep_intro_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📖 Показати способи")],
        [KeyboardButton(text="⏳ Іншим разом")]
    ],
    resize_keyboard=True
)


keep_finish_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✅ Дякую")],
        [KeyboardButton(text="▶️ Знизити напругу зараз")]
    ],
    resize_keyboard=True
)

keep_next_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✅ Далі")],
        [KeyboardButton(text="🧭 Перейти до опитування")],
        [KeyboardButton(text="⛔ Завершити діалог")]
    ],
    resize_keyboard=True
)

support_detail_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔎 Що зі мною відбувається")],
        [KeyboardButton(text="🛠 Що може допомогти")],
        [KeyboardButton(text="🚫 Чого краще не робити")],
        [KeyboardButton(text="📋 План на 30 хвилин")],
        [KeyboardButton(text="🧘 Перейти до вправ")],
        [KeyboardButton(text="⛔ Завершити діалог")]
    ],
    resize_keyboard=True
)

finish_or_advice_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💡 Ще одна порада")],
        [KeyboardButton(text="🔄 Нова вправа")],
        [KeyboardButton(text="⛔ Завершити діалог")]
    ],
    resize_keyboard=True
)
