import random

from support_strategies import LOW_SUPPORT, MEDIUM_SUPPORT


CRISIS_TEXT = (
    "Мені дуже шкода, що вам зараз настільки важко.\n\n"
    "Я не можу допомагати з діями, які можуть нашкодити вам.\n\n"
    "Зараз важливо не залишатися наодинці. "
    "Зверніться до людини поруч або до екстрених служб.\n\n"
    "Україна:\n"
    "Екстрена допомога: 112 або 103\n"
    "Lifeline Ukraine: 7333\n\n"
    "Якщо є негайна небезпека — телефонуйте 112 прямо зараз."
)


ADDITIONAL_SUPPORT_TEXT = (
    "Спробуйте ще одну коротку техніку.\n\n"
    "Поставте ноги на підлогу.\n"
    "Повільно вдихніть на 4 секунди.\n"
    "Видихніть на 6 секунд.\n"
    "Повторіть 5 разів.\n\n"
    "Після цього зробіть одну просту дію: випийте води, відкрийте вікно або відійдіть від екрана."
)


def get_branch_intro(branch: str) -> str:
    texts = {
        "PANIC": "Схоже, зараз у вас сильна тривога або панічний стан.",
        "DEPRESSION": "Схоже, вам емоційно важко і бракує сил.",
        "STRESS": "Схоже, ви перевантажені.",
        "RELATIONSHIP": "Схоже, ситуація повʼязана з відносинами або конфліктом.",
        "LONELINESS": "Схоже, вам зараз самотньо або бракує підтримки.",
        "STUDY_WORK": "Схоже, вас тисне навчання, робота або дедлайн.",
        "UNCLEAR": "Я поки не до кінця зрозумів ситуацію, тому поставлю кілька уточнень."
    }

    return texts.get(branch, texts["UNCLEAR"])


def get_recommendation(risk_level: str, branch: str) -> str:
    if risk_level == "HIGH":
        return CRISIS_TEXT

    if risk_level == "MEDIUM":
        strategy = random.choice(MEDIUM_SUPPORT)
        return strategy["text"]

    strategy = random.choice(LOW_SUPPORT)
    return strategy["text"]


def build_summary(data: dict) -> str:
    branch = data.get("branch", "UNCLEAR")
    risk_level = data.get("risk_level", "LOW")

    recommendation = get_recommendation(risk_level, branch)

    branch_names = {
        "PANIC": "тривога та емоційне перенавантаження",
        "DEPRESSION": "емоційне виснаження",
        "STRESS": "стрес та перевантаження",
        "RELATIONSHIP": "ситуація у відносинах",
        "LONELINESS": "самотність та нестача підтримки",
        "STUDY_WORK": "навчання або робоче навантаження",
        "UNCLEAR": "емоційне напруження"
    }

    readable_branch = branch_names.get(branch, "емоційне напруження")

    return (
        "Дякую, що пройшли діалог.\n\n"
        f"Схоже, зараз основна складність пов’язана з: {readable_branch}.\n\n"
        f"{recommendation}\n\n"
        "Якщо стан посилюється, триває довго або заважає нормально жити — "
        "варто звернутися до психолога або лікаря."
    )
