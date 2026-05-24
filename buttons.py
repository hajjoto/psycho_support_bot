BTN_START = "Почати"
BTN_RESTART = "Почати нову сесію"
BTN_YES = "Так"
BTN_NO_FAST = "Ні, потрібно швидше"
BTN_NEXT = "Далі"
BTN_BETTER = "Стало легше"
BTN_NOT_BETTER = "Не стало легше"
BTN_REPEAT = "Спробувати іншу вправу"
BTN_ADVICE = "Ще одна порада"
BTN_NEW_EXERCISE = "Нова вправа"
BTN_FINISH = "Завершити діалог"
BTN_SHORT = "Коротка вправа"
BTN_FULL = "Повна вправа"
BTN_UNDERSTAND = "Зрозуміти свій стан"
BTN_EXERCISES = "Перейти до вправ"
BTN_DAILY_ADVICE = "Поради на день"
BTN_KEEP_SHOW = "Показати способи"
BTN_LATER = "Іншим разом"
BTN_THANKS = "Дякую"
BTN_REDUCE_NOW = "Знизити напругу зараз"
BTN_TO_SURVEY = "Перейти до опитування"
BTN_WHAT_HELPS = "Що може допомогти"
BTN_AVOID = "Чого краще не робити"
BTN_PLAN = "План на 30 хвилин"
BTN_SELF_HELP_STRESS = "Як допомогти собі при стресі"
BTN_HOW_APPLY = "Як це застосувати"


def clean_button(text: str) -> str:
    if not text:
        return ""

    text = text.strip()

    buttons = [
        BTN_START,
        BTN_RESTART,
        BTN_YES,
        BTN_NO_FAST,
        BTN_NEXT,
        BTN_BETTER,
        BTN_NOT_BETTER,
        BTN_REPEAT,
        BTN_ADVICE,
        BTN_NEW_EXERCISE,
        BTN_FINISH,
        BTN_SHORT,
        BTN_FULL,
        BTN_UNDERSTAND,
        BTN_EXERCISES,
        BTN_DAILY_ADVICE,
        BTN_KEEP_SHOW,
        BTN_LATER,
        BTN_THANKS,
        BTN_REDUCE_NOW,
        BTN_TO_SURVEY,
        BTN_WHAT_HELPS,
        BTN_AVOID,
        BTN_PLAN
    ]

    for button in buttons:
        if text.endswith(button):
            return button

    return text
