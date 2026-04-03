import os
from groq import AsyncGroq
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Состояния диалога
CHOOSING_LEVEL, CHOOSING_DURATION, CHOOSING_STUDENTS, CHOOSING_TOPIC, CHATTING = range(5)

LEVELS = ["A1 — Beginner", "A2 — Elementary", "B1 — Intermediate", "B2 — Upper-Intermediate", "C1/C2 — Advanced", "🤷 Level unknown"]
TOPICS = ["📝 Grammar", "🗣 Speaking", "📚 Vocabulary", "✍️ Writing", "🎧 Listening", "🎲 Surprise me!"]
DURATIONS = ["30 min", "45 min", "60 min", "90 min"]
STUDENTS = ["1 (individual)", "2-5 (small group)", "6-10 (group)", "10+ (class)"]

SYSTEM_PROMPT = """You are an expert English teaching assistant helping teachers create lesson ideas and activities.

Your specialty:
- Generating creative, practical lesson ideas for English teachers
- Adapting all suggestions to the student's proficiency level, lesson duration and class size
- Providing ready-to-use activities with clear step-by-step instructions

Formatting rules (VERY IMPORTANT):
- ALWAYS respond in Russian, but keep all English examples, activities names and vocabulary in English
- Mix: explanations and instructions in Russian, English terms stay in English
- Example: "🎯 **Debate: Pros and Cons**\n📋 Описание: студенты обсуждают тему..."

🎯 **Activity Name**
📋 Description: what to do
⚙️ How it works: step by step
⏱ Time: X minutes
👥 Works best for: class size note

- Give exactly 3-4 ideas
- Be specific and practical
- Do NOT mention the level, duration or class size in your intro text — just dive straight into the ideas
- Start directly with the first activity, no intro sentences whatsoever
- Never say "Here are some ideas", "Вот несколько идей", "For this level" or anything similar
- Just start with the first emoji and activity name immediately
"""


async def ask_groq(messages: list, context_info: dict) -> str:
    level = context_info.get("level", "unknown")
    duration = context_info.get("duration", "45 min")
    students = context_info.get("students", "unknown")

    system = SYSTEM_PROMPT + f"""
Current lesson context:
- Student level: {level}
- Lesson duration: {duration}
- Number of students: {students}

Adapt ALL activities to fit within {duration} and suit {students} students."""

    client = AsyncGroq(api_key=GROQ_API_KEY)
    response = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": system}] + messages,
        max_tokens=1500,
    )
    return response.choices[0].message.content


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    keyboard = [[level] for level in LEVELS]
    await update.message.reply_text(
        "👋 Hi! I'm your *English Teaching Assistant*.\n"
        "Привет! Я помогаю учителям английского создавать идеи для уроков.\n\n"
        "🎯 Выберите уровень ученика:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return CHOOSING_LEVEL


async def choose_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["level"] = update.message.text
    context.user_data["history"] = []

    keyboard = [[d] for d in DURATIONS]
    await update.message.reply_text(
        "⏱ Сколько длится урок?",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return CHOOSING_DURATION


async def choose_duration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["duration"] = update.message.text

    keyboard = [[s] for s in STUDENTS]
    await update.message.reply_text(
        "👥 Сколько учеников?",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return CHOOSING_STUDENTS


async def choose_students(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["students"] = update.message.text

    level = context.user_data["level"]
    duration = context.user_data["duration"]
    students = context.user_data["students"]

    keyboard = [[topic] for topic in TOPICS]
    await update.message.reply_text(
        f"✅ *Настройки урока:*\n"
        f"📊 Уровень: {level}\n"
        f"⏱ Длительность: {duration}\n"
        f"👥 Учеников: {students}\n\n"
        f"Выберите тип активности:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return CHOOSING_TOPIC


async def choose_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    topic = update.message.text
    context_info = {
        "level": context.user_data.get("level"),
        "duration": context.user_data.get("duration"),
        "students": context.user_data.get("students"),
    }

    if topic == "🎲 Surprise me!":
        user_message = "Give me a creative and fun surprise activity idea."
    else:
        user_message = f"Give me 3-4 practical {topic} activity ideas."

    context.user_data["history"].append({"role": "user", "content": user_message})
    await update.message.reply_text("⏳ Генерирую идеи...")

    response = await ask_groq(context.user_data["history"], context_info)
    context.user_data["history"].append({"role": "assistant", "content": response})

    await update.message.reply_text(
        response,
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(
            [["🔄 Другая тема", "⚙️ Новые настройки", "🎲 Surprise me!"]],
            resize_keyboard=True
        )
    )
    return CHATTING


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    context_info = {
        "level": context.user_data.get("level"),
        "duration": context.user_data.get("duration"),
        "students": context.user_data.get("students"),
    }

    if text == "🔄 Другая тема":
        keyboard = [[topic] for topic in TOPICS]
        await update.message.reply_text(
            "Выберите тему:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return CHOOSING_TOPIC

    if text == "⚙️ Новые настройки":
        return await start(update, context)

    if text == "🎲 Surprise me!":
        text = "Give me a creative surprise activity!"

    context.user_data["history"].append({"role": "user", "content": text})

    if len(context.user_data["history"]) > 10:
        context.user_data["history"] = context.user_data["history"][-10:]

    await update.message.reply_text("⏳ Думаю...")

    response = await ask_groq(context.user_data["history"], context_info)
    context.user_data["history"].append({"role": "assistant", "content": response})

    await update.message.reply_text(
        response,
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(
            [["🔄 Другая тема", "⚙️ Новые настройки", "🎲 Surprise me!"]],
            resize_keyboard=True
        )
    )
    return CHATTING


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *English Teaching Assistant*\n\n"
        "Помогаю учителям английского создавать идеи для уроков.\n\n"
        "Команды:\n"
        "/start — Начать заново\n"
        "/help — Это сообщение\n\n"
        "После настройки урока можете просто писать запросы:\n"
        "— _'Придумай игру для закрепления Present Simple'_\n"
        "— _'Нужно что-то для работы в парах'_\n"
        "— _'Активность на первые 10 минут урока'_",
        parse_mode="Markdown"
    )


def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_LEVEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_level)],
            CHOOSING_DURATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_duration)],
            CHOOSING_STUDENTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_students)],
            CHOOSING_TOPIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_topic)],
            CHATTING: [MessageHandler(filters.TEXT & ~filters.COMMAND, chat)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("help", help_command))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()