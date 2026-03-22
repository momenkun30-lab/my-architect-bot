import telebot
from telebot import types
from flask import Flask, request
from pymongo import MongoClient
import random
import string

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
content_col = db['dynamic_content']
vip_codes_col = db['vip_codes']

# --- قوائم الأقسام ---
def main_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('🔢 قسم الأرقام', '💻 أدوات الترمكس')
    markup.add('🐍 دروس بايثون', '📚 شروحات تقنية')
    markup.add('💎 قسم VIP', '👨‍💻 المطور')
    return markup

def vip_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('🔹 أفضل بوتات الأرقام الفيك')
    markup.add('🔹 أدوات Python وTermux الاحترافية')
    markup.add('🔹 شروحات الذكاء الاصطناعي')
    markup.add('🔙 رجوع للقائمة الرئيسية')
    return markup

def admin_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("➕ إضافة محتوى (فيديو/نص)", callback_data="add_content"))
    markup.add(types.InlineKeyboardButton("💎 إدارة أكواد VIP", callback_data="manage_vip"))
    markup.add(types.InlineKeyboardButton("📢 إذاعة عامة", callback_data="broadcast"))
    markup.add(types.InlineKeyboardButton("📊 الإحصائيات", callback_data="stats"))
    return markup

# --- الأوامر الأساسية ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    users_col.update_one({'id': user_id}, {'$setOnInsert': {'id': user_id, 'is_vip': False}}, upsert=True)
    welcome = "─── ❖ ── ✦ ── ❖ ───\n🌐 **ARCHITECT OS v4.0 ONLINE**\n─── ❖ ── ✦ ── ❖ ───\n\nنظام الإدارة المركزية جاهز للعمل.\nاختر القسم الذي تريده من القائمة أدناه 👇"
    bot.send_message(message.chat.id, welcome, reply_markup=main_markup(), parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == '👨‍💻 المطور')
def developer(message):
    bot.send_message(message.chat.id, "👨‍💻 **المطور:**\n@SDVee249", parse_mode="Markdown")

# --- قائمة بجميع الأقسام ---
all_categories = [
    '🔢 قسم الأرقام', 
    '💻 أدوات الترمكس', 
    '🐍 دروس بايثون', 
    '📚 شروحات تقنية',
    '🔹 أفضل بوتات الأرقام الفيك',
    '🔹 أدوات Python وTermux الاحترافية',
    '🔹 شروحات الذكاء الاصطناعي'
]

# --- دالة عرض المحتوى (تم تحديثها بالكامل لإصلاح مشكلة العرض) ---
@bot.message_handler(func=lambda m: m.text in all_categories)
def show_content(message):
    try:
        category = message.text
        
        # 1. رسالة تحميل مؤقتة
        loading_msg = bot.send_message(message.chat.id, f"⏳ جاري البحث في {category}...")
        
        # 2. تحويل المؤشر إلى قائمة (list) لضمان جلب البيانات بالكامل قبل العرض
        # هذا هو الحل الأساسي لمشكلة عدم ظهور البيانات
        items = list(content_col.find({'category': category}).sort('_id', -1))
        
        # 3. حذف رسالة التحميل
        try:
            bot.delete_message(message.chat.id, loading_msg.message_id)
        except:
            pass
            
        if not items:
            bot.send_message(message.chat.id, "⚠️ لا يوجد محتوى مضاف في هذا القسم حالياً.")
            return

        # 4. عرض العناصر واحداً تلو الآخر
        for item in items:
            name = item.get('name', 'غير مسمى')
            details = item.get('details', 'لا توجد تفاصيل')
            
            # إزالة رموز التنسيق من النص لتجنب الأخطاء
            text = f"🔹 الاسم: {name}\n──────────────────\n{details}"
            
            video_id = item.get('video_id')
            
            if video_id:
                try:
                    bot.send_video(message.chat.id, video_id, caption=text)
                except Exception as e:
                    bot.send_message(message.chat.id, text + f"\n\n(⚠️ الفيديو غير متاح أو تم حذفه)")
            else:
                bot.send_message(message.chat.id, text)
                
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ حدث خطأ أثناء جلب البيانات:\n{str(e)}")

# --- منطق قسم VIP ---
@bot.message_handler(func=lambda m: m.text == '💎 قسم VIP')
def vip_section(message):
    try:
        user_id = message.from_user.id
        user = users_col.find_one({'id': user_id})
        
        if user and user.get('is_vip', False):
            bot.send_message(message.chat.id, "📩 مرحباً بك في قسم VIP 🔐\nاختر القسم الذي تريده:", reply_markup=vip_markup())
        else:
            msg = bot.send_message(message.chat.id, "🔒 **قسم VIP مغلق**\nهذا القسم خاص بحاملي عضوية VIP.\nيرجى إرسال كود الاشتراك للدخول:")
            bot.register_next_step_handler(msg, check_vip_code)
    except Exception as e:
        bot.send_message(message.chat.id, f"Error: {e}")

def check_vip_code(message):
    try:
        code = message.text.strip()
        valid_code = vip_codes_col.find_one({'code': code, 'active': True})
        
        if valid_code:
            users_col.update_one({'id': message.from_user.id}, {'$set': {'is_vip': True}})
            bot.send_message(message.chat.id, "✅ **الكود صحيح!**\nتم تفعيل العضوية الذهبية بنجاح.\nأهلاً بك في العالم الحصري 👑", reply_markup=vip_markup(), parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, "❌ **الكود غير صحيح** أو تم استخدامه مسبقاً.", reply_markup=main_markup())
    except Exception as e:
        bot.send_message(message.chat.id, f"Error: {e}")

@bot.message_handler(func=lambda m: m.text == '🔙 رجوع للقائمة الرئيسية')
def back_to_main(message):
    bot.send_message(message.chat.id, "🏠 عودة للقائمة الرئيسية", reply_markup=main_markup())

# --- لوحة التحكم ---
@bot.message_handler(commands=['admin'])
def admin(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "👑 **لوحة تحكم النظام**\nاختر العملية:", reply_markup=admin_markup(), parse_mode="Markdown")

# --- إضافة المحتوى ---
@bot.callback_query_handler(func=lambda call: call.data == "add_content")
def add_content_step1(call):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add('🔢 قسم الأرقام', '💻 أدوات الترمكس', '🐍 دروس بايثون')
    markup.add('📚 شروحات تقنية', '🔹 أفضل بوتات الأرقام الفيك')
    markup.add('🔹 أدوات Python وTermux الاحترافية', '🔹 شروحات الذكاء الاصطناعي')
    
    msg = bot.send_message(call.message.chat.id, "🎯 اختر القسم الذي تريد إضافة محتوى إليه:", reply_markup=markup)
    bot.register_next_step_handler(msg, add_content_step2)

def add_content_step2(message):
    category = message.text
    if category not in all_categories:
        bot.send_message(message.chat.id, "❌ اسم القسم غير صحيح، ابدأ من جديد /admin")
        return
    
    msg = bot.send_message(message.chat.id, "📝 أرسل **اسم** المحتوى (اسم البوت/الأداة/الدرس):", parse_mode="Markdown")
    bot.register_next_step_handler(msg, add_content_step3, category)

def add_content_step3(message, category):
    name = message.text
    msg = bot.send_message(message.chat.id, "🔗 أرسل **التفاصيل** (روابط، أوامر، شرح مختصر):")
    bot.register_next_step_handler(msg, add_content_step4, category, name)

def add_content_step4(message, category, name):
    details = message.text
    msg = bot.send_message(message.chat.id, "🎥 أرسل **فيديو** الآن (اختياري)\nأو اكتب `skip` للتجاوز:")
    bot.register_next_step_handler(msg, add_content_step5, category, name, details)

def add_content_step5(message, category, name, details):
    try:
        video_id = None
        if message.video:
            video_id = message.video.file_id
        # إذا لم يكن فيديو ولا كلمة skip، نتخطى الفيديو
        
        content_col.insert_one({
            'category': category,
            'name': name,
            'details': details,
            'video_id': video_id
        })
        
        bot.send_message(message.chat.id, "✅ **تم إضافة المحتوى بنجاح!**", reply_markup=main_markup(), parse_mode="Markdown")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ فشل الحفظ: {e}")

# --- إدارة أكواد VIP ---
@bot.callback_query_handler(func=lambda call: call.data == "manage_vip")
def manage_vip_menu(call):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✨ إنشاء كود جديد", callback_data="gen_vip"))
    markup.add(types.InlineKeyboardButton("📋 عرض الأكواد النشطة", callback_data="list_vip"))
    markup.add(types.InlineKeyboardButton("🗑️ حذف كود", callback_data="del_vip_prompt"))
    bot.send_message(call.message.chat.id, "💎 **إدارة أكواد VIP:**", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "gen_vip")
def generate_vip_code(call):
    try:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        vip_codes_col.insert_one({'code': code, 'active': True})
        bot.send_message(call.message.chat.id, f"✅ تم إنشاء كود جديد:\n\n🔑 `{code}`", parse_mode="Markdown")
    except Exception as e:
        bot.send_message(call.message.chat.id, f"Error: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "list_vip")
def list_vip_codes(call):
    try:
        codes = vip_codes_col.find({'active': True})
        text = "📋 **الأكواد النشطة:**\n\n"
        has_codes = False
        for c in codes:
            text += f"🔑 `{c['code']}`\n"
            has_codes = True
        if not has_codes: text = "لا توجد أكواد نشطة."
        bot.send_message(call.message.chat.id, text, parse_mode="Markdown")
    except Exception as e:
        bot.send_message(call.message.chat.id, f"Error: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "del_vip_prompt")
def delete_vip_code_prompt(call):
    msg = bot.send_message(call.message.chat.id, "🗑️ أرسل الكود الذي تريد حذفه:")
    bot.register_next_step_handler(msg, delete_vip_code_action)

def delete_vip_code_action(message):
    try:
        code = message.text.strip()
        res = vip_codes_col.delete_one({'code': code})
        if res.deleted_count > 0:
            bot.send_message(message.chat.id, "✅ تم حذف الكود.")
        else:
            bot.send_message(message.chat.id, "❌ الكود غير موجود.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Error: {e}")

# --- الإذاعة ---
@bot.callback_query_handler(func=lambda call: call.data == "broadcast")
def broadcast_prompt(call):
    msg = bot.send_message(call.message.chat.id, "📢 أرسل الرسالة التي تريد بثها:")
    bot.register_next_step_handler(msg, broadcast_send)

def broadcast_send(message):
    try:
        users = users_col.find({})
        count = 0
        for user in users:
            try:
                bot.copy_message(user['id'], message.chat.id, message.message_id)
                count += 1
            except: continue
        bot.send_message(ADMIN_ID, f"🚀 تمت الإذاعة لـ {count} مستخدم.")
    except Exception as e:
        bot.send_message(ADMIN_ID, f"Error: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "stats")
def stats(call):
    try:
        total_users = users_col.count_documents({})
        total_vip = users_col.count_documents({'is_vip': True})
        text = f"📊 **الإحصائيات:**\n\n👥 المستخدمين: {total_users}\n👑 VIP: {total_vip}"
        bot.send_message(call.message.chat.id, text, parse_mode="Markdown")
    except Exception as e:
        bot.send_message(call.message.chat.id, f"Error: {e}")

# --- تشغيل السيرفر ---
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
