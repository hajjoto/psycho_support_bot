HIGH_RISK_WORDS = [
    "хочу умереть",
    "хочу померти",
    "не хочу жить",
    "не хочу жити",
    "суицид",
    "самогубство",
    "убить себя",
    "вбити себе",
    "покончить с собой",
    "накласти на себе руки",
    "самоповреждение",
    "самоушкодження",
    "порезать себя",
    "порізати себе",
    "есть план",
    "є план",
    "прощаюсь",
    "прощавай"
]


MEDIUM_RISK_WORDS = [
    "паніка",
    "паника",
    "панічна атака",
    "паническая атака",
    "не можу дихати",
    "не могу дышать",
    "не справляюся",
    "не справляюсь",
    "дуже погано",
    "очень плохо",
    "безсоння",
    "бессонница",
    "сильно тривожно",
    "сильная тревога"
]


def normalize_text(text: str) -> str:
    return text.lower().strip()


def contains_any(text: str, words: list[str]) -> bool:
    normalized = normalize_text(text)
    return any(word in normalized for word in words)


def is_crisis(text: str) -> bool:
    if not text:
        return False

    return contains_any(text, HIGH_RISK_WORDS)


def parse_scale_score(value: str) -> int:
    value = str(value).strip()

    if value in ["1-5", "1–5"]:
        return 5

    if value in ["6-8", "6–8"]:
        return 8

    if value in ["9-10", "9–10"]:
        return 10

    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def analyze_final_risk(session_data: dict) -> str:
    combined_text = " ".join(
        str(value).lower()
        for value in session_data.values()
        if value
    )

    if is_crisis(combined_text):
        return "HIGH"

    scale = parse_scale_score(session_data.get("scale_score", ""))

    if scale >= 9:
        return "HIGH"

    if scale >= 6:
        return "MEDIUM"

    if contains_any(combined_text, MEDIUM_RISK_WORDS):
        return "MEDIUM"

    return "LOW"


def classify_branch(text: str) -> str:
    return "UNCLEAR"


def classify_coping_answer(text: str) -> str:
    if not text:
        return "GENERAL"

    text = normalize_text(text)

    if contains_any(text, HIGH_RISK_WORDS):
        return "RISKY_ATTEMPT"

    return "GENERAL"
