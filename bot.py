# Full Persian bot.py script with extended traveler questions and group rotation

import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters
)

# تنظیمات بات
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 110259200
PUBLIC_GROUP_ID = -1002680256379
MATCH_GROUP_IDS = [-1002657351630, -4732482512]  # Room #1 and Room #2
current_group_index = 0

# وضعیت‌ها
(
    CHOOSE_ROLE,
    COLLECT_SENDER_FROM,
    COLLECT_SENDER_TO,
    COLLECT_SENDER_ITEM,
    COLLECT_SENDER_DATE,
    COLLECT_TRAVELER_FROM,
    COLLECT_TRAVELER_TO,
    COLLECT_TRAVELER_DATE,
    COLLECT_TRAVELER_SPACE,
    COLLECT_TRAVELER_AIRLINE,
    COLLECT_TRAVELER_DEST_OPTION,
    COLLECT_TRAVELER_NOTE
) = range(12)

user_data = {}
pending_matches = {}

def get_next_group_id():
    global current_group_index
    group_id = MATCH_GROUP_IDS[current_group_index]
    current_group_index = (current_group_index + 1) % len(MATCH_GROUP_IDS)
    return group_id

# شروع
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    keyboard = [
        [InlineKeyboardButton("✈️ مسافر", callback_data='role_traveler')],
        [InlineKeyboardButton("📦 فرستنده", callback_data='role_sender')],
        [InlineKeyboardButton("🔎 خودم می‌گردم", url="https://t.me/YOUR_PUBLIC_GROUP_LINK")]
    ]
    await update.message.reply_text("🚩 شما فرستنده‌اید یا مسافر؟", reply_markup=InlineKeyboardMarkup(keyboard))
    return CHOOSE_ROLE

# نقش
async def choose_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == 'role_sender':
        user_data[user_id] = {"role": "sender"}
        await query.message.reply_text("📍 مبدا بسته کجاست؟")
        return COLLECT_SENDER_FROM
    else:
        user_data[user_id] = {"role": "traveler"}
        await query.message.reply_text("🛫 مبدا سفر شما کجاست؟")
        return COLLECT_TRAVELER_FROM

# فرستنده
async def sender_from(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id]["from"] = update.message.text
    await update.message.reply_text("📦 مقصد بسته کجاست؟")
    return COLLECT_SENDER_TO

async def sender_to(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id]["to"] = update.message.text
    await update.message.reply_text("📄 چه نوع بسته‌ای است؟")
    return COLLECT_SENDER_ITEM

async def sender_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id]["item"] = update.message.text
    await update.message.reply_text("📅 بسته تا چه تاریخی باید برسد؟")
    return COLLECT_SENDER_DATE

async def sender_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id]["date"] = update.message.text
    data = user_data[user_id]

    post_text = (
        f"📦 *درخواست ارسال جدید*\n\n"
        f"مبدا: {data['from']}\n"
        f"مقصد: {data['to']}\n"
        f"نوع بسته: {data['item']}\n"
        f"تاریخ موردنظر: {data['date']}\n\n"
        f"👤 فرستنده: [{update.effective_user.first_name}](tg://user?id={user_id})"
    )

    match_id = f"sender_{user_id}"
    pending_matches[match_id] = {"sender_id": user_id, "group_id": get_next_group_id()}

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ من می‌توانم این را ببرم", callback_data=f"match_{match_id}")]
    ])

    await context.bot.send_message(chat_id=PUBLIC_GROUP_ID, text=post_text, parse_mode='Markdown', reply_markup=keyboard)
    await update.message.reply_text("✅ درخواست شما منتشر شد.")
    return ConversationHandler.END

# مسافر
async def traveler_from(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id] = {"from": update.message.text}
    await update.message.reply_text("🛬 مقصد سفر شما کجاست؟")
    return COLLECT_TRAVELER_TO

async def traveler_to(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id]["to"] = update.message.text
    await update.message.reply_text("📅 تاریخ سفرتان چیست؟")
    return COLLECT_TRAVELER_DATE

async def traveler_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id]["date"] = update.message.text
    await update.message.reply_text("🎒 چقدر فضا دارید؟ (مثلاً ۲ کیلو یا یک کیف دستی)")
    return COLLECT_TRAVELER_SPACE

async def traveler_space(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id]["space"] = update.message.text
    await update.message.reply_text("✈️ نام شرکت هواپیمایی چیست؟")
    return COLLECT_TRAVELER_AIRLINE

async def traveler_airline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id]["airline"] = update.message.text
    await update.message.reply_text("🏙 آیا امکان تحویل بسته به شهرهای دیگر در مقصد وجود دارد؟")
    return COLLECT_TRAVELER_DEST_OPTION

async def traveler_dest_option(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id]["city_option"] = update.message.text
    await update.message.reply_text("📝 توضیحات تکمیلی:")
    return COLLECT_TRAVELER_NOTE

async def traveler_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id]["note"] = update.message.text
    data = user_data[user_id]

    post_text = (
        f"✈️ *مسافر موجود است!*\n\n"
        f"مبدا: {data['from']}\n"
        f"مقصد: {data['to']}\n"
        f"تاریخ سفر: {data['date']}\n"
        f"فضا: {data['space']}\n"
        f"شرکت هواپیمایی: {data['airline']}\n"
        f"ارسال به شهرهای دیگر: {data['city_option']}\n"
        f"توضیحات: {data['note']}\n\n"
        f"👤 مسافر: [{update.effective_user.first_name}](tg://user?id={user_id})"
    )

    match_id = f"traveler_{user_id}"
    pending_matches[match_id] = {"traveler_id": user_id, "group_id": get_next_group_id()}

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📦 می‌خواهم بسته‌ای ارسال کنم", callback_data=f"match_{match_id}")]
    ])

    await context.bot.send_message(chat_id=PUBLIC_GROUP_ID, text=post_text, parse_mode='Markdown', reply_markup=keyboard)
    await update.message.reply_text("✅ اطلاعات سفر شما با موفقیت منتشر شد.")
    return ConversationHandler.END

# تطبیق و تأیید
async def handle_match_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    match_id = query.data.replace("match_", "")

    if match_id not in pending_matches:
        await query.message.reply_text("❌ تطابقی یافت نشد.")
        return

    await context.bot.send_message(
        chat_id=user.id,
        text="🚀 آیا مایلید با این کاربر وارد چت خصوصی شوید؟",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ بله، ما را متصل کن", callback_data=f"confirm_{match_id}_{user.id}")]
        ])
    )

async def handle_confirm_match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.replace("confirm_", "").split("_")
    match_id = f"{parts[0]}_{parts[1]}"
    confirmer_id = int(parts[2])

    if match_id not in pending_matches:
        await query.message.reply_text("❌ این تطابق دیگر معتبر نیست.")
        return

    match_info = pending_matches[match_id]
    group_id = match_info["group_id"]
    sender_id = match_info.get("sender_id", confirmer_id)
    traveler_id = match_info.get("traveler_id", confirmer_id)

    invite_link = await context.bot.create_chat_invite_link(chat_id=group_id)
    await context.bot.send_message(chat_id=sender_id, text=f"🔗 به گروه گفتگو بپیوندید: {invite_link.invite_link}")
    await context.bot.send_message(chat_id=traveler_id, text=f"🔗 به گروه گفتگو بپیوندید: {invite_link.invite_link}")
    await context.bot.send_message(chat_id=ADMIN_ID, text=f"🚀 یک تطابق جدید به گروه زیر اختصاص یافت: {group_id}")

    del pending_matches[match_id]
    await query.message.reply_text("✅ لینک گروه ارسال شد!")

# لغو
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ عملیات لغو شد.")
    return ConversationHandler.END

# راه‌اندازی بات
app = ApplicationBuilder().token(BOT_TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        CHOOSE_ROLE: [CallbackQueryHandler(choose_role)],
        COLLECT_SENDER_FROM: [MessageHandler(filters.TEXT & ~filters.COMMAND, sender_from)],
        COLLECT_SENDER_TO: [MessageHandler(filters.TEXT & ~filters.COMMAND, sender_to)],
        COLLECT_SENDER_ITEM: [MessageHandler(filters.TEXT & ~filters.COMMAND, sender_item)],
        COLLECT_SENDER_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, sender_date)],
        COLLECT_TRAVELER_FROM: [MessageHandler(filters.TEXT & ~filters.COMMAND, traveler_from)],
        COLLECT_TRAVELER_TO: [MessageHandler(filters.TEXT & ~filters.COMMAND, traveler_to)],
        COLLECT_TRAVELER_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, traveler_date)],
        COLLECT_TRAVELER_SPACE: [MessageHandler(filters.TEXT & ~filters.COMMAND, traveler_space)],
        COLLECT_TRAVELER_AIRLINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, traveler_airline)],
        COLLECT_TRAVELER_DEST_OPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, traveler_dest_option)],
        COLLECT_TRAVELER_NOTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, traveler_note)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

app.add_handler(conv_handler)
app.add_handler(CallbackQueryHandler(handle_match_click, pattern=r'^match_'))
app.add_handler(CallbackQueryHandler(handle_confirm_match, pattern=r'^confirm_'))

app.run_polling()


from telegram import BotCommand
from telegram.ext import CommandHandler

async def help_command(update, context):
    await update.message.reply_text("📩 برای پشتیبانی، با ادمین در تماس باشید.")

async def setup_command(update, context):
    if update.effective_user.id == ADMIN_ID:
        await update.message.reply_text("⚙️ تنظیمات انجام شد.")
    else:
        await update.message.reply_text("⛔ فقط مدیر اجازه دارد این دستور را اجرا کند.")

async def set_commands(app):
    await app.bot.set_my_commands([
        BotCommand("start", "شروع بات و انتخاب نقش"),
        BotCommand("help", "راهنما و تماس با پشتیبانی"),
        BotCommand("setup", "تنظیمات اولیه (فقط برای مدیر)")
    ])

@app.on_startup
async def init_menu(app):
    await set_commands(app)

app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("setup", setup_command))
