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

    readable_branch = branch_names.get(
        branch,
        "емоційне напруження"
    )

    return (
        "Дякую, що пройшли діалог.\n\n"
        f"Схоже, зараз основна складність пов’язана з: {readable_branch}.\n\n"
        f"{recommendation}\n\n"
        "Якщо стан посилюється, триває довго або заважає нормально жити — "
        "варто звернутися до психолога або лікаря."
    )
