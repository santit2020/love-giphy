from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
    CallbackQueryHandler,
)

from telegram.request import HTTPXRequest
from telegram.error import TimedOut, NetworkError

from flask import Flask
from threading import Thread

import asyncio
import random
import os
import json
import warnings
import requests

# =========================
# KEEP ALIVE FOR RENDER
# =========================

app = Flask('')

@app.route('/')
def home():
    return "Love bot is alive 💖"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

# =========================
# WARNINGS
# =========================

warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    module="telegram.ext._conversationhandler"
)

# =========================
# ENV VARIABLES
# =========================

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GIPHY_API_KEY = os.getenv("GIPHY_API_KEY")

if not BOT_TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN missing!")
    exit(1)

if not GIPHY_API_KEY:
    print("❌ GIPHY_API_KEY missing!")
    exit(1)

print("🔑 Environment variables loaded successfully")

# =========================
# USER STORAGE
# =========================

USERS_FILE = 'users.json'

AWAITING_NAME = {}

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}

    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

users = load_users()

ASKING_NAME = 1

# =========================
# LOVE MESSAGES
# =========================

message_templates = [
    "i love uuuuuuuuuu ❤️",
    "am soooooo proud of you ✨🥺",
    "am rlyyyy proud of you my {name}",
    "you're doing amazing sweetie 💋",
    "u are awesome 😊",
    "sending u a huge hug 🤗",
    "you've got this 🥹",
    "you are so loved {name} ❤️",
    "you light up my life ✨",
    "sending all my love 💖",
    "i miss u so much 🥺",
]

love_u_more = [
    "love u more 💖",
    "love u infinity times ♾️",
    "noooo i love YOU moreeeee!",
    "i love u toooo {name} 💋",
]

# =========================
# SAFE SEND
# =========================

async def safe_send_message(
    bot,
    chat_id,
    text,
    reply_markup=None,
    parse_mode=None,
    max_retries=3
):
    for attempt in range(max_retries):
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
            return True

        except (TimedOut, NetworkError) as e:
            print(f"⚠️ retry {attempt+1}: {e}")

            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)

        except Exception as e:
            print(f"❌ send failed: {e}")
            break

    return False

# =========================
# GIF SENDER
# =========================

async def send_scheduled_gif(context, chat_id):

    search_terms = [
        "cute anime hug",
        "anime love",
        "cute cat love",
        "anime kiss",
        "anime blush",
    ]

    term = random.choice(search_terms)

    try:
        url = "https://api.giphy.com/v1/gifs/search"

        params = {
            "api_key": GIPHY_API_KEY,
            "q": term,
            "limit": 20,
            "rating": "g"
        }

        response = requests.get(url, params=params)
        data = response.json()

        if data["data"]:

            gif = random.choice(data["data"])

            gif_url = gif["images"]["original"]["url"]

            await context.bot.send_animation(
                chat_id=chat_id,
                animation=gif_url
            )

            print(f"🎬 sent gif to {chat_id}")

    except Exception as e:
        print(f"❌ gif error: {e}")

# =========================
# SCHEDULE MESSAGES
# =========================

def schedule_user_job(application, chat_id, hours):

    async def job_callback(context):

        user_data = users.get(chat_id, {})

        if not user_data.get("subscribed"):
            return

        name = user_data.get("name", "friend")

        if random.randint(1, 5) == 1:
            await send_scheduled_gif(context, chat_id)

        message = random.choice(message_templates).format(name=name)

        await safe_send_message(
            context.bot,
            chat_id,
            message
        )

    job_name = f"love_{chat_id}"

    for job in application.job_queue.get_jobs_by_name(job_name):
        job.schedule_removal()

    application.job_queue.run_repeating(
        job_callback,
        interval=hours * 3600,
        first=20,
        name=job_name
    )

    print(f"⏰ scheduled {chat_id}")

# =========================
# START COMMAND
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = str(update.effective_chat.id)

    user = users.get(chat_id, {})

    if user.get("name"):

        await safe_send_message(
            context.bot,
            chat_id,
            f"👋 welcome back {user['name']} 💖"
        )

        return ConversationHandler.END

    await safe_send_message(
        context.bot,
        chat_id,
        "💖 hiiii what's your name?"
    )

    return ASKING_NAME

# =========================
# RECEIVE NAME
# =========================

async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = str(update.effective_chat.id)

    name = update.message.text.strip()

    users[chat_id] = {
        "name": name,
        "subscribed": True,
        "interval_hours": 24
    }

    save_users(users)

    schedule_user_job(context.application, chat_id, 24)

    keyboard = [
        [
            InlineKeyboardButton("1h", callback_data="freq_1"),
            InlineKeyboardButton("4h", callback_data="freq_4"),
        ],
        [
            InlineKeyboardButton("12h", callback_data="freq_12"),
            InlineKeyboardButton("24h", callback_data="freq_24"),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await safe_send_message(
        context.bot,
        chat_id,
        f"💌 thank u {name}! choose your love frequency:",
        reply_markup=reply_markup
    )

    return ConversationHandler.END

# =========================
# STOP COMMAND
# =========================

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = str(update.effective_chat.id)

    if chat_id in users:
        users[chat_id]["subscribed"] = False
        save_users(users)

    await safe_send_message(
        context.bot,
        chat_id,
        "💔 stopped love messages"
    )

# =========================
# SETTINGS
# =========================

async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [
            InlineKeyboardButton("💌 send love now", callback_data="send_now"),
            InlineKeyboardButton("🎬 send gif", callback_data="send_gif"),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await safe_send_message(
        context.bot,
        update.effective_chat.id,
        "⚙️ settings menu",
        reply_markup=reply_markup
    )

# =========================
# LOVE REPLIES
# =========================

async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text.lower()

    has_love = "love" in text or "luv" in text
    has_you = "you" in text or "u" in text.split()

    if has_love and has_you:

        chat_id = str(update.effective_chat.id)

        name = users.get(chat_id, {}).get("name", "friend")

        response = random.choice(love_u_more).format(name=name)

        await safe_send_message(
            context.bot,
            chat_id,
            response
        )

# =========================
# BUTTON HANDLER
# =========================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    chat_id = str(query.message.chat_id)

    data = query.data

    if data.startswith("freq_"):

        hours = int(data.split("_")[1])

        users[chat_id]["interval_hours"] = hours

        save_users(users)

        schedule_user_job(
            context.application,
            chat_id,
            hours
        )

        await query.edit_message_text(
            f"💖 messages every {hours} hour(s)"
        )

    elif data == "send_now":

        name = users.get(chat_id, {}).get("name", "friend")

        message = random.choice(message_templates).format(name=name)

        await safe_send_message(
            context.bot,
            chat_id,
            message
        )

    elif data == "send_gif":

        await send_scheduled_gif(context, chat_id)

# =========================
# HELP COMMAND
# =========================

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = """
💖 COMMANDS

/start → start bot
/settings → open settings
/stop → stop messages
/help → help menu

Say "love u" for surprise replies 💋
"""

    await safe_send_message(
        context.bot,
        update.effective_chat.id,
        text
    )

# =========================
# MAIN
# =========================

async def main():

    print("🤖 starting love bot...")

    request = HTTPXRequest(
        connection_pool_size=8,
        connect_timeout=30,
        read_timeout=30,
        write_timeout=30,
        pool_timeout=30
    )

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .request(request)
        .build()
    )

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASKING_NAME: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    receive_name
                )
            ],
        },
        fallbacks=[]
    )

    application.add_handler(conv_handler)

    application.add_handler(CommandHandler("stop", stop))

    application.add_handler(CommandHandler("settings", settings))

    application.add_handler(CommandHandler("help", help_command))

    application.add_handler(CallbackQueryHandler(button_handler))

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_text_messages
        )
    )

    for chat_id, data in users.items():

        if data.get("subscribed"):

            hours = data.get("interval_hours", 24)

            schedule_user_job(
                application,
                chat_id,
                hours
            )

    print("💖 bot is alive!")

    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    while True:
        await asyncio.sleep(3600)

# =========================
# RUN
# =========================

if __name__ == '__main__':

    keep_alive()

    asyncio.run(main())
