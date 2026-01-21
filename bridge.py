import telebot
import requests
from threading import Timer
import re
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from telebot.types import ReplyKeyboardRemove
import os

TOKEN = os.getenv("TELEGRAM_TOKEN")
RASA_URL = os.getenv("RASA_URL")

bot = telebot.TeleBot(TOKEN)
user_buffers = {}

def format_html(text: str) -> str:
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)

    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)

    text = re.sub(r"(?m)^\s*\.\.\.\s*$", "", text)

    text = re.sub(r"--+", "", text)

    text = re.sub(r"(?m)^\s*-\s+", "• ", text)
    text = re.sub(r"(?m)^\s*\d+\.\s+", "• ", text)

    text = re.sub(r"(?m)^•\s*([А-ЯA-Z][^:\n]{3,}):\s*$", r"\1", text)

    text = re.sub(
        r"(?m)^(?!•)([А-ЯA-Z][^.\n]{6,})$",
        r"\n<b>\1</b>",
        text
    )

    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()

def format_terms(text: str) -> str:
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)

    lines = [line.strip() for line in text.split("\n") if line.strip()]
    result = []

    for line in lines:
        if len(line) < 60 and not line.endswith("."):
            result.append(f"\n<b>{line}</b>")
        else:
            result.append(line)

    return "\n".join(result).strip()

def send_to_rasa(chat_id):
    if chat_id not in user_buffers:
        return

    full_text = user_buffers[chat_id]
    del user_buffers[chat_id]

    try:
        responses = requests.post(
            RASA_URL,
            json={"sender": str(chat_id), "message": full_text}
        ).json()

        combined_text = ""
        buttons = None

        for resp in responses:
            if "buttons" in resp:
                buttons = resp["buttons"]

            if "text" in resp and resp["text"]:
                line = resp["text"].strip()

                if line == "...":
                    continue

                combined_text += line + "\n\n"

        if "Ключевые термины" in combined_text:
            combined_text = format_terms(combined_text)
        else:
            combined_text = format_html(combined_text)

        if buttons:
            keyboard = ReplyKeyboardMarkup(
                resize_keyboard=True,
                one_time_keyboard=True
            )
            for btn in buttons:
                keyboard.add(KeyboardButton(btn["title"]))

            bot.send_message(
                chat_id,
                combined_text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )

        else:
            bot.send_message(
                chat_id,
                combined_text,
                parse_mode="HTML"
            )

            bot.send_message(
                chat_id,
                "✨ <b>Готово.</b>\n\n"
                "Если хотите продолжить — просто отправьте следующий текст 📄",
                reply_markup=ReplyKeyboardRemove(),
                parse_mode="HTML"
            )

    except Exception as e:
        print(f"Error: {e}")

@bot.message_handler(commands=["start"])
def start_cmd(message):
    bot.send_message(
        message.chat.id,
        "👋 <b>Добро пожаловать!</b>\n\n"
        "Я — бот-конспектатор.\n"
        "Пришлите учебный текст, и я помогу вам с ним работать 📚",
        parse_mode="HTML"
    )

@bot.message_handler(commands=["help"])
def help_cmd(message):
    bot.send_message(
        message.chat.id,
        "ℹ️ <b>Как пользоваться ботом</b>\n\n"
        "1) Пришлите текст\n"
        "2) Выберите действие\n"
        "3) Получите результат\n\n"
        "Вы можете отправлять тексты сколько угодно раз.",
        parse_mode="HTML"
    )

@bot.message_handler(commands=["about"])
def about_cmd(message):
    bot.send_message(
        message.chat.id,
        "🤖 <b>О боте</b>\n\n"
        "Бот разработан в рамках университетской практики.\n"
        "Использует технологии NLP и ИИ для работы с учебными текстами.",
        parse_mode="HTML"
    )

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    
    chat_id = message.chat.id
    text = message.text if message.text else ""
    
    if chat_id not in user_buffers:
        user_buffers[chat_id] = text
    else:
        user_buffers[chat_id] += " " + text
    
    if hasattr(handle_message, f"timer_{chat_id}"):
        getattr(handle_message, f"timer_{chat_id}").cancel()
    
    t = Timer(1.0, send_to_rasa, args=[chat_id])
    setattr(handle_message, f"timer_{chat_id}", t)
    t.start()

if __name__ == "__main__":
    print("🚀 Мост запущен! Токен проверен.")
    bot.set_my_commands([
        telebot.types.BotCommand("start", "Запустить бота"),
        telebot.types.BotCommand("help", "Как пользоваться ботом"),
        telebot.types.BotCommand("about", "О боте")
    ])
    bot.polling(none_stop=True)