import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from src.config import BOT_TOKEN, USDT_WALLET, ADMIN_ID, CURRENCY, ACCOUNT_TYPES
from src.database import get_balance, add_balance, deduct_balance, create_order, get_user_orders

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

user_states = {}


def main_keyboard():
    keyboard = [
        [InlineKeyboardButton("💰 My Wallet", callback_data="wallet")],
        [InlineKeyboardButton("🛒 Buy Accounts", callback_data="buy_menu")],
        [InlineKeyboardButton("📞 Contact Support", callback_data="support")]
    ]
    return InlineKeyboardMarkup(keyboard)


def wallet_keyboard():
    keyboard = [
        [InlineKeyboardButton("💳 Add Funds", callback_data="add_funds")],
        [InlineKeyboardButton("⬅️ Main Menu", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def buy_menu_keyboard():
    keyboard = []
    for acc in ACCOUNT_TYPES:
        keyboard.append([InlineKeyboardButton(f"{acc['emoji']} {acc['name']} - {acc['price']} {CURRENCY}", callback_data=f"view_{acc['id']}")])
    keyboard.append([InlineKeyboardButton("⬅️ Main Menu", callback_data="back_main")])
    return InlineKeyboardMarkup(keyboard)


def account_keyboard(account_id):
    keyboard = [
        [InlineKeyboardButton("🛒 Purchase", callback_data=f"purchase_{account_id}")],
        [InlineKeyboardButton("⬅️ Back", callback_data="buy_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


def purchase_confirm_keyboard(account_id):
    keyboard = [
        [InlineKeyboardButton("✅ Confirm Purchase", callback_data=f"confirm_{account_id}")],
        [InlineKeyboardButton("⬅️ Cancel", callback_data="buy_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    first_name = update.effective_user.first_name or "there"
    text = (
        f"👋 Welcome <b>{first_name}</b> to <b>Reddit Accounts Store</b>!\n\n"
        f"We offer high-quality Reddit accounts.\n"
        f"Add funds to your wallet and purchase instantly."
    )
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=main_keyboard())


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    user_id = update.effective_user.id
    data = query.data

    if data == "back_main":
        text = "👋 <b>Main Menu</b>\n\nChoose an option below:"
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=main_keyboard())
        return

    if data == "support":
        text = "📞 <b>Contact Support</b>\n\nFor any questions or issues, contact us directly:\n@YourSupportUsername\n\nWe usually respond within 24 hours."
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Main Menu", callback_data="back_main")]])
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=keyboard)
        return

    if data == "wallet":
        balance = get_balance(user_id)
        text = (
            f"💰 <b>My Wallet</b>\n\n"
            f"Your balance: <b>{balance:.2f} {CURRENCY}</b>\n\n"
            f"Use \"Add Funds\" to deposit USDT into your wallet."
        )
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=wallet_keyboard())
        return

    if data == "add_funds":
        user_states[user_id] = {"step": "awaiting_amount"}
        await query.edit_message_text(
            f"💳 <b>Add Funds</b>\n\n"
            f"Enter the amount of {CURRENCY} you want to deposit (minimum 5 {CURRENCY}):",
            parse_mode="HTML"
        )
        return

    if data == "buy_menu":
        text = "🛒 <b>Buy Accounts</b>\n\nSelect an account type:"
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=buy_menu_keyboard())
        return

    if data.startswith("view_"):
        account_id = data.replace("view_", "")
        account = next((a for a in ACCOUNT_TYPES if a["id"] == account_id), None)
        if not account:
            return
        text = (
            f"<b>{account['emoji']} {account['name']}</b>\n\n"
            f"📅 <b>Age:</b> {account['age']}\n"
            f"📊 <b>Karma:</b> {account['karma']}\n"
            f"💰 <b>Price:</b> {account['price']} {CURRENCY}\n\n"
            f"{account['description']}"
        )
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=account_keyboard(account_id))
        return

    if data.startswith("purchase_"):
        account_id = data.replace("purchase_", "")
        account = next((a for a in ACCOUNT_TYPES if a["id"] == account_id), None)
        if not account:
            return
        balance = get_balance(user_id)
        if balance < account["price"]:
            text = (
                f"❌ <b>Insufficient Balance</b>\n\n"
                f"You need <b>{account['price']} {CURRENCY}</b> to purchase this account.\n"
                f"Your balance: <b>{balance:.2f} {CURRENCY}</b>\n\n"
                f"Please add funds first."
            )
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("💰 Add Funds", callback_data="add_funds")],
                [InlineKeyboardButton("⬅️ Back", callback_data="buy_menu")]
            ])
            await query.edit_message_text(text, parse_mode="HTML", reply_markup=keyboard)
            return
        text = (
            f"🛒 <b>Confirm Purchase</b>\n\n"
            f"Account: <b>{account['name']}</b>\n"
            f"Price: <b>{account['price']} {CURRENCY}</b>\n"
            f"Your balance: <b>{balance:.2f} {CURRENCY}</b>\n\n"
            f"Please enter your <b>Telegram username</b> or contact info:"
        )
        user_states[user_id] = {"step": "awaiting_contact", "account": account}
        await query.edit_message_text(text, parse_mode="HTML")
        return

    if data.startswith("confirm_"):
        return

    if data.startswith("paid_"):
        await query.edit_message_text("✅ Your deposit request has been submitted. Admin will verify and credit your balance.")
        return


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.message.chat_id
    text = update.message.text

    if not text or text.startswith("/"):
        return

    state = user_states.get(user_id)
    if not state:
        return

    if state["step"] == "awaiting_amount":
        try:
            amount = float(text)
            if amount < 5:
                await context.bot.send_message(chat_id, "❌ Minimum deposit is 5 USDT. Please enter a higher amount.")
                return
        except ValueError:
            await context.bot.send_message(chat_id, "❌ Invalid amount. Please enter a number (e.g. 20).")
            return

        deposit_text = (
            f"💳 <b>Deposit Instructions</b>\n\n"
            f"Amount: <b>{amount:.2f} {CURRENCY}</b>\n\n"
            f"Send exactly <b>{amount:.2f} {CURRENCY}</b> (TRC20) to:\n\n"
            f"<code>{USDT_WALLET}</code>\n\n"
            f"Your balance will be credited once payment is verified."
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ I Have Paid", callback_data=f"paid_{user_id}")],
            [InlineKeyboardButton("⬅️ Main Menu", callback_data="back_main")]
        ])
        await context.bot.send_message(chat_id, deposit_text, parse_mode="HTML", reply_markup=keyboard)
        del user_states[user_id]

        if ADMIN_ID:
            await context.bot.send_message(
                ADMIN_ID,
                f"💰 <b>New Deposit Request</b>\n\n"
                f"User ID: <code>{user_id}</code>\n"
                f"Amount: <b>{amount:.2f} {CURRENCY}</b>\n\n"
                f"Use: /addbalance {user_id} {amount:.2f} to credit the user after verification.",
                parse_mode="HTML"
            )
        return

    if state["step"] == "awaiting_contact":
        contact_info = text.strip()
        account = state["account"]
        balance = get_balance(user_id)

        if balance < account["price"]:
            await context.bot.send_message(chat_id, "❌ Insufficient balance. Please add funds.")
            del user_states[user_id]
            return

        deduct_balance(user_id, account["price"])
        order = create_order(user_id, contact_info, account, account["price"])
        new_balance = get_balance(user_id)

        text = (
            f"✅ <b>Purchase Successful!</b>\n\n"
            f"Order: <b>#{order['id']}</b>\n"
            f"Account: <b>{account['name']}</b>\n"
            f"Price: <b>{account['price']} {CURRENCY}</b>\n"
            f"Remaining balance: <b>{new_balance:.2f} {CURRENCY}</b>\n\n"
            f"We will deliver your account to <b>{contact_info}</b>.\n"
            f"Thank you for your purchase! 🎉"
        )
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Main Menu", callback_data="back_main")]])
        await context.bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=keyboard)
        del user_states[user_id]

        if ADMIN_ID:
            await context.bot.send_message(
                ADMIN_ID,
                f"🛒 <b>New Order!</b>\n\n"
                f"Order: #{order['id']}\n"
                f"User ID: <code>{user_id}</code>\n"
                f"Contact: {contact_info}\n"
                f"Account: {account['name']}\n"
                f"Price: {account['price']} {CURRENCY}\n\n"
                f"Deliver the account to the user.",
                parse_mode="HTML"
            )
        return


async def addbalance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized.")
        return

    if len(context.args) < 2:
        await update.message.reply_text("Usage: /addbalance <user_id> <amount>")
        return

    try:
        target_id = int(context.args[0])
        amount = float(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Invalid arguments. Usage: /addbalance <user_id> <amount>")
        return

    add_balance(target_id, amount)
    await update.message.reply_text(f"✅ Added {amount:.2f} {CURRENCY} to user <code>{target_id}</code>.", parse_mode="HTML")
    try:
        await context.bot.send_message(
            target_id,
            f"✅ <b>Balance Credited!</b>\n\n"
            f"Your wallet has been credited with <b>{amount:.2f} {CURRENCY}</b>.\n"
            f"New balance: <b>{get_balance(target_id):.2f} {CURRENCY}</b>",
            parse_mode="HTML"
        )
    except Exception:
        pass


async def balance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text(f"Your balance: {get_balance(user_id):.2f} {CURRENCY}")
        return

    if context.args:
        try:
            target_id = int(context.args[0])
            bal = get_balance(target_id)
            await update.message.reply_text(f"User <code>{target_id}</code> balance: <b>{bal:.2f} {CURRENCY}</b>", parse_mode="HTML")
        except ValueError:
            await update.message.reply_text("Usage: /balance [user_id]")
    else:
        await update.message.reply_text(f"Your balance: {get_balance(user_id):.2f} {CURRENCY}")


def main():
    if not BOT_TOKEN:
        print("ERROR: BOT_TOKEN environment variable is not set")
        return
    if not USDT_WALLET:
        print("ERROR: USDT_WALLET environment variable is not set")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addbalance", addbalance))
    app.add_handler(CommandHandler("balance", balance_cmd))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Reddit Accounts Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
