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
    "самоушкодження"
]


MEDIUM_RISK_WORDS = [
    "паника",
    "паніка",
    "паническая атака",
    "панічна атака",
    "сильная тревога",
    "сильна тривога",
    "бессонница",
    "безсоння",
    "не справляюсь",
    "не справляюся",
    "очень плохо",
    "дуже погано"
]


LOW_RISK_WORDS = [
    "стресс",
    "стрес",
    "усталость",
    "втома",
    "одиночество",
    "самотність",
    "отношения",
    "відносини",
    "тревога",
    "тривога",
    "грусть",
    "сум"
]


def analyze_risk(text: str) -> str:
    text = text.lower()

    if any(word in text for word in HIGH_RISK_WORDS):
        return "HIGH"

    if any(word in text for word in MEDIUM_RISK_WORDS):
        return "MEDIUM"

    if any(word in text for word in LOW_RISK_WORDS):
        return "LOW"

    return "LOW"