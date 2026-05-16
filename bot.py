import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from states import SupportDialog
from logger_config import setup_logger
from risk_analyzer import analyze_risk
from recommendations import get_recommendation
from session_service import create_session_id
from keyboards import start_keyboard, problem_keyboard, restart_keyboard


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


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

    session_id = create_session_id()

    await state.update_data(
        session_id=session_id
    )

    logging.info(f"New anonymous session created: {session_id}")

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

    logging.info(f"Risk level detected: {risk_level}")

    await state.update_data(
        problem_text=problem_text,
        risk_level=risk_level
    )

    recommendation = get_recommendation(risk_level)

    if risk_level == "HIGH":
        await state.set_state(SupportDialog.crisis_mode)

        await message.answer(
            recommendation,
            reply_markup=restart_keyboard
        )

        await state.set_state(SupportDialog.finished)
        return

    await state.set_state(SupportDialog.recommendations)

    await message.answer(
        recommendation,
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
        await message.answer("Натисніть /start, щоб почати діалог.")
    else:
        await message.answer("Я не зрозумів повідомлення. Натисніть /start, щоб почати заново.")


async def main():
    setup_logger()
    logging.info("Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
