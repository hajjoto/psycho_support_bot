from aiogram.fsm.state import State, StatesGroup


class SupportDialog(StatesGroup):
    consent = State()
    collecting_problem = State()
    crisis_mode = State()
    recommendations = State()
    finished = State()