# Updated script with group rotation logic between Room #1 and Room #2

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

# Bot config
BOT_TOKEN = "7582873069:AAGnebTwavXrILNtZsDaX51buM2wG7nhAe8"
ADMIN_ID = 110259200
PUBLIC_GROUP_ID = -1002680256379

# Pre-created match groups
MATCH_GROUP_IDS = [-1002657351630, -4732482512]  # Replace with actual chat IDs of Room #1 and Room #2
current_group_index = 0  # Rotates between groups

# States
(
    CHOOSE_ROLE,
    COLLECT_SENDER_FROM,
    COLLECT_SENDER_TO,
    COLLECT_SENDER_ITEM,
    COLLECT_SENDER_DATE,
    COLLECT_TRAVELER_FROM,
    COLLECT_TRAVELER_TO,
    COLLECT_TRAVELER_DATE,
    COLLECT_TRAVELER_SPACE
) = range(9)

# Storage
user_data = {}
pending_matches = {}

# Rotate to next match group
def get_next_group_id():
    global current_group_index
    group_id = MATCH_GROUP_IDS[current_group_index]
    current_group_index = (current_group_index + 1) % len(MATCH_GROUP_IDS)
    return group_id

# Start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("✈️ Traveler", callback_data='role_traveler')],
        [InlineKeyboardButton("📦 Sender", callback_data='role_sender')]
    ]
    await update.message.reply_text("Are you a traveler or a sender?", reply_markup=InlineKeyboardMarkup(keyboard))
    return CHOOSE_ROLE

# Role
async def choose_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == 'role_sender':
        user_data[user_id] = {"role": "sender"}
        await query.message.reply_text("📍 Where is the item being sent *from*?")
        return COLLECT_SENDER_FROM
    else:
        user_data[user_id] = {"role": "traveler"}
        await query.message.reply_text("🛫 Where are you departing *from*?")
        return COLLECT_TRAVELER_FROM

# Sender flow
async def sender_from(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id]["from"] = update.message.text
    await update.message.reply_text("📦 Where is the item going *to*?")
    return COLLECT_SENDER_TO

async def sender_to(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id]["to"] = update.message.text
    await update.message.reply_text("📄 What kind of item is it?")
    return COLLECT_SENDER_ITEM

async def sender_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id]["item"] = update.message.text
    await update.message.reply_text("📅 By what date should it arrive?")
    return COLLECT_SENDER_DATE

async def sender_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id]["date"] = update.message.text

    data = user_data[user_id]
    post_text = (
        f"📦 *New Delivery Request!*\n\n"
        f"From: {data['from']}\n"
        f"To: {data['to']}\n"
        f"Item: {data['item']}\n"
        f"Deadline: {data['date']}\n\n"
        f"👤 Sender: [{update.effective_user.first_name}](tg://user?id={user_id})"
    )

    match_id = f"sender_{user_id}"
    pending_matches[match_id] = {"sender_id": user_id, "group_id": get_next_group_id()}

    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("✅ I can take this", callback_data=f"match_{match_id}")]]
    )

    await context.bot.send_message(chat_id=PUBLIC_GROUP_ID, text=post_text, parse_mode='Markdown', reply_markup=keyboard)
    await update.message.reply_text("✅ Your request has been published.")
    return ConversationHandler.END

# Traveler flow
async def traveler_from(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id]["from"] = update.message.text
    await update.message.reply_text("🛬 Where are you traveling *to*?")
    return COLLECT_TRAVELER_TO

async def traveler_to(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id]["to"] = update.message.text
    await update.message.reply_text("📅 What is your travel date?")
    return COLLECT_TRAVELER_DATE

async def traveler_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id]["date"] = update.message.text
    await update.message.reply_text("🎒 How much space do you have?")
    return COLLECT_TRAVELER_SPACE

async def traveler_space(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id]["space"] = update.message.text

    data = user_data[user_id]
    post_text = (
        f"✈️ *Traveler Available!*\n\n"
        f"From: {data['from']}\n"
        f"To: {data['to']}\n"
        f"Date: {data['date']}\n"
        f"Space: {data['space']}\n\n"
        f"👤 Traveler: [{update.effective_user.first_name}](tg://user?id={user_id})"
    )

    match_id = f"traveler_{user_id}"
    pending_matches[match_id] = {"traveler_id": user_id, "group_id": get_next_group_id()}

    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("📦 I want to send something", callback_data=f"match_{match_id}")]]
    )

    await context.bot.send_message(chat_id=PUBLIC_GROUP_ID, text=post_text, parse_mode='Markdown', reply_markup=keyboard)
    await update.message.reply_text("✅ Your travel info has been published.")
    return ConversationHandler.END

# Handle match button
async def handle_match_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    match_id = query.data.replace("match_", "")

    if match_id not in pending_matches:
        await query.message.reply_text("❌ Match not found.")
        return

    await context.bot.send_message(
        chat_id=user.id,
        text="🚀 Do you want to connect with this user and join a private chat?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Yes, connect us", callback_data=f"confirm_{match_id}_{user.id}")]
        ])
    )

# Handle confirmation
async def handle_confirm_match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.replace("confirm_", "").split("_")
    match_id = f"{parts[0]}_{parts[1]}"
    confirmer_id = int(parts[2])

    if match_id not in pending_matches:
        await query.message.reply_text("❌ Match no longer valid.")
        return

    match_info = pending_matches[match_id]
    group_id = match_info["group_id"]
    sender_id = match_info.get("sender_id", confirmer_id)
    traveler_id = match_info.get("traveler_id", confirmer_id)

    invite_link = await context.bot.create_chat_invite_link(chat_id=group_id)

    await context.bot.send_message(chat_id=sender_id, text=f"🔗 Join your match group: {invite_link.invite_link}")
    await context.bot.send_message(chat_id=traveler_id, text=f"🔗 Join your match group: {invite_link.invite_link}")
    await context.bot.send_message(chat_id=ADMIN_ID, text=f"🚀 New match assigned to group: {group_id}")

    del pending_matches[match_id]
    await query.message.reply_text("✅ Group invite sent!")

# Cancel
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Cancelled.")
    return ConversationHandler.END

# Setup
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
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

app.add_handler(conv_handler)
app.add_handler(CallbackQueryHandler(handle_match_click, pattern=r'^match_'))
app.add_handler(CallbackQueryHandler(handle_confirm_match, pattern=r'^confirm_'))

app.run_polling()
