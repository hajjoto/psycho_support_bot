from support_strategies import (
    get_low_support,
    get_medium_support,
    get_additional_support,
)


CRISIS_TEXT = (
    "Мені дуже шкода, що вам зараз настільки важко.\n\n"
    "Я не можу допомагати з діями, які можуть нашкодити вам.\n\n"
    "Зараз важливо не залишатися наодинці. "
    "Зверніться до людини поруч або до екстрених служб.\n\n"
    "Україна:\n"
    "Екстрена допомога: 112 або 103\n"
    "Lifeline Ukraine: 7333\n\n"
    "Якщо є негайна небезпека - телефонуйте 112 прямо зараз."
)


def get_branch_intro(branch: str) -> str:
    texts = {
        "PANIC": "Схоже, зараз у вас сильна тривога або панічний стан.",
        "DEPRESSION": "Схоже, вам емоційно важко і бракує сил.",
        "STRESS": "Схоже, ви перевантажені.",
        "RELATIONSHIP": "Схоже, ситуація повʼязана з відносинами або конфліктом.",
        "LONELINESS": "Схоже, вам зараз самотньо або бракує підтримки.",
        "STUDY_WORK": "Схоже, вас тисне навчання, робота або дедлайн.",
        "UNCLEAR": "Питання для уточнення ситуації."
    }

    return texts.get(branch, texts["UNCLEAR"])


def get_recommendation(risk_level: str, branch: str) -> str:
    if risk_level == "HIGH":
        return CRISIS_TEXT

    if risk_level == "MEDIUM":
        return get_medium_support()

    if branch:
        return get_additional_support(branch)

    return get_low_support()


def build_summary(data: dict) -> str:
    branch = data.get("branch", "UNCLEAR")

    branch_names = {
        "PANIC": "тривога або панічний стан",
        "DEPRESSION": "емоційне виснаження",
        "STRESS": "стрес і перевантаження",
        "RELATIONSHIP": "ситуація у відносинах",
        "LONELINESS": "самотність або нестача підтримки",
        "STUDY_WORK": "навчальне чи робоче навантаження",
        "UNCLEAR": "емоційне напруження"
    }

    readable_branch = branch_names.get(branch, "емоційне напруження")

    return (
        "Дякую, що пройшли діалог.\n\n"
        f"Схоже, зараз основна складність пов’язана з: {readable_branch}.\n\n"
        "На найближчий час краще обрати не багато дій, а одну просту й реальну:\n"
        "- зробити коротку паузу\n"
        "- зменшити навантаження\n"
        "- повернутися до того, що ви можете контролювати\n"
        "- звернутися до людини, якій довіряєте\n\n"
        "Якщо стан посилюється, триває довго або заважає нормально жити - "
        "варто звернутися до психолога або лікаря."
    )


def get_followup_support(branch: str) -> str:
    return get_additional_support(branch)
