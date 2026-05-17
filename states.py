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
    safety_check = State()

    panic_branch = State()
    depression_branch = State()
    stress_branch = State()
    relationship_branch = State()
    loneliness_branch = State()
    study_work_branch = State()
    unclear_branch = State()

    technique = State()
    feedback = State()
    additional_support = State()
    summary = State()

    crisis_mode = State()
    finished = State()
