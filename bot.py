from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import sqlite3
import config

db = sqlite3.connect("database.db", check_same_thread=False)
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY,
    balance INTEGER DEFAULT 0
)
""")

keyboard = [
    ["💳 Add Balance", "🛒 Buy ID"],
    ["💰 Balance", "📞 Admin"]
]
markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    cursor.execute("INSERT OR IGNORE INTO users(id) VALUES(?)", (uid,))
    db.commit()
    
    await update.message.reply_text(
        "🔥 Welcome to Gaming ID Shop Bot",
        reply_markup=markup
    )

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text
    uid = update.message.from_user.id

    if msg == "💰 Balance":
        cursor.execute("SELECT balance FROM users WHERE id=?", (uid,))
        bal = cursor.fetchone()[0]
        await update.message.reply_text(f"Your Balance: ₹{bal}")

    elif msg == "💳 Add Balance":
        await update.message.reply_text(
            f"Send payment to UPI:\n{config.UPI_ID}\n\nThen send screenshot."
        )

    elif msg == "🛒 Buy ID":
        price = 300
        cursor.execute("SELECT balance FROM users WHERE id=?", (uid,))
        bal = cursor.fetchone()[0]

        if bal < price:
            await update.message.reply_text("❌ Balance low")
            return

        cursor.execute("UPDATE users SET balance=balance-? WHERE id=?", (price, uid))
        db.commit()

        with open("ids.txt") as f:
            ids = [line.strip() for line in f.readlines()]

        if not ids:
            await update.message.reply_text("❌ Out of stock")
            return

        send_id = ids[0]

        with open("ids.txt", "w") as f:
            f.writelines(f"{i}\n" for i in ids[1:])

        await update.message.reply_text(f"✅ Your ID:\n{send_id}")

app = ApplicationBuilder().token(config.BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT, menu))

app.run_polling()







