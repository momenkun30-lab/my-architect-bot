import telebot
from telebot import types
from flask import Flask, request
from pymongo import MongoClient

# --- الإعدادات المركزية ---
API_TOKEN = '8070560190:AAFjbU4sfFLjS77uE4X_csCG-T71za3eAvg'
ADMIN_ID = 8305841557
MONGO_URI = 'mongodb+srv://mfasd94_db_user:umLYtGDdobe1HGBt@cluster0.ss2d7fa.mongodb.net/?appName=Cluster0'
WEBHOOK_URL = 'https://my-architect-bot-1.onrender.com/' 

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# --- ربط قاعدة البيانات ---
client = MongoClient(MONGO_URI)
db = client['bot_database']
users_col = db['users']
content_col = db['dynamic_content'] # المجموعة الخاصة بمحتواك (ترمكس، بايثون، إلخ)

# --- لوحة المفاتيح الرئيسية ---
def main_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('🔢 قسم الأرقام', '💻 أدوات الترمكس')
    markup.add('🐍 دروس بايثون', '📚 شروحات تقنية')
    markup.add('💎 قسم VIP', '👨‍💻 المطور')
    return markup

# --- الأوامر الأساسية ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    users_col.update_one({'id': user_id}, {'$set': {'id': user_id}}, upsert=True)
    
    welcome = "─── ❖ ── ✦ ── ❖ ───\n🌐 **ARCHITECT OS v4.0 ONLINE**\n─── ❖ ── ✦ ── ❖ ───\n\nنظام الإدارة المركزية جاهز للعمل.\nجميع الأقسام مرتبطة بقاعدة البيانات السحابية ✅"
    bot.send_message(message.chat.id, welcome, reply_markup=main_markup(), parse_mode="Markdown")

# --- عرض المحتوى ديناميكياً من القاعدة ---
@bot.message_handler(func=lambda m: m.text in ['🔢 قسم الأرقام', '💻 أدوات الترمكس', '🐍 دروس بايثون', '📚 شروحات تقنية'])
def get_content(message):
    category = message.text
    items = content_col.find({'category': category})
    
    response = f"📂 **محتوى {category}:**\n"
    response += "──────────────────\n\n"
    
    found = False
    for item in items:
        response += f"🔹 **{item['name']}**\n`{item['details']}`\n\n"
        found = True
    
    if not found:
        response += "⚠️ لا يوجد محتوى مضاف حالياً. القائد سيعمل على الإضافة قريباً."
    
    bot.send_message(message.chat.id, response, parse_mode="Markdown")

# --- لوحة التحكم (للقائد فقط) ---
@bot.message_handler(commands=['admin'])
def admin(message):
    if message.from_user.id == ADMIN_ID:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("➕ إضافة أداة/محتوى", callback_data="add_item"))
        markup.add(types.InlineKeyboardButton("📢 إذاعة عامة", callback_data="broadcast"))
        markup.add(types.InlineKeyboardButton("📊 الإحصائيات", callback_data="stats"))
        bot.send_message(message.chat.id, "👑 **أهلاً بك يا مصمم النظام**\nيمكنك التحكم في المحتوى من هنا:", reply_markup=markup, parse_mode="Markdown")

# --- نظام إضافة المحتوى (Step-by-Step) ---
@bot.callback_query_handler(func=lambda call: call.data == "add_item")
def add_item_start(call):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add('🔢 قسم الأرقام', '💻 أدوات الترمكس', '🐍 دروس بايثون', '📚 شروحات تقنية')
    msg = bot.send_message(call.message.chat.id, "🎯 اختر القسم الذي تريد التعديل عليه:", reply_markup=markup)
    bot.register_next_step_handler(msg, step_set_category)

def step_set_category(message):
    category = message.text
    msg = bot.send_message(message.chat.id, f"📝 أرسل اسم (الأداة/الدرس/البوت):")
    bot.register_next_step_handler(msg, step_set_name, category)

def step_set_name(message, category):
    name = message.text
    msg = bot.send_message(message.chat.id, f"🔗 أرسل التفاصيل (أوامر ترمكس أو روابط البوتات):")
    bot.register_next_step_handler(msg, step_final_save, category, name)

def step_final_save(message, category, name):
    details = message.text
    content_col.insert_one({'category': category, 'name': name, 'details': details})
    bot.send_message(message.chat.id, "✅ **تم الحفظ بنجاح!**\nالمحتوى الآن متاح لجميع المستخدمين.", reply_markup=main_markup(), parse_mode="Markdown")

# --- نظام الإذاعة الشاملة ---
@bot.callback_query_handler(func=lambda call: call.data == "broadcast")
def broadcast_prompt(call):
    msg = bot.send_message(call.message.chat.id, "📢 أرسل الرسالة التي تريد بثها (نص، صورة، فيديو):")
    bot.register_next_step_handler(msg, broadcast_send)

def broadcast_send(message):
    users = users_col.find({})
    count = 0
    for user in users:
        try:
            bot.copy_message(user['id'], message.chat.id, message.message_id)
            count += 1
        except: continue
    bot.send_message(ADMIN_ID, f"🚀 تمت الإذاعة بنجاح لـ {count} مستخدم.")

# --- Flask & Webhook Setup ---
@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_str = request.get_data().decode('UTF-8')
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return "OK", 200
    return "Forbidden", 403

@app.route('/', methods=['GET'])
def index(): return "The Architect Bot is Live! 🌐", 200

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=10000)
