CRISIS_WORDS = [
    "хочу умереть",
    "хочу померти",
    "суицид",
    "самогубство",
    "убить себя",
    "вбити себе",
]

HIGH_RISK_WORDS = [
    "хочу умереть", "хочу померти",
    "не хочу жить", "не хочу жити",
    "суицид", "самогубство",
    "убить себя", "вбити себе",
    "покончить с собой", "накласти на себе руки",
    "самоповреждение", "самоушкодження",
    "есть план", "є план",
    "прощаюсь", "прощавай"
]

PANIC_WORDS = [
    "паника", "паніка",
    "паническая атака", "панічна атака",
    "не могу дышать", "не можу дихати",
    "сердце бьется", "серце бʼється",
    "страшно", "накрывает", "накриває"
]

DEPRESSION_WORDS = [
    "нет сил", "немає сил",
    "ничего не хочу", "нічого не хочу",
    "апатия", "апатія",
    "пустота", "порожнеча",
    "не вижу смысла", "не бачу сенсу",
    "лежу весь день"
]

STRESS_WORDS = [
    "стресс", "стрес",
    "перегруз", "перевантаження",
    "дедлайн", "не успеваю", "не встигаю",
    "все навалилось", "все навалилося"
]

RELATIONSHIP_WORDS = [
    "отношения", "відносини",
    "девушка", "дівчина",
    "парень", "хлопець",
    "ссора", "сварка",
    "расставание", "розставання",
    "игнор", "конфликт", "конфлікт"
]

LONELINESS_WORDS = [
    "одиноко", "самотньо",
    "одиночество", "самотність",
    "никому не нужен", "нікому не потрібен",
    "нет друзей", "немає друзів",
    "не с кем поговорить", "немає з ким поговорити"
]

STUDY_WORK_WORDS = [
    "учеба", "навчання",
    "работа", "робота",
    "диплом", "экзамен", "іспит",
    "прокрастинация", "прокрастинація",
    "задача", "проект", "проєкт"
]


def contains_any(text: str, words: list[str]) -> bool:
    text = text.lower()
    return any(word in text for word in words)


def is_crisis(text: str) -> bool:
    return contains_any(text, HIGH_RISK_WORDS)


def classify_branch(text: str) -> str:
    text = text.lower()

    if contains_any(text, PANIC_WORDS):
        return "PANIC"

    if contains_any(text, DEPRESSION_WORDS):
        return "DEPRESSION"

    if contains_any(text, STRESS_WORDS):
        return "STRESS"

    if contains_any(text, RELATIONSHIP_WORDS):
        return "RELATIONSHIP"

    if contains_any(text, LONELINESS_WORDS):
        return "LONELINESS"

    if contains_any(text, STUDY_WORK_WORDS):
        return "STUDY_WORK"

    return "UNCLEAR"


def analyze_final_risk(session_data: dict) -> str:
    combined_text = " ".join(
        str(value).lower()
        for value in session_data.values()
        if value
    )

    if is_crisis(combined_text):
        return "HIGH"

    scale = session_data.get("scale_score")

    try:
        scale = int(scale)
    except (TypeError, ValueError):
        scale = 0

    medium_markers = [
        "паника", "паніка",
        "не справляюсь", "не справляюся",
        "бессонница", "безсоння",
        "дуже погано", "очень плохо",
        "нет поддержки", "немає підтримки"
    ]

    if scale >= 7 or contains_any(combined_text, medium_markers):
        return "MEDIUM"

    return "LOW"

def classify_coping_answer(text: str) -> str:
    text = text.lower()

    if any(word in text for word in ["нічого", "ничего", "не пробував", "не пробовал"]):
        return "NOTHING"

    if any(word in text for word in ["не допомогло", "не помогло", "гірше", "хуже"]):
        return "DID_NOT_HELP"

    if any(word in text for word in ["дихання", "дышал", "прогулян", "сон", "музик", "говорив", "говорил"]):
        return "HEALTHY_ATTEMPT"

    if any(word in text for word in ["алкоголь", "таблет", "поріз", "резал", "самоповреж", "самоушкод"]):
        return "RISKY_ATTEMPT"

    if any(word in text for word in ["не знаю", "не знаю що", "не уверен", "не впевнений"]):
        return "UNKNOWN"

    return "GENERAL"
