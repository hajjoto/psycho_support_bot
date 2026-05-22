import asyncio
import logging
import random

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from states import SupportDialog
from logger_config import setup_logger
from risk_analyzer import (
    is_crisis,
    classify_branch,
    analyze_final_risk,
    classify_coping_answer
)
from recommendations import (
    CRISIS_TEXT,
    get_branch_intro,
    get_recommendation,
    get_followup_support,
    build_summary
)
from session_service import create_session_id
from keyboards import (
    start_keyboard,
    dialog_keyboard,
    feedback_keyboard,
    restart_keyboard,
    finish_or_advice_keyboard
)
from database import init_db, create_session, save_message, update_session_risk
from therapy_flows import THERAPY_FLOWS


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


async def finish_dialog(message: Message, state: FSMContext, text: str):
    data = await state.get_data()
    session_id = data.get("session_id")

    if session_id:
        await update_session_risk(
            session_id=session_id,
            risk_level=data.get("risk_level", "UNKNOWN"),
            status="finished"
        )

    await state.set_state(SupportDialog.finished)

    await message.answer(
        text,
        reply_markup=restart_keyboard
    )


async def crisis_intercept(message: Message, state: FSMContext) -> bool:
    if not message.text:
        return False

    if not is_crisis(message.text):
        return False

    data = await state.get_data()
    session_id = data.get("session_id")

    if session_id:
        await save_message(session_id, "user", message.text, "crisis_intercept")
        await save_message(session_id, "bot", CRISIS_TEXT, "crisis_mode")
        await update_session_risk(session_id, "HIGH", "crisis")

    await state.update_data(risk_level="HIGH")
    await state.set_state(SupportDialog.crisis_mode)

    logging.info("Crisis mode activated")

    await message.answer(
        CRISIS_TEXT,
        reply_markup=restart_keyboard
    )

    await state.set_state(SupportDialog.finished)
    return True


@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(SupportDialog.consent)

    await message.answer(
        "Вітаю. Це бот анонімної психологічної підтримки.\n\n"
        "Бот не просить ваше імʼя, телефон, адресу або інші персональні дані.\n"
        "Ваші повідомлення використовуються для поточного діалогу та анонімної сесії.\n\n"
        "Бот не замінює психолога або лікаря.\n"
        "У кризових ситуаціях потрібно звертатися до екстрених служб.\n\n"
        "Щоб почати, натисніть «Почати».",
        reply_markup=start_keyboard
    )


@dp.message(SupportDialog.consent, F.text == "Почати")
async def process_consent(message: Message, state: FSMContext):
    session_id = create_session_id()

    await create_session(session_id)

    await state.update_data(session_id=session_id)
    await state.set_state(SupportDialog.open_problem)

    logging.info(f"New anonymous session created: {session_id}")

    await message.answer(
        "Опишіть у кількох реченнях, що вас зараз турбує.\n\n"
        "Не вказуйте імʼя, телефон, адресу або інші персональні дані.",
        reply_markup=dialog_keyboard
    )


@dp.message(SupportDialog.consent)
async def wrong_consent_message(message: Message):
    await message.answer(
        "Щоб почати діалог, натисніть кнопку «Почати».",
        reply_markup=start_keyboard
    )


@dp.message(F.text == "Завершити діалог")
async def manual_finish(message: Message, state: FSMContext):
    await finish_dialog(
        message,
        state,
        "Діалог завершено. Ви можете почати нову сесію будь-коли."
    )


@dp.message(SupportDialog.open_problem)
async def open_problem(message: Message, state: FSMContext):
    if await crisis_intercept(message, state):
        return

    data = await state.get_data()
    session_id = data.get("session_id")

    branch = classify_branch(message.text)

    await state.update_data(
        problem_text=message.text,
        branch=branch
    )

    if session_id:
        await save_message(session_id, "user", message.text, "open_problem")

    await state.set_state(SupportDialog.duration_check)

    await message.answer(
        f"{get_branch_intro(branch)}\n\n"
        "Як давно ви це відчуваєте?",
        reply_markup=dialog_keyboard
    )


@dp.message(SupportDialog.duration_check)
async def duration_check(message: Message, state: FSMContext):
    if await crisis_intercept(message, state):
        return

    data = await state.get_data()
    session_id = data.get("session_id")

    await state.update_data(duration=message.text)

    if session_id:
        await save_message(session_id, "user", message.text, "duration_check")

    await state.set_state(SupportDialog.trigger_check)

    await message.answer(
        "Що, на вашу думку, найбільше вплинуло на цей стан?",
        reply_markup=dialog_keyboard
    )


@dp.message(SupportDialog.trigger_check)
async def trigger_check(message: Message, state: FSMContext):
    if await crisis_intercept(message, state):
        return

    data = await state.get_data()
    session_id = data.get("session_id")

    await state.update_data(trigger=message.text)

    if session_id:
        await save_message(session_id, "user", message.text, "trigger_check")

    await state.set_state(SupportDialog.impact_check)

    await message.answer(
        "Як це впливає на ваш день: сон, навчання, роботу або спілкування?",
        reply_markup=dialog_keyboard
    )


@dp.message(SupportDialog.impact_check)
async def impact_check(message: Message, state: FSMContext):
    if await crisis_intercept(message, state):
        return

    data = await state.get_data()
    session_id = data.get("session_id")

    await state.update_data(impact=message.text)

    if session_id:
        await save_message(session_id, "user", message.text, "impact_check")

    await state.set_state(SupportDialog.scale_check)

    await message.answer(
        "Оцініть свій стан зараз від 1 до 10, де 10 — максимально важко.",
        reply_markup=dialog_keyboard
    )


@dp.message(SupportDialog.scale_check)
async def scale_check(message: Message, state: FSMContext):
    if await crisis_intercept(message, state):
        return

    data = await state.get_data()
    session_id = data.get("session_id")

    await state.update_data(scale_score=message.text)

    if session_id:
        await save_message(session_id, "user", message.text, "scale_check")

    await state.set_state(SupportDialog.support_check)

    await message.answer(
        "Чи є зараз поруч людина, якій ви можете написати або подзвонити?",
        reply_markup=dialog_keyboard
    )


@dp.message(SupportDialog.support_check)
async def support_check(message: Message, state: FSMContext):
    if await crisis_intercept(message, state):
        return

    data = await state.get_data()
    session_id = data.get("session_id")

    await state.update_data(support_available=message.text)

    if session_id:
        await save_message(session_id, "user", message.text, "support_check")

    await state.set_state(SupportDialog.coping_check)

    await message.answer(
        "Ви вже пробували щось зробити, щоб трохи покращити свій стан?",
        reply_markup=dialog_keyboard
    )


@dp.message(SupportDialog.coping_check)
async def coping_check(message: Message, state: FSMContext):
    if await crisis_intercept(message, state):
        return

    data = await state.get_data()
    session_id = data.get("session_id")
    branch = data.get("branch", "UNCLEAR")

    coping_type = classify_coping_answer(message.text)

    await state.update_data(
        coping_attempts=message.text,
        coping_type=coping_type
    )

    if session_id:
        await save_message(session_id, "user", message.text, "coping_check")

    if coping_type == "RISKY_ATTEMPT":
        await state.set_state(SupportDialog.safety_check)

        await message.answer(
            "Те, що ви описали, може бути небезпечним способом справлятися зі станом.\n\n"
            "Перед тим як продовжити: чи є зараз думки нашкодити собі?",
            reply_markup=dialog_keyboard
        )
        return

    available_flows = THERAPY_FLOWS.get(
        branch,
        THERAPY_FLOWS["UNCLEAR"]
    )

    selected_flow = random.choice(available_flows)

    await state.update_data(
        current_flow=selected_flow,
        current_step=0
    )

    if session_id:
        await save_message(
            session_id,
            "bot",
            selected_flow["steps"][0],
            "therapy_flow_step_0"
        )

    await state.set_state(SupportDialog.therapy_flow)

    await message.answer(
        selected_flow["steps"][0] + "\n\nНапишіть «Далі», коли будете готові продовжити.",
        reply_markup=dialog_keyboard
    )


@dp.message(SupportDialog.therapy_flow)
async def therapy_flow_step(message: Message, state: FSMContext):
    if await crisis_intercept(message, state):
        return

    data = await state.get_data()
    session_id = data.get("session_id")
    current_flow = data.get("current_flow")
    current_step = data.get("current_step", 0)

    if not current_flow:
        await state.set_state(SupportDialog.safety_check)

        await message.answer(
            "Перед тим як я дам рекомендацію: чи є зараз думки нашкодити собі?",
            reply_markup=dialog_keyboard
        )
        return

    next_step = current_step + 1

    if session_id:
        await save_message(session_id, "user", message.text, "therapy_flow_confirmation")

    if next_step >= len(current_flow["steps"]):
        await state.set_state(SupportDialog.safety_check)

        await message.answer(
            "Добре. Тепер коротко перевіримо безпеку.\n\n"
            "Чи є зараз думки нашкодити собі?",
            reply_markup=dialog_keyboard
        )
        return

    await state.update_data(current_step=next_step)

    step_text = current_flow["steps"][next_step]

    if session_id:
        await save_message(
            session_id,
            "bot",
            step_text,
            f"therapy_flow_step_{next_step}"
        )

    await message.answer(
        step_text + "\n\nНапишіть «Далі», коли будете готові продовжити.",
        reply_markup=dialog_keyboard
    )


@dp.message(SupportDialog.safety_check)
async def safety_check(message: Message, state: FSMContext):
    data = await state.get_data()
    session_id = data.get("session_id")

    safety_answer = message.text

    await state.update_data(safety_answer=safety_answer)

    if session_id:
        await save_message(session_id, "user", safety_answer, "safety_check")

    if is_crisis(safety_answer) or safety_answer.lower() in [
        "так",
        "да",
        "є",
        "есть",
        "іноді",
        "иногда",
        "не знаю"
    ]:
        await state.update_data(risk_level="HIGH")

        if session_id:
            await save_message(session_id, "bot", CRISIS_TEXT, "crisis_mode")
            await update_session_risk(session_id, "HIGH", "crisis")

        await state.set_state(SupportDialog.crisis_mode)

        await message.answer(
            CRISIS_TEXT,
            reply_markup=restart_keyboard
        )

        await state.set_state(SupportDialog.finished)
        return

    data = await state.get_data()
    risk_level = analyze_final_risk(data)
    branch = data.get("branch", "UNCLEAR")

    await state.update_data(risk_level=risk_level)

    recommendation = get_recommendation(risk_level, branch)

    if session_id:
        await save_message(session_id, "bot", recommendation, "recommendation")
        await update_session_risk(session_id, risk_level, "recommendation_given")

    logging.info(f"Final risk level detected: {risk_level}")

    await state.set_state(SupportDialog.feedback)

    await message.answer(
        recommendation + "\n\nЧи стало вам трохи легше?",
        reply_markup=feedback_keyboard
    )


@dp.message(SupportDialog.feedback, F.text == "Стало легше")
async def feedback_better(message: Message, state: FSMContext):
    data = await state.get_data()
    session_id = data.get("session_id")

    await state.set_state(SupportDialog.ready_to_finish)

    text = (
        "Добре. Тоді зараз важливо не перевантажувати себе одразу.\n\n"
        "На найближчі 30 хвилин:\n"
        "1. Не повертайтесь різко до важкої теми.\n"
        "2. Зробіть одну просту дію.\n"
        "3. Залишайтесь у спокійнішому середовищі.\n"
        "4. Якщо можете — напишіть людині, якій довіряєте.\n\n"
        "Можете завершити діалог або отримати ще одну коротку пораду."
    )

    if session_id:
        await save_message(session_id, "user", message.text, "feedback")
        await save_message(session_id, "bot", text, "ready_to_finish")

    await message.answer(
        text,
        reply_markup=finish_or_advice_keyboard
    )


@dp.message(SupportDialog.feedback, F.text == "Не стало легше")
async def feedback_not_better(message: Message, state: FSMContext):
    data = await state.get_data()
    session_id = data.get("session_id")

    followup_text = get_followup_support(data.get("branch", "UNCLEAR"))

    if session_id:
        await save_message(session_id, "user", message.text, "feedback")
        await save_message(session_id, "bot", followup_text, "stabilization_followup")

    await state.set_state(SupportDialog.stabilization_followup)

    await message.answer(
        "Добре, тоді спробуємо інший підхід.\n\n"
        f"{followup_text}\n\n"
        "Після цього натисніть: «Стало легше» або «Не стало легше».",
        reply_markup=feedback_keyboard
    )


@dp.message(SupportDialog.stabilization_followup, F.text == "Стало легше")
async def second_feedback_better(message: Message, state: FSMContext):
    await feedback_better(message, state)


@dp.message(SupportDialog.stabilization_followup, F.text == "Не стало легше")
async def second_feedback_not_better(message: Message, state: FSMContext):
    data = await state.get_data()
    session_id = data.get("session_id")

    text = (
        "Якщо після кількох технік стан не знижується, краще не залишатися з цим наодинці.\n\n"
        "Зараз варто:\n"
        "1. Написати або подзвонити людині, якій довіряєте.\n"
        "2. Зменшити навантаження й не приймати різких рішень.\n"
        "3. Якщо стан посилюється — звернутися до психолога або лікаря.\n\n"
        "Я підсумую діалог нижче."
    )

    summary = build_summary(data)

    if session_id:
        await save_message(session_id, "user", message.text, "second_feedback")
        await save_message(session_id, "bot", text, "specialist_support")
        await save_message(session_id, "bot", summary, "summary")
        await update_session_risk(session_id, data.get("risk_level", "MEDIUM"), "finished")

    await finish_dialog(
        message,
        state,
        text + "\n\n" + summary
    )


@dp.message(SupportDialog.ready_to_finish, F.text == "Ще одна порада")
async def extra_advice(message: Message, state: FSMContext):
    data = await state.get_data()
    session_id = data.get("session_id")

    advice = get_followup_support(data.get("branch", "UNCLEAR"))

    if session_id:
        await save_message(session_id, "user", message.text, "ready_to_finish")
        await save_message(session_id, "bot", advice, "extra_advice")

    await message.answer(
        advice,
        reply_markup=finish_or_advice_keyboard
    )


@dp.message(SupportDialog.ready_to_finish, F.text == "Завершити діалог")
async def finish_after_better(message: Message, state: FSMContext):
    data = await state.get_data()
    summary = build_summary(data)

    session_id = data.get("session_id")

    if session_id:
        await save_message(session_id, "user", message.text, "ready_to_finish")
        await save_message(session_id, "bot", summary, "summary")
        await update_session_risk(session_id, data.get("risk_level", "LOW"), "finished")

    await finish_dialog(message, state, summary)


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
        await message.answer(
            "Продовжіть відповідати на поточне питання або натисніть «Завершити діалог».",
            reply_markup=dialog_keyboard
        )


async def main():
    setup_logger()
    logging.info("Bot started")

    await init_db()
    logging.info("Database initialized")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
