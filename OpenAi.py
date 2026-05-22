import logging
import asyncio
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from openai import OpenAI

# ================= CONFIG =================
import os

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BOT_USERNAME = "AdvanceChatRobot"  # without @

# =========================================

logging.basicConfig(level=logging.INFO)

client = OpenAI(api_key=OPENAI_API_KEY)

# ================= DATABASE (TEMP) =================
USERS = {}
# USERS[user_id] = {
#   "referrals": 0,
#   "pro": False,
#   "referred_by": None
# }
# ==================================================

# 🔹 /start + REFERRAL
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    if user_id not in USERS:
        USERS[user_id] = {"referrals": 0, "pro": False, "referred_by": None}

    # referral detect
    if context.args:
        arg = context.args[0]
        if arg.startswith("REF_"):
            referrer_id = int(arg.replace("REF_", ""))
            if referrer_id != user_id and USERS[user_id]["referred_by"] is None:
                USERS[user_id]["referred_by"] = referrer_id
                if referrer_id in USERS:
                    USERS[referrer_id]["referrals"] += 1

    await update.message.reply_text(
                "» 𝙃𝙀𝙇𝙇𝙊 👋 𝘼𝙉𝘿 𝙒𝙀𝙇𝘾𝙊𝙈𝙀 𝙏𝙊 𝘼𝘿𝙑𝘼𝙉𝘾𝙀 𝘼𝙄 𝘾𝙃𝘼𝙏 𝘽𝙊𝙏🎃\n" 
            "𝘼𝙎𝙆 𝙈𝙀 𝘼𝙉𝙔𝙏𝙃𝙄𝙉𝙂👑\n\n"
        "» 𝙏𝙤 𝙘𝙝𝙖𝙩 𝙬𝙞𝙩𝙝 𝘽𝙤𝙩👇:\n"
        "`/chat` <𝙔𝙤𝙪𝙧 𝙈𝙖𝙨𝙨𝙖𝙜𝙚>\n\n"
        "» 𝘗𝘰𝘸𝘦𝘳𝘦𝘥 𝘉𝘺 OhhCoder.t.me 🍷",
        parse_mode="Markdown"
    )

# 🔹 UPGRADE BUTTON
def upgrade_button():
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("🚀 𝘜𝘱𝘨𝘳𝘢𝘥𝘦 𝘵𝘰 𝘱𝘳𝘰 𝘝𝘦𝘳𝘴𝘪𝘰𝘯", callback_data="upgrade")]]
    )

# 🔹 CHAT
async def chat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in USERS:
        USERS[user_id] = {"referrals": 0, "pro": False, "referred_by": None}

    if not context.args:
        await update.message.reply_text("❗ `/chat your message`", parse_mode="Markdown")
        return

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )

    try:
        user_text = " ".join(context.args)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": user_text}
            ]
        )

        markup = None
        if not USERS[user_id]["pro"]:
            markup = upgrade_button()

        await update.message.reply_text(
            response.choices[0].message.content,
            reply_markup=markup
        )

    except:
        await update.message.reply_text("❌ Error, try later")

# 🔹 UPGRADE HANDLER
async def upgrade_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    refs = USERS[user_id]["referrals"]

    if refs >= 5:
        USERS[user_id]["pro"] = True
        await query.message.edit_text("✅ 𝙋𝙍𝙊 𝙑𝙀𝙍𝙎𝙄𝙊𝙉 𝘼𝘾𝙏𝙄𝙑𝘼𝙏𝙀𝘿 🎉")
    else:
        link = f"https://t.me/{BOT_USERNAME}?start=REF_{user_id}"
        await query.message.reply_text(
            f"🔒 𝙋𝙧𝙤 𝙇𝙤𝙘𝙠𝙚𝙙\n\n"
            f"» 𝙍𝙚𝙦𝙪𝙞𝙧𝙚𝙙: 5 𝙍𝙚𝙛𝙚𝙧𝙧𝙖𝙡𝙨\n"
            f"» 𝙏𝙤𝙩𝙖𝙡 𝘾𝙤𝙪𝙣𝙩: {refs}\n\n"
            f"🔗 𝙔𝙤𝙪𝙧 𝙇𝙞𝙣𝙠:\n{link}"
        )

# 🔹 MAIN
def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(upgrade_handler, pattern="upgrade"))
    app.add_handler(CommandHandler("chat", chat_command))

    logging.info("🤖 Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()