BTN_START = "Почати"
BTN_RESTART = "Почати нову сесію"
BTN_YES = "Так"
BTN_NO_FAST = "Ні, потрібно швидше"
BTN_NEXT = "Далі"
BTN_BETTER = "Стало легше"
BTN_NOT_BETTER = "Не стало легше"
BTN_REPEAT = "Повторити вправу"
BTN_ADVICE = "Ще одна порада"
BTN_FINISH = "Завершити діалог"


def clean_button(text: str) -> str:
    text = text.strip()

    for button in [
        BTN_START,
        BTN_RESTART,
        BTN_YES,
        BTN_NO_FAST,
        BTN_NEXT,
        BTN_BETTER,
        BTN_NOT_BETTER,
        BTN_REPEAT,
        BTN_ADVICE,
        BTN_FINISH,
    ]:
        if text.endswith(button):
            return button

    return text