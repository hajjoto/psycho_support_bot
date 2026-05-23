from aiogram.types import BotCommand


BOT_COMMANDS = [
    BotCommand(command="start", description="🔄 Почати спочатку"),
    BotCommand(command="reminder", description="🗓 Налаштувати нагадування"),
    BotCommand(command="keep", description="📌 Тримати під рукою"),
    BotCommand(command="review", description="💌 Написати відгук"),
    BotCommand(command="language", description="🌐 Обрати мову"),
    BotCommand(command="help", description="ℹ️ Допомога"),
    BotCommand(command="contacts", description="☎️ Екстрені контакти"),
]