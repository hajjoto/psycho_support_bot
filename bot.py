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
from risk_analyzer import is_crisis, analyze_final_risk
from recommendations import CRISIS_TEXT, get_followup_support, build_summary
from session_service import create_session_id
from keyboards import (
    start_time_keyboard,
    urgent_protocol_keyboard,
    start_keyboard,
    dialog_keyboard,
    restart_keyboard,
    finish_or_advice_keyboard,
    scale_keyboard,
    yes_no_keyboard,
    protocol_choice_keyboard,
    protocol_next_keyboard,
    protocol_feedback_keyboard,
    scenario_choice_keyboard
)
from database import init_db, create_session, save_message, update_session_risk
from protocols import get_protocols
from scenario_texts import get_state_text_by_risk, get_daily_advice_by_risk
from buttons import (
    clean_button,
    BTN_START,
    BTN_RESTART,
    BTN_YES,
    BTN_NO_FAST,
    BTN_NEXT,
    BTN_BETTER,
    BTN_NOT_BETTER,
    BTN_REPEAT,
    BTN_ADVICE,
    BTN_NEW_EXERCISE,
    BTN_FINISH,
    BTN_SHORT,
    BTN_FULL,
    BTN_UNDERSTAND,
    BTN_EXERCISES,
    BTN_DAILY_ADVICE
)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


def button_text(message: Message) -> str:
    return clean_button(message.text or "")


def normalize_scale(text: str) -> str:
    text = text or ""

    if "9" in text and "10" in text:
        return "9-10"

    if "6" in text and "8" in text:
        return "6-8"

    if "1" in text and "5" in text:
        return "1-5"

    return text.strip()


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
        "Я допоможу коротко оцінити ваш стан і запропоную вправу або поради, "
        "які можуть бути корисними саме зараз.\n\n"
        "Бот не замінює психолога або лікаря. "
        "Якщо є загроза життю чи здоровʼю — зверніться до екстрених служб.\n\n"
        "Щоб почати, натисніть «Почати».",
        reply_markup=start_keyboard
    )


@dp.message(SupportDialog.consent)
async def process_consent(message: Message, state: FSMContext):
    if button_text(message) != BTN_START:
        await message.answer(
            "Щоб почати діалог, натисніть кнопку «Почати».",
            reply_markup=start_keyboard
        )
        return

    session_id = create_session_id()
    await create_session(session_id)

    await state.update_data(
        session_id=session_id,
        branch="UNCLEAR"
    )

    await state.set_state(SupportDialog.start_time_choice)

    logging.info(f"New anonymous session created: {session_id}")

    await message.answer(
        "Чи можете ви приділити собі приблизно 3 хвилини?",
        reply_markup=start_time_keyboard
    )


@dp.message(SupportDialog.start_time_choice)
async def start_time_choice(message: Message, state: FSMContext):
    selected = button_text(message)

    data = await state.get_data()
    session_id = data.get("session_id")

    if session_id:
        await save_message(session_id, "user", message.text, "start_time_choice")

    if selected == BTN_YES or "Так" in (message.text or ""):
        await state.set_state(SupportDialog.scale_check)

        await message.answer(
            "Оцініть рівень напруги зараз.\n\n"
            "1–5 — неприємно, але ви ще можете справлятися.\n\n"
            "6–8 — напруга сильна, складно займатися справами.\n\n"
            "9–10 — дуже важко, контроль майже втрачається.",
            reply_markup=scale_keyboard
        )
        return

    if selected == BTN_NO_FAST or "швидше" in (message.text or ""):
        await message.answer(
            "Можемо почати з короткої самодопомоги. Вона займає близько 1 хвилини.\n\n"
            "Якщо маєте трохи більше часу — оберіть повний варіант. "
            "Він займає близько 3 хвилин і працює глибше.",
            reply_markup=urgent_protocol_keyboard
        )

        await state.set_state(SupportDialog.protocol_choice)
        return

    await message.answer(
        "Оберіть один із варіантів нижче.",
        reply_markup=start_time_keyboard
    )


@dp.message(F.text.endswith(BTN_FINISH))
async def manual_finish(message: Message, state: FSMContext):
    await finish_dialog(
        message,
        state,
        "Діалог завершено. Ви можете почати нову сесію будь-коли."
    )


@dp.message(SupportDialog.scale_check)
async def scale_check(message: Message, state: FSMContext):
    if await crisis_intercept(message, state):
        return

    scale_score = normalize_scale(message.text)

    if scale_score not in ["1-5", "6-8", "9-10"]:
        await message.answer(
            "Оберіть рівень напруги кнопкою нижче.",
            reply_markup=scale_keyboard
        )
        return

    data = await state.get_data()
    session_id = data.get("session_id")

    await state.update_data(scale_score=scale_score)

    if session_id:
        await save_message(session_id, "user", message.text, "scale_check")

    risk_level = analyze_final_risk({
        **data,
        "scale_score": scale_score
    })

    await state.update_data(risk_level=risk_level)

    state_text = get_state_text_by_risk(risk_level)

    await state.set_state(SupportDialog.scenario_choice)

    await message.answer(
        state_text + "\n\nЩо хочете зробити далі?",
        reply_markup=scenario_choice_keyboard
    )


@dp.message(SupportDialog.scenario_choice)
async def scenario_choice(message: Message, state: FSMContext):
    selected = button_text(message)

    data = await state.get_data()
    session_id = data.get("session_id")
    risk_level = data.get("risk_level", "LOW")

    if selected == BTN_UNDERSTAND:
        await message.answer(
            get_state_text_by_risk(risk_level),
            reply_markup=scenario_choice_keyboard
        )
        return

    if selected == BTN_DAILY_ADVICE:
        await message.answer(
            get_daily_advice_by_risk(risk_level),
            reply_markup=scenario_choice_keyboard
        )
        return

    if selected == BTN_EXERCISES:
        if session_id:
            await save_message(session_id, "user", message.text, "scenario_choice")

        await state.set_state(SupportDialog.protocol_choice)

        await message.answer(
            "Оберіть формат вправи:",
            reply_markup=protocol_choice_keyboard
        )
        return

    await message.answer(
        "Оберіть один із варіантів нижче.",
        reply_markup=scenario_choice_keyboard
    )


@dp.message(SupportDialog.protocol_choice)
async def protocol_choice(message: Message, state: FSMContext):
    selected = button_text(message)

    if selected not in [BTN_SHORT, BTN_FULL, "Терміновий протокол", "Повний варіант", "Короткий варіант"]:
        await message.answer(
            "Оберіть формат вправи:",
            reply_markup=protocol_choice_keyboard
        )
        return

    data = await state.get_data()
    session_id = data.get("session_id")
    branch = data.get("branch", "UNCLEAR")

    mode = "FULL" if selected in [BTN_FULL, "Повний варіант"] else "SHORT"

    protocols = get_protocols(branch, mode)
    selected_protocol = random.choice(protocols)

    await state.update_data(
        protocol_mode=mode,
        current_protocol=selected_protocol,
        protocol_step=0,
        protocol_attempts=data.get("protocol_attempts", 0) + 1,
        used_protocol_ids=[selected_protocol.get("id")]
    )

    if session_id:
        await save_message(session_id, "user", message.text, "protocol_choice")
        await save_message(session_id, "bot", selected_protocol["steps"][0], "protocol_step_0")

    await state.set_state(SupportDialog.protocol_running)

    await message.answer(
        selected_protocol["steps"][0],
        reply_markup=protocol_next_keyboard
    )


@dp.message(SupportDialog.protocol_running)
async def protocol_running(message: Message, state: FSMContext):
    if await crisis_intercept(message, state):
        return

    selected = button_text(message)

    if selected != BTN_NEXT:
        await message.answer(
            "Натисніть «Далі», щоб продовжити вправу.",
            reply_markup=protocol_next_keyboard
        )
        return

    data = await state.get_data()
    session_id = data.get("session_id")
    protocol = data.get("current_protocol")
    step = data.get("protocol_step", 0)

    if not protocol:
        await state.set_state(SupportDialog.protocol_choice)

        await message.answer(
            "Оберіть формат вправи:",
            reply_markup=protocol_choice_keyboard
        )
        return

    next_step = step + 1

    if session_id:
        await save_message(session_id, "user", message.text, "protocol_next")

    if next_step >= len(protocol["steps"]):
        await state.set_state(SupportDialog.protocol_feedback)

        await message.answer(
            "Чи стало вам трохи легше після цієї вправи?",
            reply_markup=protocol_feedback_keyboard
        )
        return

    await state.update_data(protocol_step=next_step)

    step_text = protocol["steps"][next_step]

    if session_id:
        await save_message(session_id, "bot", step_text, f"protocol_step_{next_step}")

    await message.answer(
        step_text,
        reply_markup=protocol_next_keyboard
    )


@dp.message(SupportDialog.protocol_feedback)
async def protocol_feedback(message: Message, state: FSMContext):
    selected = button_text(message)

    if selected == BTN_BETTER:
        data = await state.get_data()
        session_id = data.get("session_id")

        risk_level = analyze_final_risk(data)

        await state.update_data(risk_level=risk_level)

        answer_text = (
            "Добре. Зараз важливо не перевантажувати себе одразу.\n\n"
            "На найближчі 30 хвилин:\n"
            "1. Залишайтесь у спокійнішому середовищі.\n"
            "2. Не відкривайте новини або соцмережі.\n"
            "3. Зробіть ще кілька повільних видихів.\n"
            "4. Якщо можете — дайте собі трохи тиші.\n\n"
            "Можете завершити діалог або отримати ще одну коротку пораду."
        )

        if session_id:
            await save_message(session_id, "user", message.text, "protocol_feedback")
            await save_message(session_id, "bot", answer_text, "ready_to_finish")
            await update_session_risk(session_id, risk_level, "stabilized")

        await state.set_state(SupportDialog.ready_to_finish)

        await message.answer(
            answer_text,
            reply_markup=finish_or_advice_keyboard
        )
        return

    if selected == BTN_REPEAT or selected == "Повторити вправу":
        data = await state.get_data()

        session_id = data.get("session_id")
        branch = data.get("branch", "UNCLEAR")
        mode = data.get("protocol_mode", "SHORT")
        used_protocol_ids = data.get("used_protocol_ids", [])

        protocols = get_protocols(branch, mode)

        available_protocols = [
            protocol for protocol in protocols
            if protocol.get("id") not in used_protocol_ids
        ]

        if not available_protocols:
            available_protocols = protocols
            used_protocol_ids = []

        selected_protocol = random.choice(available_protocols)
        used_protocol_ids.append(selected_protocol.get("id"))

        await state.update_data(
            current_protocol=selected_protocol,
            protocol_step=0,
            used_protocol_ids=used_protocol_ids,
            protocol_attempts=data.get("protocol_attempts", 0) + 1
        )

        if session_id:
            await save_message(session_id, "user", message.text, "protocol_repeat")
            await save_message(session_id, "bot", selected_protocol["steps"][0], "protocol_step_0_repeat")

        await state.set_state(SupportDialog.protocol_running)

        await message.answer(
            selected_protocol["steps"][0],
            reply_markup=protocol_next_keyboard
        )
        return

    if selected == BTN_NOT_BETTER:
        data = await state.get_data()
        attempts = data.get("protocol_attempts", 1)

        if attempts >= 2:
            text = (
                "Якщо після кількох вправ напруга не знижується, краще не залишатися з цим наодинці.\n\n"
                "Зараз важливо перейти до безпечного режиму:\n"
                "1. Залишайтесь у місці, де вам фізично безпечно.\n"
                "2. Не приймайте різких рішень у піку емоцій.\n"
                "3. Напишіть або подзвоніть людині, якій довіряєте.\n"
                "4. Якщо з’являються думки нашкодити собі — зверніться до екстреної допомоги."
            )

            await finish_dialog(message, state, text)
            return

        await state.set_state(SupportDialog.protocol_choice)

        await message.answer(
            "Добре. Тоді спробуємо інший підхід.\n\n"
            "Оберіть формат наступної вправи:",
            reply_markup=protocol_choice_keyboard
        )
        return

    await message.answer(
        "Оберіть один із варіантів нижче.",
        reply_markup=protocol_feedback_keyboard
    )


@dp.message(SupportDialog.ready_to_finish)
async def ready_to_finish(message: Message, state: FSMContext):
    selected = button_text(message)

    if selected == BTN_ADVICE:
        data = await state.get_data()
        session_id = data.get("session_id")

        used_types = data.get("used_support_types", [])

        advice, advice_type = get_followup_support(
            data.get("branch", "UNCLEAR"),
            used_types
        )

        used_types.append(advice_type)

        await state.update_data(used_support_types=used_types)

        if session_id:
            await save_message(session_id, "user", message.text, "ready_to_finish")
            await save_message(session_id, "bot", advice, "extra_advice")

        await message.answer(
            advice,
            reply_markup=finish_or_advice_keyboard
        )
        return

    if selected == BTN_NEW_EXERCISE:
        await state.set_state(SupportDialog.protocol_choice)

        await message.answer(
            "Оберіть формат вправи:",
            reply_markup=protocol_choice_keyboard
        )
        return

    if selected == BTN_FINISH:
        data = await state.get_data()
        summary = build_summary(data)
        session_id = data.get("session_id")

        if session_id:
            await save_message(session_id, "user", message.text, "ready_to_finish")
            await save_message(session_id, "bot", summary, "summary")
            await update_session_risk(session_id, data.get("risk_level", "LOW"), "finished")

        await finish_dialog(message, state, summary)
        return

    await message.answer(
        "Оберіть: завершити діалог, нову вправу або ще одну пораду.",
        reply_markup=finish_or_advice_keyboard
    )


@dp.message(SupportDialog.safety_check)
async def safety_check(message: Message, state: FSMContext):
    data = await state.get_data()
    session_id = data.get("session_id")

    safety_answer = button_text(message)

    await state.update_data(safety_answer=safety_answer)

    if session_id:
        await save_message(session_id, "user", message.text, "safety_check")

    if is_crisis(message.text or "") or safety_answer in [BTN_YES, "Так", "Не знаю"]:
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

    await state.set_state(SupportDialog.protocol_choice)

    await message.answer(
        "Добре. Тоді перейдемо до стабілізаційної вправи.\n\n"
        "Оберіть формат:",
        reply_markup=protocol_choice_keyboard
    )


@dp.message(SupportDialog.finished)
async def finished_message(message: Message, state: FSMContext):
    if button_text(message) == BTN_RESTART:
        await start(message, state)
        return

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
