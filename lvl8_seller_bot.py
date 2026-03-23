import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import psycopg2
from psycopg2.extras import RealDictCursor
import time
import requests
import uuid
from datetime import datetime
import urllib.parse
from flask import Flask
import threading
import os
import schedule
import time

# ================= CONFIGURATION =================
TOKEN = '8679506198:AAFbuNw_R0D1CO5BSSkDTqhwClceZtTuGhk'
ADMIN_ID = 6347273583
ADMIN_USER = '@Mohit_modz'
SAFE_ADMIN = ADMIN_USER.replace('_', '\\_')
SUPPORT_CHANNEL = '@support'
UPI_ID = 'paytm.slsdhpu@p'
UPIGATEWAY_KEY = '61063d-a23876-6c09b9-bf46c0-0f8ff2' # Aapka UPIGateway API key
# Supabase - PostgreSQL URI (Password supra@ultimat encoded as supra%40ultimat)
DB_URL = 'postgresql://postgres:supra%40ultimat@db.opseljsvrnclsohcsqiq.supabase.co:6543/postgres'
DB_NAME = 'seller_bot.db' # Legacy name, now using DB_URL

bot = telebot.TeleBot(TOKEN)

# ================= DATABASE =================
def get_db():
    conn = psycopg2.connect(DB_URL)
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (user_id BIGINT PRIMARY KEY, balance INTEGER DEFAULT 0)')
    c.execute('CREATE TABLE IF NOT EXISTS admins (user_id BIGINT PRIMARY KEY)')
    c.execute('CREATE TABLE IF NOT EXISTS inventory (id SERIAL PRIMARY KEY, category TEXT, price INTEGER, login_details TEXT, status TEXT DEFAULT \'AVAILABLE\')')
    c.execute('CREATE TABLE IF NOT EXISTS transactions (client_txn_id TEXT PRIMARY KEY, user_id BIGINT, amount INTEGER, date TEXT, status TEXT DEFAULT \'PENDING\')')
    conn.commit()
    c.close()
    conn.close()

init_db()

def is_admin(user_id):
    if user_id == ADMIN_ID: return True
    conn = get_db()
    c = conn.cursor(cursor_factory=RealDictCursor)
    c.execute('SELECT 1 FROM admins WHERE user_id=%s', (user_id,))
    res = c.fetchone()
    c.close()
    conn.close()
    return bool(res)

def get_balance(user_id):
    conn = get_db()
    c = conn.cursor(cursor_factory=RealDictCursor)
    c.execute('SELECT balance FROM users WHERE user_id=%s', (user_id,))
    res = c.fetchone()
    c.close()
    conn.close()
    return res['balance'] if res else 0

def update_balance(user_id, amount):
    conn = get_db()
    c = conn.cursor()
    c.execute('UPDATE users SET balance = balance + %s WHERE user_id = %s', (amount, user_id))
    conn.commit()
    c.close()
    conn.close()

# ================= MAIN MENU =================
def main_menu(user_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton('ADD FUNDS')
    )
    markup.add(
        KeyboardButton('FACEBOOK ID'),
        KeyboardButton('GOOGLE ID')
    )
    markup.add(
        KeyboardButton('📦 STOCK'),
        KeyboardButton('MY BALANCE')
    )
    markup.add(
        KeyboardButton('How To Use'),
        KeyboardButton('40lv+ 125 star')
    )
    if is_admin(user_id):
        markup.add(KeyboardButton('🛠 Admin Panel'))
    return markup

@bot.message_handler(commands=['start'])
def start_msg(message):
    user_id = message.from_user.id
    conn = get_db()
    c = conn.cursor()
    c.execute('INSERT INTO users (user_id, balance) VALUES (%s, 0) ON CONFLICT (user_id) DO NOTHING', (user_id,))
    conn.commit()
    c.close()
    conn.close()
    name = message.from_user.first_name if message.from_user.first_name else "User"
    start_text = (
        f"👋 HELLO {name}!\n\n"
        "WELCOME TO MOHIT MODZ ID STORE\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚡ FAST & TRUSTED SERVICE\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "NICHE DIYE GAYE BUTTONS SE SELECT KAREIN:"
    )
    bot.send_message(message.chat.id, start_text, reply_markup=main_menu(user_id))

@bot.message_handler(func=lambda m: m.text == 'MY BALANCE')
def balance_cmd(message):
    bal = get_balance(message.from_user.id)
    bot.send_message(message.chat.id, f"✅ BALANCE FETCHED\n\nYOUR BALANCE IS :- ₹{bal}\n\n❤️CONTACT {ADMIN_USER} TO ADD FUNDS MANUALLY")

@bot.message_handler(func=lambda m: m.text == 'How To Use')
def how_to_use_cmd(message):
    text = (
        "👋 **BOT KO KAISE USE KAREIN (GUIDE)**\n\n"
        "Bhai, bot use karna bohot hi aasaan hai! Bas ye steps follow karo:\n\n"
        "1️⃣ **BALANCE ADD KAREIN:** Sabse pehle `ADD FUNDS` par click karein aur jitne paise add karne hain wo likhein (min ₹1). QR code generate hoga, uspar pay karke `CHECK ✅` button dabayein.\n\n"
        "2️⃣ **CATEGORY CHUNEIN:** Recharge hone ke baad `FACEBOOK ID` ya `GOOGLE ID` wale button par click karein.\n\n"
        "3️⃣ **QUANTITY SELECT KAREIN:** Aapko buttons dikhenge jaise `F-BUY 1`, `F-BUY 2` wagairah. Aapko ek saath jitni IDs chahiye, utne number wale button ko select karein.\n\n"
        "4️⃣ **ID DELIVERY:** Jaise hi aap button dabayenge, bot aapke paise kaat lega aur turant aapko **Login Emails & Passwords** isi chat mein bhej dega!\n\n"
        "⚠️ **DHYAN RAKHEIN:** Login karne ke baad agar koi dikkaat aaye toh turant owner @Mohit\\_modz ko contact karein."
    )
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text == '📦 STOCK')
def stock_cmd(message):
    conn = get_db()
    c = conn.cursor(cursor_factory=RealDictCursor)
    c.execute("SELECT count(*) as c FROM inventory WHERE category='FB' AND status='AVAILABLE'")
    fb_c = c.fetchone()['c']
    c.execute("SELECT count(*) as c FROM inventory WHERE category='GOOGLE' AND status='AVAILABLE'")
    g_c = c.fetchone()['c']
    c.execute("SELECT count(*) as c FROM inventory WHERE category='LEVEL40' AND status='AVAILABLE'")
    lv40_c = c.fetchone()['c']
    c.close()
    conn.close()
    bot.send_message(message.chat.id, f"▶ *AVAILABLE STOCK* ◀\n\n`📄 FACEBOOK ACCOUNTS ▶ {fb_c}`\n\n`📄 GOOGLE ACCOUNTS  ▶ {g_c}`\n\n`⭐ 40LV+ 125 STAR   ▶ {lv40_c}`", parse_mode='Markdown')

# ================= 100% AUTO PAYMENT =================

@bot.message_handler(func=lambda m: m.text == 'ADD FUNDS')
def add_funds_cmd(message):
    msg = bot.send_message(message.chat.id, "💰 *Enter amount to Add in Wallet in INR ₹ (Min ₹1)*:\nSend just the number (e.g. 50):", parse_mode='Markdown')
    bot.register_next_step_handler(msg, generate_payment)

def generate_payment(message):
    try:
        amount = int(message.text)
        if amount < 1:
            return bot.send_message(message.chat.id, "❌ Minimum add money limit is ₹1. Try again by clicking ADD FUNDS.")
        
        bot.send_message(message.chat.id, "PLEASE WAIT.. GENERATING API QR 🧑‍💻👨‍💻")
        
        client_txn_id = f"ORDER_{message.from_user.id}_{int(time.time())}"
        date_str = datetime.now().strftime("%d-%m-%Y")
        
        url = "https://allapi.in/order/create"
        data = {
            "token": UPIGATEWAY_KEY,
            "order_id": client_txn_id,
            "txn_amount": amount,
            "txn_note": "Wallet Recharge",
            "product_name": "Wallet Recharge",
            "customer_name": message.from_user.first_name[:15] if message.from_user.first_name else "User",
            "customer_mobile": "9999999999",
            "customer_email": "botuser@gmail.com",
            "redirect_url": "https://google.com"
        }
        res = requests.post(url, json=data).json()
        
        if res.get('status') == True:
            # Direct UPI intent URL
            bhim_link = res['results']['upi_intent']['bhim']
            safe_link = urllib.parse.quote_plus(bhim_link)
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={safe_link}"
            
            conn = get_db()
            c = conn.cursor()
            c.execute('INSERT INTO transactions (client_txn_id, user_id, amount, date) VALUES (%s, %s, %s, %s)', (client_txn_id, message.from_user.id, amount, date_str))
            conn.commit()
            c.close()
            conn.close()

            caption = f"PAY ON THIS QR AND CLICK CHECK ✅ TO ADD YOUR BALANCE ✅\n\n🎯 *Amount to Pay:* ₹{amount}\n🧾 *Order ID:* `{client_txn_id}`\n\nइस QR पर ठीक ₹{amount} भुगतान करें और अपना पैसा जोड़ने के लिए Check ✅ पर क्लिक करें ✅"
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("✅ CHECK PAYMENT ✅", callback_data=f"auto_check_{client_txn_id}"))
            
            bot.send_photo(message.chat.id, qr_url, caption=caption, reply_markup=markup, parse_mode='Markdown')
        else:
            bot.send_message(message.chat.id, f"❌ Gateway API Error: {res.get('message', 'N/A')}\nAsk Admin to check their account.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Validation Error: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('auto_check_'))
def handle_auto_check(call):
    client_txn_id = call.data.replace('auto_check_', '')
    user_id = call.from_user.id
    
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM transactions WHERE client_txn_id=?', (client_txn_id,))
    txn = c.fetchone()
    
    if not txn:
        bot.answer_callback_query(call.id, "❌ Invalid Order ID!", show_alert=True)
        return conn.close()
        
    if txn['status'] == 'SUCCESS':
        bot.answer_callback_query(call.id, "✅ This payment is already claimed!", show_alert=True)
        return conn.close()
        
    date_str = txn['date']
    amount = txn['amount']
    
    url = "https://allapi.in/order/status"
    data = {
        "token": UPIGATEWAY_KEY,
        "order_id": client_txn_id
    }
    
    try:
        res = requests.post(url, json=data).json()
        if res.get('status') == True:
            api_status = str(res.get('results', {}).get('status', 'PENDING')).upper()
            if api_status in ['COMPLETED', 'SUCCESS', 'PAID']:
                c.execute('UPDATE users SET balance = balance + ? WHERE user_id=?', (amount, user_id))
                c.execute('UPDATE transactions SET status="SUCCESS" WHERE client_txn_id=?', (client_txn_id,))
                conn.commit()
                bot.send_message(call.message.chat.id, f"🎉 *AUTOMATIC SUCCESS!*\n₹{amount} has been added to your wallet automatically!", parse_mode='Markdown')
                
                # Safe markdown for admin notification
                raw_name = call.from_user.username if call.from_user.username else call.from_user.first_name
                safe_name = str(raw_name).replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace('`', '\\`')
                admin_name = f"@{safe_name}" if call.from_user.username else safe_name
                bot.send_message(ADMIN_ID, f"💰 *AUTO PAYMENT RECEIVED*\nUser {admin_name} (`{user_id}`) has added ₹{amount} via Payment Gateway. Wallet updated safely.", parse_mode='Markdown')
            else:
                bot.answer_callback_query(call.id, "⏳ Payment status is PENDING/FAILED! If you just paid, wait 1 minute & click CHECK again.", show_alert=True)
        else:
            bot.answer_callback_query(call.id, "⚠️ Payment NOT FOUND! Scan the QR and pay exact amount first.", show_alert=True)
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Gateway error: {e}", show_alert=True)
    conn.close()

# ================= BUY IDs =================
@bot.message_handler(func=lambda m: m.text in ['FACEBOOK ID', 'GOOGLE ID', '40lv+ 125 star'])
def show_ids(message):
    if message.text == 'FACEBOOK ID': cat = 'FB'
    elif message.text == 'GOOGLE ID': cat = 'GOOGLE'
    else: cat = 'LEVEL40'
    conn = get_db()
    c = conn.cursor(cursor_factory=RealDictCursor)
    c.execute('SELECT id, price FROM inventory WHERE category=%s AND status=%s', (cat, 'AVAILABLE'))
    items = c.fetchall()
    c.close()
    conn.close()
    
    if not items:
        bot.reply_to(message, f"😔 NO {message.text} STOCK AVAILABLE.", reply_markup=main_menu(message.from_user.id))
        return

    sample_price = items[0]['price']
    stock_count = len(items)
    text = f"▶ *{message.text}* ◀\n\n💰 *PRICE PER ID :-* ₹{sample_price}\n📦 *AVAILABLE STOCK:* {stock_count}\n\nChoose the number of IDs you want to buy at once:\n*(Max 5 at a time)*\n\nBUY ID AND DM FOR LOGIN APPROVAL {SAFE_ADMIN}"
    
    markup = InlineKeyboardMarkup(row_width=3)
    buttons = []
    max_buy = min(5, stock_count)
    if cat == 'FB': prefix = 'F-BUY'
    elif cat == 'GOOGLE': prefix = 'G-BUY'
    else: prefix = 'L-BUY'
    
    for qty in range(1, max_buy + 1):
        buttons.append(InlineKeyboardButton(f"{prefix} {qty}", callback_data=f"buy_{cat}_{qty}"))
    
    markup.add(*buttons)
    markup.row(InlineKeyboardButton("🚪 Exit", callback_data="exit_menu"))
    bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
def handle_buy_confirm(call):
    parts = call.data.split('_')
    cat = parts[1]
    qty = int(parts[2])
    user_id = call.from_user.id
    
    conn = get_db()
    c = conn.cursor(cursor_factory=RealDictCursor)
    c.execute('SELECT id, login_details, price FROM inventory WHERE category=%s AND status=%s LIMIT %s', (cat, 'AVAILABLE', qty))
    itemsToBuy = c.fetchall()
    
    if len(itemsToBuy) < qty:
        bot.answer_callback_query(call.id, f"Sorry, only {len(itemsToBuy)} IDs left in stock!", show_alert=True)
        return conn.close()
        
    total_price = sum(item['price'] for item in itemsToBuy)
    bal = get_balance(user_id)
    
    if bal < total_price:
        bot.answer_callback_query(call.id, f"Insufficient Balance! You need ₹{total_price} but have ₹{bal}.", show_alert=True)
        return conn.close()
        
    c.execute('UPDATE users SET balance = balance - %s WHERE user_id=%s', (total_price, user_id))
    
    delivery_text = ""
    for item in itemsToBuy:
        c.execute('UPDATE inventory SET status=%s WHERE id=%s', ('SOLD', item['id']))
        delivery_text += f"`{item['login_details']}`\n"
        
    conn.commit()
    c.close()
    conn.close()

    bot.answer_callback_query(call.id, f"✅ Bought {qty} IDs successfully!", show_alert=False)
    delivery = f"🎉 *AUTO ID DELIVERY SUCCESS!* ({qty}x)\n\n📂 *Type:* {cat} ID\n💵 *Total Deducted:* ₹{total_price}\n\n🔐 *LOGIN DETAILS:*\n{delivery_text}\nThanks for purchasing! DM owner for Login Approval."
    bot.send_message(call.message.chat.id, delivery, parse_mode='Markdown')
    
    raw_name = call.from_user.username if call.from_user.username else call.from_user.first_name
    safe_name = str(raw_name).replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace('`', '\\`')
    admin_name = f"@{safe_name}" if call.from_user.username else safe_name
    bot.send_message(ADMIN_ID, f"🛒 *NEW SALE!*\nUser {admin_name} (`{user_id}`) has auto-bought {qty}x {cat} Accounts for ₹{total_price}.", parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data == 'exit_menu')
def handle_exit(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    bot.send_message(call.message.chat.id, "🚪 Exit\nEXITED SUCCESSFULLY", reply_markup=main_menu(call.from_user.id))

# ================= ADMIN PANEL =================
@bot.message_handler(func=lambda m: m.text == '🛠 Admin Panel' and is_admin(m.from_user.id))
def admin_panel(message):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(InlineKeyboardButton("➕ Add FB ID", callback_data="admin_add_fb"), InlineKeyboardButton("➕ Add Google ID", callback_data="admin_add_g"))
    markup.add(InlineKeyboardButton("➕ Add 40lv+ 125 star", callback_data="admin_add_lv40"))
    markup.add(InlineKeyboardButton("📦 Bulk Add FB/Google", callback_data="admin_bulk_add"))
    markup.add(InlineKeyboardButton("📢 Broadcast Msg", callback_data="admin_broadcast"), InlineKeyboardButton("💰 Add User Balance", callback_data="admin_add_bal_btn"))
    markup.add(InlineKeyboardButton("📝 Manage Inventory", callback_data="admin_manage_inv"))
    if message.from_user.id == ADMIN_ID:
        markup.add(InlineKeyboardButton("👑 Add Admin", callback_data="owner_add_admin"), InlineKeyboardButton("🗑 Remove Admin", callback_data="owner_rem_admin"))
    bot.send_message(message.chat.id, "🛠 *Admin Panel*", parse_mode='Markdown', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'owner_add_admin' and call.from_user.id == ADMIN_ID)
def add_admin_start(call):
    msg = bot.send_message(call.message.chat.id, "Send the Target User ID to promote to Admin:")
    bot.register_next_step_handler(msg, process_add_admin)

def process_add_admin(message):
    try:
        uid = int(message.text)
        conn = get_db()
        c = conn.cursor()
        c.execute('INSERT INTO admins (user_id) VALUES (%s) ON CONFLICT (user_id) DO NOTHING', (uid,))
        conn.commit()
        c.close()
        conn.close()
        bot.send_message(message.chat.id, f"✅ User {uid} is now an Admin!")
        try: bot.send_message(uid, "🎉 You have been promoted to ADMIN! Send /start to refresh your menu.")
        except: pass
    except:
        bot.send_message(message.chat.id, "❌ Invalid ID!")

@bot.callback_query_handler(func=lambda call: call.data == 'owner_rem_admin' and call.from_user.id == ADMIN_ID)
def rem_admin_start(call):
    msg = bot.send_message(call.message.chat.id, "Send the User ID to Remove from Admins:")
    bot.register_next_step_handler(msg, process_rem_admin)

def process_rem_admin(message):
    try:
        uid = int(message.text)
        conn = get_db()
        conn.cursor().execute('DELETE FROM admins WHERE user_id=?', (uid,))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, f"✅ User {uid} removed from admins.")
    except:
        bot.send_message(message.chat.id, "❌ Invalid ID!")

@bot.callback_query_handler(func=lambda call: call.data == 'admin_manage_inv' and is_admin(call.from_user.id))
def manage_inv_start(call):
    conn = get_db()
    c = conn.cursor(cursor_factory=RealDictCursor)
    c.execute('SELECT id, category, login_details FROM inventory WHERE status=%s ORDER BY id DESC LIMIT 20', ('AVAILABLE',))
    items = c.fetchall()
    c.close()
    conn.close()
    
    if not items:
        return bot.answer_callback_query(call.id, "📂 No items in inventory!", show_alert=True)
        
    for item in items:
        short_login = item['login_details'][:50] + "..." if len(item['login_details']) > 50 else item['login_details']
        text = f"🆔 **DB ID:** `{item['id']}`\n📂 **Cat:** {item['category']}\n🔐 **Details:** `{short_login}`"
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(f"❌ DELETE ID {item['id']}", callback_data=f"admin_delete_inv_{item['id']}"))
        bot.send_message(call.message.chat.id, text, parse_mode='Markdown', reply_markup=markup)
    
    bot.send_message(call.message.chat.id, "✅ Listed last 20 IDs. Click ❌ to remove any.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_delete_inv_') and is_admin(call.from_user.id))
def handle_delete_inv(call):
    inv_id = call.data.replace('admin_delete_inv_', '')
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM inventory WHERE id=%s', (inv_id,))
    conn.commit()
    c.close()
    conn.close()
    bot.answer_callback_query(call.id, f"✅ ID {inv_id} DELETED!", show_alert=True)
    bot.delete_message(call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data in ['admin_add_fb', 'admin_add_g', 'admin_add_lv40'] and is_admin(call.from_user.id))
def add_id_start(call):
    if call.data == 'admin_add_fb': cat = 'FB'
    elif call.data == 'admin_add_g': cat = 'GOOGLE'
    else: cat = 'LEVEL40'
    
    if cat == 'LEVEL40':
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Facebook Type", callback_data="lv40_type_FB"), InlineKeyboardButton("Google Type", callback_data="lv40_type_GOOGLE"))
        bot.send_message(call.message.chat.id, "Select Login Type for this Level 40 ID:", reply_markup=markup)
    else:
        msg = bot.send_message(call.message.chat.id, f"Send Login Details for {cat} ID (e.g. Email/Pass):")
        bot.register_next_step_handler(msg, process_add_id_login, cat)

@bot.callback_query_handler(func=lambda call: call.data.startswith('lv40_type_'))
def handle_lv40_type(call):
    login_type = call.data.replace('lv40_type_', '')
    msg = bot.send_message(call.message.chat.id, f"Send Login Details for {login_type} (Level 40 ID):")
    bot.register_next_step_handler(msg, process_add_id_login, 'LEVEL40', login_type)

def process_add_id_login(message, cat, login_type=None):
    if message.text == '/cancel': return
    final_login = f"[{login_type}] {message.text}" if login_type else message.text
    msg = bot.send_message(message.chat.id, "Enter Price for this ID (Number only):")
    bot.register_next_step_handler(msg, process_add_id_price, cat, final_login)

def process_add_id_price(message, cat, login):
    try:
        price = int(message.text)
        conn = get_db()
        c = conn.cursor()
        c.execute('INSERT INTO inventory (category, price, login_details, status) VALUES (%s, %s, %s, %s)', (cat, price, login, 'AVAILABLE'))
        conn.commit()
        c.close()
        conn.close()
        bot.send_message(message.chat.id, f"✅ Successfully added 1 {cat} ID for ₹{price} to stock.")
    except:
        bot.send_message(message.chat.id, "❌ Valid Number required for Price!")

@bot.callback_query_handler(func=lambda call: call.data == 'admin_bulk_add' and is_admin(call.from_user.id))
def bulk_id_start(call):
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(KeyboardButton("FB"), KeyboardButton("GOOGLE"), KeyboardButton("LEVEL40"))
    msg = bot.send_message(call.message.chat.id, "📝 Select Category for Bulk Add:", reply_markup=markup)
    bot.register_next_step_handler(msg, process_bulk_cat)

def process_bulk_cat(message):
    if message.text not in ["FB", "GOOGLE", "LEVEL40"]:
        return bot.send_message(message.chat.id, "❌ Cancelled. Invalid Category.", reply_markup=main_menu(message.from_user.id))
    cat = message.text
    msg = bot.send_message(message.chat.id, f"📥 Send ALL `{cat}` Usernames/Emails/Numbers (One per line):\n\nExample:\nuser1@gmail.com\nuser2\n12345678", parse_mode='Markdown', reply_markup=telebot.types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, process_bulk_emails, cat)

def process_bulk_emails(message, cat):
    emails = [line.strip() for line in message.text.split('\n') if line.strip()]
    if not emails:
        return bot.send_message(message.chat.id, "❌ No emails found. Cancelled.", reply_markup=main_menu(message.from_user.id))
    msg = bot.send_message(message.chat.id, f"🔑 Send the COMMON PASSWORD for all these {len(emails)} IDs:")
    bot.register_next_step_handler(msg, process_bulk_password, cat, emails)

def process_bulk_password(message, cat, emails):
    password = message.text.strip()
    msg = bot.send_message(message.chat.id, f"💰 Enter Selling Price for EACH of these IDs (e.g., 50):")
    bot.register_next_step_handler(msg, process_bulk_price_final, cat, emails, password)

def process_bulk_price_final(message, cat, emails, password):
    try:
        price = int(message.text)
        conn = get_db()
        c = conn.cursor()
        for email in emails:
            login_details = f"{email} | Password: {password}"
            c.execute('INSERT INTO inventory (category, price, login_details, status) VALUES (%s, %s, %s, %s)', (cat, price, login_details, 'AVAILABLE'))
        conn.commit()
        c.close()
        conn.close()
        bot.send_message(message.chat.id, f"🎉 Successfully Bulk Added {len(emails)} {cat} IDs to stock at ₹{price} each!", reply_markup=main_menu(message.from_user.id))
    except Exception as e:
        bot.send_message(message.chat.id, "❌ Invalid Number! Bulk Add Cancelled.", reply_markup=main_menu(message.from_user.id))

@bot.callback_query_handler(func=lambda call: call.data == 'admin_broadcast' and is_admin(call.from_user.id))
def broadcast_start(call):
    msg = bot.send_message(call.message.chat.id, "Send message you want to Broadcast:")
    bot.register_next_step_handler(msg, process_broadcast)

def process_broadcast(message):
    conn = get_db()
    c = conn.cursor(cursor_factory=RealDictCursor)
    c.execute('SELECT user_id FROM users')
    users = c.fetchall()
    c.close()
    conn.close()
    count = 0
    bot.send_message(message.chat.id, "Broadcasting...")
    for u in users:
        try:
            bot.send_message(u['user_id'], message.text)
            count += 1
        except: pass
    bot.send_message(message.chat.id, f"✅ Broadcast sent to {count} users!")

@bot.callback_query_handler(func=lambda call: call.data == 'admin_add_bal_btn' and is_admin(call.from_user.id))
def addbal_start(call):
    msg = bot.send_message(call.message.chat.id, "Send Target User ID:")
    bot.register_next_step_handler(msg, process_addbal_uid)

def process_addbal_uid(message):
    msg = bot.send_message(message.chat.id, f"Enter amount to add for {message.text}:")
    bot.register_next_step_handler(msg, process_addbal_amount, message.text)

def process_addbal_amount(message, uid):
    try:
        amt = int(message.text)
        update_balance(uid, amt)
        bot.send_message(message.chat.id, f"✅ Added ₹{amt} to User {uid}.")
        try: bot.send_message(uid, f"💳 Your wallet has been credited with ₹{amt} by Admin!")
        except: pass
    except:
        bot.send_message(message.chat.id, "Error in Add Balance. Send a valid numeric value.")

# ================= BACKUP SYSTEM =================
import json

def send_backup():
    try:
        conn = get_db()
        c = conn.cursor(cursor_factory=RealDictCursor)
        # Backup Users and Inventory
        c.execute('SELECT * FROM users')
        users = c.fetchall()
        c.execute('SELECT * FROM inventory')
        inv = c.fetchall()
        c.close()
        conn.close()

        backup_data = {"users": users, "inventory": inv, "timestamp": str(datetime.now())}
        with open("backup.json", "w") as f:
            json.dump(backup_data, f, indent=4)
        
        with open("backup.json", "rb") as f:
            bot.send_document(ADMIN_ID, f, caption=f"☁️ CLOUD DB AUTO-BACKUP (JSON)\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("Cloud Backup sent successfully!")
    except Exception as e:
        print(f"Backup failed: {e}")

@bot.message_handler(commands=['backup'])
def manual_backup(message):
    if is_admin(message.from_user.id):
        bot.reply_to(message, "⏳ Generating Cloud Database Backup...")
        send_backup()

def run_scheduler():
    # Schedule backup every 24 hours
    schedule.every(24).hours.do(send_backup)
    while True:
        schedule.run_pending()
        time.sleep(60)

# ================= RENDER KEEP-ALIVE =================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Alive!"

def run_flask():
    # Use port 8080 or the one provided by Render
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def start_keep_alive():
    # Start Flask
    t1 = threading.Thread(target=run_flask)
    t1.start()
    # Start Scheduler
    t2 = threading.Thread(target=run_scheduler)
    t2.start()

start_keep_alive()

print("Starting True Auto-Pay Bot...")
# Clear webhook and any pending updates to force restart on cloud
bot.delete_webhook(drop_pending_updates=True)
while True:
    try:
        bot.polling(none_stop=True, timeout=60, long_polling_timeout=60)
    except Exception as e:
        print(f"Network Error: {e}")
        time.sleep(5)
