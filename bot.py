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
        "Ми поставимо кілька коротких запитань, щоб краще зрозуміти "
        "ваш стан і підібрати підтримку, яка може бути корисною саме зараз.\n\n"
        "Бот не замінює психолога або лікаря. "
        "У кризових ситуаціях необхідно звернутися до екстрених служб.\n\n"
        "Щоб почати, натисніть «Почати».",
        reply_markup=start_keyboard
    )


@dp.message(SupportDialog.start_time_choice, F.text == "Так")
async def start_time_yes(message: Message, state: FSMContext):
    data = await state.get_data()
    session_id = data.get("session_id")

    if session_id:
        await save_message(session_id, "user", message.text, "start_time_choice")

    await state.set_state(SupportDialog.scale_check)

    await message.answer(
        "Оцініть свій рівень напруги від 1 до 10.\n\n"
        "1–5 - неприємно, але я можу справлятися.\n\n"
        "6–8 - сильно переживаю, складно займатися справами.\n\n"
        "9–10 - майже не контролюю емоції, дуже важко.",
        reply_markup=scale_keyboard
    )


@dp.message(SupportDialog.start_time_choice, F.text == "Ні, потрібно швидше")
async def start_time_no(message: Message, state: FSMContext):
    data = await state.get_data()
    session_id = data.get("session_id")

    if session_id:
        await save_message(session_id, "user", message.text, "start_time_choice")

    await message.answer(
        "Можемо запропонувати протокол термінової самодопомоги: він займає приблизно 1 хвилину.\n\n"
        "Якщо у вас є трохи більше часу — оберіть повний варіант. Він займає близько 3 хвилин і працює глибше.",
        reply_markup=urgent_protocol_keyboard
    )

    await state.set_state(SupportDialog.protocol_choice)

@dp.message(SupportDialog.consent)
async def process_consent(message: Message, state: FSMContext):
    if message.text.strip() != "Почати":
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
        "Що зараз дається вам найважче?",
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
        "Оцініть свій рівень напруги від 1 до 10.\n\n"
        "1–5 - неприємно, але я можу справлятися.\n\n"
        "6–8 - сильно переживаю, складно займатися справами.\n\n"
        "9–10 - майже не контролюю емоції, дуже важко.",
        reply_markup=scale_keyboard
    )


@dp.message(SupportDialog.scale_check)
async def scale_check(message: Message, state: FSMContext):
    if await crisis_intercept(message, state):
        return

    data = await state.get_data()
    session_id = data.get("session_id")

    await state.update_data(
        scale_score=message.text
    )

    if session_id:
        await save_message(
            session_id,
            "user",
            message.text,
            "scale_check"
        )

    risk_level = analyze_final_risk({
        **data,
        "scale_score": message.text
    })

    await state.update_data(
        risk_level=risk_level
    )

    state_text = get_state_text_by_risk(risk_level)

    await state.set_state(SupportDialog.scenario_choice)

    await message.answer(
        state_text + "\n\n"
        "Що хочете зробити далі?",
        reply_markup=scenario_choice_keyboard
    )

@dp.message(SupportDialog.scenario_choice, F.text == "Зрозуміти свій стан")
async def explain_state(message: Message, state: FSMContext):
    data = await state.get_data()
    risk_level = data.get("risk_level", "LOW")

    await state.set_state(SupportDialog.scenario_choice)

    await message.answer(
        get_state_text_by_risk(risk_level),
        reply_markup=scenario_choice_keyboard
    )


@dp.message(SupportDialog.scenario_choice, F.text == "Поради на день")
async def daily_advice(message: Message, state: FSMContext):
    data = await state.get_data()
    risk_level = data.get("risk_level", "LOW")

    await message.answer(
        get_daily_advice_by_risk(risk_level),
        reply_markup=scenario_choice_keyboard
    )


@dp.message(SupportDialog.scenario_choice, F.text == "Перейти до вправ")
async def go_to_protocols(message: Message, state: FSMContext):
    data = await state.get_data()
    session_id = data.get("session_id")

    if session_id:
        await save_message(session_id, "user", message.text, "scenario_choice")

    await state.set_state(SupportDialog.protocol_choice)

    await message.answer(
        "Оберіть формат вправи:",
        reply_markup=protocol_choice_keyboard
    )


@dp.message(SupportDialog.scenario_choice)
async def scenario_choice_wrong(message: Message):
    await message.answer(
        "Оберіть один із варіантів нижче.",
        reply_markup=scenario_choice_keyboard
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
        reply_markup=yes_no_keyboard
    )


@dp.message(SupportDialog.coping_check)
async def coping_check(message: Message, state: FSMContext):
    if await crisis_intercept(message, state):
        return

    data = await state.get_data()
    session_id = data.get("session_id")

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
            reply_markup=yes_no_keyboard
        )
        return

    await state.set_state(SupportDialog.protocol_choice)

    await message.answer(
        "Зараз краще перейти до короткої стабілізації.\n\n"
        "Оберіть формат вправи:",
        reply_markup=protocol_choice_keyboard
    )


@dp.message(SupportDialog.protocol_choice, F.text.in_(["Терміновий протокол", "Повний варіант", "Короткий варіант"]))
async def protocol_choice(message: Message, state: FSMContext):
    data = await state.get_data()
    session_id = data.get("session_id")
    branch = data.get("branch", "UNCLEAR")

    mode = "FULL" if message.text == "Повний варіант" else "SHORT"

    protocols = get_protocols(branch, mode)
    selected_protocol = random.choice(protocols)

    await state.update_data(
        protocol_mode=mode,
        current_protocol=selected_protocol,
        protocol_step=0,
        protocol_attempts=data.get("protocol_attempts", 0) + 1
    )

    if session_id:
        await save_message(session_id, "user", message.text, "protocol_choice")
        await save_message(session_id, "bot", selected_protocol["steps"][0], "protocol_step_0")

    await state.set_state(SupportDialog.protocol_running)

    await message.answer(
        selected_protocol["steps"][0],
        reply_markup=protocol_next_keyboard
    )


@dp.message(SupportDialog.protocol_choice)
async def protocol_choice_wrong(message: Message):
    await message.answer(
        "Оберіть один із варіантів нижче.",
        reply_markup=protocol_choice_keyboard
    )


@dp.message(SupportDialog.protocol_running, F.text == "Далі")
async def protocol_running(message: Message, state: FSMContext):
    if await crisis_intercept(message, state):
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
        await save_message(
            session_id,
            "bot",
            step_text,
            f"protocol_step_{next_step}"
        )

    await message.answer(
        step_text,
        reply_markup=protocol_next_keyboard
    )


@dp.message(SupportDialog.protocol_running)
async def protocol_running_wrong_input(message: Message):
    await message.answer(
        "Натисніть «Далі», щоб продовжити вправу.",
        reply_markup=protocol_next_keyboard
    )

@dp.message(SupportDialog.protocol_feedback, F.text == "Стало легше")
async def protocol_feedback_better(message: Message, state: FSMContext):
    data = await state.get_data()
    session_id = data.get("session_id")

    risk_level = analyze_final_risk(data)
    branch = data.get("branch", "UNCLEAR")
    recommendation = get_recommendation(risk_level, branch)

    await state.update_data(risk_level=risk_level)

    if session_id:
        await save_message(session_id, "user", message.text, "protocol_feedback")
        await save_message(session_id, "bot", recommendation, "recommendation")
        await update_session_risk(session_id, risk_level, "recommendation_given")

    await state.set_state(SupportDialog.ready_to_finish)

    await message.answer(
        recommendation + "\n\nМожете завершити діалог або отримати ще одну коротку пораду.",
        reply_markup=finish_or_advice_keyboard
    )

@dp.message(SupportDialog.protocol_feedback, F.text == "Повторити вправу")
async def protocol_repeat(message: Message, state: FSMContext):
    data = await state.get_data()

    session_id = data.get("session_id")
    branch = data.get("branch", "UNCLEAR")
    mode = data.get("protocol_mode", "SHORT")
    current_protocol = data.get("current_protocol")
    used_protocol_ids = data.get("used_protocol_ids", [])

    if current_protocol:
        used_protocol_ids.append(current_protocol.get("id"))

    protocols = get_protocols(branch, mode)

    available_protocols = [
        protocol for protocol in protocols
        if protocol.get("id") not in used_protocol_ids
    ]

    if not available_protocols:
        available_protocols = protocols
        used_protocol_ids = []

    selected_protocol = random.choice(available_protocols)

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

@dp.message(SupportDialog.protocol_feedback, F.text == "Стало легше")
async def protocol_feedback_better_action(message: Message, state: FSMContext):
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
        "4. Якщо можете - дайте собі трохи тиші.\n\n"
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


@dp.message(SupportDialog.protocol_feedback)
async def protocol_feedback_wrong(message: Message):
    await message.answer(
        "Оберіть один із варіантів нижче.",
        reply_markup=protocol_feedback_keyboard
    )


@dp.message(SupportDialog.ready_to_finish, F.text == "Ще одна порада")
async def extra_advice(message: Message, state: FSMContext):
    data = await state.get_data()
    session_id = data.get("session_id")

    used_types = data.get("used_support_types", [])

    advice, advice_type = get_followup_support(
        data.get("branch", "UNCLEAR"),
        used_types
    )

    used_types.append(advice_type)

    await state.update_data(
        used_support_types=used_types
    )

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


@dp.message(SupportDialog.ready_to_finish)
async def ready_to_finish_wrong(message: Message):
    await message.answer(
        "Оберіть: завершити діалог або отримати ще одну пораду.",
        reply_markup=finish_or_advice_keyboard
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

    await state.set_state(SupportDialog.protocol_choice)

    await message.answer(
        "Добре. Тоді перейдемо до стабілізаційної вправи.\n\n"
        "Оберіть формат:",
        reply_markup=protocol_choice_keyboard
    )


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
