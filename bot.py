import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from states import SupportDialog


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


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


HIGH_RISK_WORDS = [
    "хочу умереть",
    "хочу померти",
    "не хочу жить",
    "не хочу жити",
    "суицид",
    "самогубство",
    "убить себя",
    "вбити себе",
    "покончить с собой",
    "накласти на себе руки",
    "самоповреждение",
    "самоушкодження"
]


MEDIUM_RISK_WORDS = [
    "паника",
    "паніка",
    "паническая атака",
    "панічна атака",
    "сильная тревога",
    "сильна тривога",
    "бессонница",
    "безсоння",
    "не справляюсь",
    "не справляюся",
    "очень плохо",
    "дуже погано"
]


LOW_RISK_WORDS = [
    "стресс",
    "стрес",
    "усталость",
    "втома",
    "одиночество",
    "самотність",
    "отношения",
    "відносини",
    "тревога",
    "тривога",
    "грусть",
    "сум"
]

def analyze_risk(text: str) -> str:
    text = text.lower()

    if any(word in text for word in HIGH_RISK_WORDS):
        return "HIGH"

    if any(word in text for word in MEDIUM_RISK_WORDS):
        return "MEDIUM"

    if any(word in text for word in LOW_RISK_WORDS):
        return "LOW"

    return "LOW"


def get_recommendation(risk_level: str) -> str:
    if risk_level == "MEDIUM":
        return (
            "Ваш стан виглядає напруженим. Спробуйте техніку grounding 5-4-3-2-1:\n\n"
            "5 речей, які ви бачите\n"
            "4 речі, які можете відчути тілом\n"
            "3 звуки, які чуєте\n"
            "2 запахи\n"
            "1 річ, яку можете назвати про себе зараз\n\n"
            "Також зробіть дихання: вдих 4 секунди, видих 6 секунд. Повторіть 5 разів.\n\n"
            "Якщо стан не проходить або посилюється, зверніться до психолога або лікаря."
        )

    return (
        "Схоже, ваш стан не є критичним, але вам потрібна підтримка.\n\n"
        "Спробуйте:\n"
        "1. Записати, що саме вас турбує.\n"
        "2. Відділити факти від думок.\n"
        "3. Зробити коротку прогулянку або паузу.\n"
        "4. Поговорити з людиною, якій довіряєте.\n\n"
        "Дихальна вправа: вдих на 4 секунди, видих на 6 секунд, 5 повторів."
    )


CRISIS_TEXT = (
    "Мені дуже шкода, що вам зараз настільки важко.\n\n"
    "Я не можу допомагати з діями, які можуть нашкодити вам.\n\n"
    "Зараз важливо не залишатися наодинці. Зверніться до людини поруч або до екстрених служб.\n\n"
    "Україна:\n"
    "Екстрена допомога: 112 або 103\n"
    "Lifeline Ukraine: 7333\n\n"
    "Якщо є негайна небезпека — телефонуйте 112 прямо зараз."
)


@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(SupportDialog.consent)

    await message.answer(
        "Вітаю. Це бот анонімної психологічної підтримки.\n\n"
        "Бот не просить ваше імʼя, телефон, адресу або інші персональні дані.\n"
        "Ваше повідомлення використовується тільки для поточного діалогу.\n\n"
        "Бот не замінює психолога або лікаря. "
        "У кризових ситуаціях потрібно звертатися до екстрених служб.\n\n"
        "Щоб почати, натисніть «Почати».",
        reply_markup=start_keyboard
    )


@dp.message(SupportDialog.consent, F.text == "Почати")
async def process_consent(message: Message, state: FSMContext):
    await state.set_state(SupportDialog.collecting_problem)

    await message.answer(
        "Опишіть у кількох словах, що вас зараз турбує.\n\n"
        "Не вказуйте імʼя, телефон, адресу або інші персональні дані.",
        reply_markup=problem_keyboard
    )


@dp.message(SupportDialog.consent)
async def wrong_consent_message(message: Message):
    await message.answer(
        "Щоб почати діалог, натисніть кнопку «Почати».",
        reply_markup=start_keyboard
    )


@dp.message(SupportDialog.collecting_problem, F.text == "Завершити діалог")
async def finish_from_problem(message: Message, state: FSMContext):
    await state.set_state(SupportDialog.finished)

    await message.answer(
        "Діалог завершено. Ви можете почати нову сесію будь-коли.",
        reply_markup=restart_keyboard
    )


@dp.message(SupportDialog.collecting_problem)
async def collect_problem(message: Message, state: FSMContext):
    problem_text = message.text
    risk_level = analyze_risk(problem_text)

    await state.update_data(
        problem_text=problem_text,
        risk_level=risk_level
    )

    if risk_level == "HIGH":
        await state.set_state(SupportDialog.crisis_mode)

        await message.answer(
            CRISIS_TEXT,
            reply_markup=restart_keyboard
        )

        await state.set_state(SupportDialog.finished)
        return

    await state.set_state(SupportDialog.recommendations)

    recommendation = get_recommendation(risk_level)

    await message.answer(
        f"Рівень ризику: {risk_level}\n\n"
        f"{recommendation}",
        reply_markup=restart_keyboard
    )

    await state.set_state(SupportDialog.finished)


@dp.message(SupportDialog.finished, F.text == "Почати нову сесію")
async def restart_session(message: Message, state: FSMContext):
    await start(message, state)


@dp.message(SupportDialog.finished)
async def finished_message(message: Message):
    await message.answer(
        "Поточний діалог завершено. Щоб почати заново, натисніть «Почати нову сесію».",
        reply_markup=restart_keyboard
    )


@dp.message()
async def unknown_message(message: Message, state: FSMContext):
    current_state = await state.get_state()

    if current_state is None:
        await message.answer(
            "Натисніть /start, щоб почати діалог."
        )
    else:
        await message.answer(
            "Я не зрозумів повідомлення. Натисніть /start, щоб почати заново."
        )


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
