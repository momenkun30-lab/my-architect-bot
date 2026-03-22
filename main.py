import telebot
from telebot import types
import random
import string
from flask import Flask, request
from pymongo import MongoClient

# --- الإعدادات الخاصة بك ---
API_TOKEN = '8070560190:AAFjbU4sfFLjS77uE4X_csCG-T71za3eAvg'
ADMIN_ID = 8305841557
MONGO_URI = 'mongodb+srv://mfasd94_db_user:umLYtGDdobe1HGBt@cluster0.ss2d7fa.mongodb.net/?appName=Cluster0'
# ⚠️ ملاحظة: استبدل 'your-app-name' برابط Render الذي ستحصل عليه لاحقاً
WEBHOOK_URL = 'https://your-app-name.onrender.com/' 

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# --- الاتصال بـ MongoDB ---
client = MongoClient(MONGO_URI)
db = client['bot_database']
users_col = db['users']
vip_codes_col = db['vip_codes']
vip_users_col = db['vip_users']

# --- وظائف مساعدة ---
def generate_random_code(length=10):
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def main_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('🔢 الأرقام الفيك', '💻 أدوات Termux/Python')
    markup.add('📚 قسم الشروحات', '💎 قسم VIP')
    markup.add('👨‍💻 المطور')
    return markup

# --- الأوامر الأساسية ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    users_col.update_one({'id': user_id}, {'$set': {'id': user_id}}, upsert=True)
    
    welcome_text = "─── ❖ ── ✦ ── ❖ ───\n🌐 **ARCHITECT OS v3.0 ONLINE**\n─── ❖ ── ✦ ── ❖ ───\n\nمرحباً بك في النظام المركزي.\nتم التوصيل بقاعدة البيانات السحابية... ✅"
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_markup(), parse_mode="Markdown")

# --- نظام الإذاعة (Broadcast) ---
@bot.callback_query_handler(func=lambda call: call.data == "broadcast")
def broadcast_init(call):
    if call.from_user.id == ADMIN_ID:
        msg = bot.send_message(call.message.chat.id, "📢 أرسل الرسالة التي تريد إذاعتها (نص، صورة، فيديو، ملف):")
        bot.register_next_step_handler(msg, broadcast_execute)

def broadcast_execute(message):
    all_users = users_col.find({})
    count = 0
    fail = 0
    
    bot.send_message(ADMIN_ID, "⏳ جاري بدء عملية الإذاعة العالمية...")
    
    for user in all_users:
        try:
            bot.copy_message(user['id'], message.chat.id, message.message_id)
            count += 1
        except:
            fail += 1
            
    bot.send_message(ADMIN_ID, f"✅ اكتملت الإذاعة!\n\n📈 تم الإرسال لـ: {count}\n❌ فشل الإرسال لـ: {fail}")

# --- نظام VIP ---
@bot.message_handler(func=lambda m: m.text == '💎 قسم VIP')
def vip_access(message):
    user_id = message.from_user.id
    if vip_users_col.find_one({'user_id': user_id}):
        bot.send_message(message.chat.id, "🔥 مرحباً بك في المحتوى الحصري VIP.")
    else:
        msg = bot.send_message(message.chat.id, "🔐 القسم مشفر. أدخل كود الوصول:")
        bot.register_next_step_handler(msg, process_vip)

def process_vip(message):
    code = message.text.strip()
    valid = vip_codes_col.find_one({'code': code, 'used': 0})
    if valid:
        vip_codes_col.update_one({'code': code}, {'$set': {'used': 1}})
        vip_users_col.insert_one({'user_id': message.from_user.id})
        bot.send_message(message.chat.id, "✅ تم تفعيل العضوية بنجاح.")
    else:
        bot.send_message(message.chat.id, "❌ الكود غير صحيح.")

# --- لوحة التحكم ---
@bot.message_handler(commands=['admin'])
def admin(message):
    if message.from_user.id == ADMIN_ID:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💎 توليد كود VIP", callback_data="gen_vip"))
        markup.add(types.InlineKeyboardButton("📢 إذاعة جماعية", callback_data="broadcast"))
        markup.add(types.InlineKeyboardButton("📊 إحصائيات", callback_data="stats"))
        bot.send_message(message.chat.id, "👑 لوحة تحكم القائد:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    if call.from_user.id == ADMIN_ID:
        if call.data == "gen_vip":
            code = generate_random_code()
            vip_codes_col.insert_one({'code': code, 'used': 0})
            bot.send_message(ADMIN_ID, f"✅ كود جديد:\n`{code}`", parse_mode="Markdown")
        elif call.data == "stats":
            count = users_col.count_documents({})
            bot.answer_callback_query(call.id, f"عدد المستخدمين: {count}", show_alert=True)

# --- Flask Webhook ---
@app.route('/', methods=['GET'])
def home(): return "SYSTEM ONLINE ✅"

@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_str = request.get_data().decode('UTF-8')
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return "OK", 200
    return "Forbidden", 403

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=10000)
