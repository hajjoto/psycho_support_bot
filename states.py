from aiogram.fsm.state import State, StatesGroup


class SupportDialog(StatesGroup):
    consent = State()

    open_problem = State()
    duration_check = State()
    trigger_check = State()
    impact_check = State()
    scale_check = State()
    support_check = State()
    coping_check = State()

    tension_journal = State()
    action_choice = State()

    safety_check = State()
    feedback = State()
    stabilization_followup = State()
    second_feedback = State()
    additional_support = State()
    ready_to_finish = State()

    crisis_mode = State()
    finished = State()
