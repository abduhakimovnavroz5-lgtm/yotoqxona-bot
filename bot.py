import os, telebot, sqlite3, threading
from telebot import types
from flask import Flask

# Yangi tokeningiz kod ichiga yuz foiz to'g'ri joylashtirildi
TOKEN = "8824857133:AAHSwpO2EtcqW0EQMKEbbTnAduW_HiK7R7s"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def home(): return "Yotoqxona bot 24/7 faol!"

def dB(q, p=()):
    u = sqlite3.connect("yotoqxona.db")
    k = u.cursor()
    k.execute(q, p)
    u.commit()
    r = k.fetchall()
    u.close()
    return r

# Jadvallarni yaratish
dB("CREATE TABLE IF NOT EXISTS q (uid INT, ism TEXT, sm INT DEFAULT 0, PRIMARY KEY(uid,ism))")
dB("CREATE TABLE IF NOT EXISTS t (uid INT, nomi TEXT, nx INT, PRIMARY KEY(uid,nomi))")
dB("CREATE TABLE IF NOT EXISTS h (uid INT, ism TEXT, info TEXT)")

def klaviatura():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton("📋 Qarzlar Ro'yxati")
    btn2 = types.KeyboardButton("📦 Mahsulotlar (Narxlar)")
    markup.add(btn1, btn2)
    return markup

@bot.message_handler(commands=['start'])
def st(m):
    uid = m.from_user.id
    dB("INSERT OR IGNORE INTO t VALUES (?, 'Energetik', 150)", (uid,))
    dB("INSERT OR IGNORE INTO t VALUES (?, 'Pechene1', 60)", (uid,))
    dB("INSERT OR IGNORE INTO t VALUES (?, 'Flash', 100)", (uid,))
    dB("INSERT OR IGNORE INTO t VALUES (?, 'Rulet', 140)", (uid,))
    
    yo_riqnomi = (
        "👋 *Salom! Men yotoqxona uchun qarz daftari botiman.*\n\n"
        "📖 *Mendan qanday foydalaniladi?*:\n\n"
        "1️⃣ *Tovar qo'shish yoki narx o'zgartirish:*\n"
        "👉 Nomi va narxini yozing: `Kofe 120`\n\n"
        "2️⃣ *Qarzga narsa sotganda (O'zim hisoblayman):*\n"
        "👉 Kim nima va nechta olganini yozing: `Ali Flash 2ta Rulet 1ta`\n\n"
        "3️⃣ *Qo'lda qarz qo'shish yoki ayirish:*\n"
        "👉 Ism va pulni yozing: `Ali+500` yoki `Ali-300`"
    )
    bot.send_message(m.chat.id, yo_riqnomi, parse_mode="Markdown", reply_markup=klaviatura())

@bot.message_handler(func=lambda msg: True)
def tx(m):
    txt, uid = m.text.strip(), m.from_user.id
    
    if txt == "📋 Qarzlar Ro'yxati":
        data = dB("SELECT ism, sm FROM q WHERE uid=?", (uid,))
        if not data:
            bot.send_message(m.chat.id, "📋 Qarzdorlar ro'yxati bo'sh.", reply_markup=klaviatura())
            return
        bot.send_message(m.chat.id, "📋 *Qarzdorlar va ularning cheklari:*", parse_mode="Markdown")
        for ism, sm in data:
            tarix_data = dB("SELECT info FROM h WHERE uid=? AND ism=?", (uid, ism))
            chek_matni = "\n*🛍 Olingan tovarlar tarixi:*\n" + "\n".join([str(i[0]) for i in tarix_data]) if tarix_data else "\n_Tarix bo'sh._"
            inline_kb = types.InlineKeyboardMarkup()
            btn = types.InlineKeyboardButton(text="❌ O'chirish", callback_data=f"del_qarz:{ism}")
            inline_kb.add(btn)
            bot.send_message(m.chat.id, f"👤 *Xaridor:* {ism}\n💰 *Umumiy qarz:* {sm} rubl{chek_matni}", parse_mode="Markdown", reply_markup=inline_kb)
        return

    elif txt == "📦 Mahsulotlar (Narxlar)":
        data = dB("SELECT nomi, nx FROM t WHERE uid=?", (uid,))
        if not data:
            bot.send_message(m.chat.id, "📦 Mahsulotlar ro'yxati bo'sh.", reply_markup=klaviatura())
            return
        bot.send_message(m.chat.id, "📦 *Sotuvdagi mahsulotlar va narxlar:*", parse_mode="Markdown")
        for nomi, nx in data:
            inline_kb = types.InlineKeyboardMarkup()
            btn = types.InlineKeyboardButton(text="❌ O'chirish", callback_data=f"del_tovar:{nomi}")
            inline_kb.add(btn)
            bot.send_message(m.chat.id, f"🔸 *{nomi}*: {nx} rubl", parse_mode="Markdown", reply_markup=inline_kb)
        return

    if "+" in txt:
        try:
            i, s = txt.split("+")
            dB("INSERT INTO q VALUES (?, ?, ?) ON CONFLICT(uid, ism) DO UPDATE SET sm=sm+?", (uid, i.strip(), int(s.strip()), int(s.strip())))
            dB("INSERT INTO h VALUES (?, ?, ?)", (uid, i.strip(), f"▪️ Qarz qo'shildi: +{s.strip()} r"))
            r = dB("SELECT sm FROM q WHERE uid=? AND ism=?", (uid, i.strip()))
            bot.send_message(m.chat.id, f"✅ {i.strip()} qarziga qo'shildi. Umumiy: {r[0][0]} r.", reply_markup=klaviatura())
        except: bot.send_message(m.chat.id, "❌ Xato format. Misol: Ali+500")
        return

    elif "-" in txt:
        try:
            i, s = txt.split("-")
            dB("INSERT INTO q VALUES (?, ?, 0) ON CONFLICT(uid, ism) DO UPDATE SET sm=sm-?", (uid, i.strip(), int(s.strip())))
            dB("INSERT INTO h VALUES (?, ?, ?)", (uid, i.strip(), f"🔻 Qarz ayirildi: -{s.strip()} r"))
            r = dB("SELECT sm FROM q WHERE uid=? AND ism=?", (uid, i.strip()))
            bot.send_message(m.chat.id, f"✅ {i.strip()} qarzidan ayirildi. Umumiy: {r[0][0]} r.", reply_markup=klaviatura())
        except: bot.send_message(m.chat.id, "❌ Xato format. Misol: Ali-300")
        return

    temp_sp = txt.split()
    if len(temp_sp) >= 2 and temp_sp[-1].isdigit():
        x = int(temp_sp[-1])
        n = " ".join(temp_sp[:-1]).strip()
        dB("INSERT INTO t VALUES (?, ?, ?) ON CONFLICT(uid, nomi) DO UPDATE SET nx=?", (uid, n, x, x))
        bot.send_message(m.chat.id, f"✅ Tovar saqlandi: *{n}* -> {x} r.", parse_mode="Markdown", reply_markup=klaviatura())
        return

    sp = txt.replace("ta", " ta").split()
    if len(sp) >= 3:
        xaridor_ismi = sp[0].strip()
        jurnal, jami_summa = "", 0
        tovarlar_ro_yxati = []
        
        i = 1
        while i < len(sp):
            t_nomi = sp[i].strip()
            miqdor = 1
            if i + 1 < len(sp) and sp[i+1].isdigit():
                miqdor = int(sp[i+1])
                i += 2
            else:
                i += 1
                
            nx = dB("SELECT nx FROM t WHERE uid=? AND nomi LIKE ?", (uid, t_nomi))
            if nx and len(nx) > 0:
                tovar_narxi = int(nx[0][0])
                oraliq_summa = tovar_narxi * miqdor
                jami_summa += oraliq_summa
                jurnal += f"▪️ {t_nomi} ({tovar_narxi} r) x {miqdor} = {oraliq_summa} r\n"
                tovarlar_ro_yxati.append(f"• {t_nomi} x{miqdor} ({oraliq_summa} r)")
            
        if jami_summa > 0:
            dB("INSERT INTO q VALUES (?, ?, ?) ON CONFLICT(uid, ism) DO UPDATE SET sm=sm+?", (uid, xaridor_ismi, jami_summa, jami_summa))
            for tovar_matn in tovarlar_ro_yxati:
                dB("INSERT INTO h VALUES (?, ?, ?)", (uid, xaridor_ismi, tovar_matn))
            r = dB("SELECT sm FROM q WHERE uid=? AND ism=?", (uid, xaridor_ismi))
            bot.send_message(m.chat.id, f"🛍 *Sotuv hisoboti:*\n\n👤 Xaridor: *{xaridor_ismi}*\n{jurnal}🧮 Jami savdo: *{jami_summa} rubl*\n💰 *{xaridor_ismi}* umumiy qarzi: *{r[0][0]} rubl*.", parse_mode="Markdown", reply_markup=klaviatura())
            return

    bot.send_message(m.chat.id, "❌ Tushunarsiz format. Pastdagi tugmalardan foydalaning.", reply_markup=klaviatura())

@bot.callback_query_handler(func=lambda call: True)
def callback_boshqar(call):
    uid = call.from_user.id
    data_str = str(call.data)
    if "del_qarz:" in data_str:
        ism = data_str.replace("del_qarz:", "").strip()
        dB("DELETE FROM q WHERE uid=? AND ism=?", (uid, ism))
        dB("DELETE FROM h WHERE uid=? AND ism=?", (uid, ism))
        bot.answer_callback_query(call.id, f"👤 {ism} o'chirildi!")
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"🗑 *{ism}* muvaffaqiyatli o'chirildi.", parse_mode="Markdown")
    elif "del_tovar:" in data_str:
        nomi = data_str.replace("del_tovar:", "").strip()
        dB("DELETE FROM t WHERE uid=? AND nomi=?", (uid, nomi))
        bot.answer_callback_query(call.id, f"📦 {nomi} o'chirildi!")
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"🗑 Tovar o'chirildi: *{nomi}*", parse_mode="Markdown")

if __name__ == "__main__":
    bot_thread = threading.Thread(target=lambda: bot.infinity_polling(timeout=20, long_polling_timeout=10))
    bot_thread.daemon = True
    bot_thread.start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
