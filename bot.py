import sqlite3
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from flask import Flask, request
import threading

TOKEN = "8830495307:AAHUW_4DL49QMQDGOTJKaB5XUNdp-3fNick"
ADMIN = 743027847
DB = "wc_pool.db"
API_KEY = "0fcafb966ba942d885c4a5ea86c9f94a"
WEBHOOK_URL = "https://andrewgrigorev.pythonanywhere.com"

db = sqlite3.connect(DB, check_same_thread=False)
db.row_factory = sqlite3.Row

db.execute("CREATE TABLE IF NOT EXISTS m(id INTEGER PRIMARY KEY, t1 TEXT, t2 TEXT, tm TEXT, s1 INTEGER, s2 INTEGER, st TEXT DEFAULT 'up', round TEXT)")
db.execute("CREATE TABLE IF NOT EXISTS p(uid INTEGER, mid INTEGER, p1 INTEGER, p2 INTEGER, PRIMARY KEY(uid,mid))")
db.execute("CREATE TABLE IF NOT EXISTS start_points(uid INTEGER PRIMARY KEY, points INTEGER DEFAULT 0)")
db.execute("CREATE TABLE IF NOT EXISTS champion_pred(uid INTEGER PRIMARY KEY, team TEXT)")
db.execute("CREATE TABLE IF NOT EXISTS champion_result(team TEXT)")
db.execute("CREATE TABLE IF NOT EXISTS names(uid INTEGER PRIMARY KEY, name TEXT)")
db.execute("CREATE TABLE IF NOT EXISTS bracket_slots(id INTEGER PRIMARY KEY, round TEXT, t1 TEXT, t2 TEXT, winner TEXT, next_id INTEGER)")

count=db.execute("SELECT COUNT(*) FROM bracket_slots").fetchone()[0]
if count==0:
    slots = [
        (1,"1/16","Германия","Парагвай","?",25),(2,"1/16","Франция","Швеция","?",25),
        (3,"1/16","Канада","ЮАР","?",26),(4,"1/16","Нидерланды","Марокко","?",26),
        (5,"1/16","Португалия","Хорватия","?",27),(6,"1/16","Испания","Австрия","?",27),
        (7,"1/16","США","Босния и Герцеговина","?",28),(8,"1/16","Бельгия","Сенегал","?",28),
        (9,"1/16","Бразилия","Япония","?",29),(10,"1/16","Кот-д'Ивуар","Норвегия","?",29),
        (11,"1/16","Мексика","Эквадор","?",30),(12,"1/16","Англия","ДР Конго","?",30),
        (13,"1/16","Аргентина","Кабо-Верде","?",31),(14,"1/16","Австралия","Египет","?",31),
        (15,"1/16","Швейцария","Алжир","?",32),(16,"1/16","Колумбия","Гана","?",32),
        (25,"1/8","?","?","?",33),(26,"1/8","?","?","?",33),
        (27,"1/8","?","?","?",34),(28,"1/8","?","?","?",34),
        (29,"1/8","?","?","?",35),(30,"1/8","?","?","?",35),
        (31,"1/8","?","?","?",36),(32,"1/8","?","?","?",36),
        (33,"1/4","?","?","?",37),(34,"1/4","?","?","?",37),
        (35,"1/4","?","?","?",38),(36,"1/4","?","?","?",38),
        (37,"1/2","?","?","?",39),(38,"1/2","?","?","?",40),
        (39,"Финал","?","?","?",None),(40,"3 место","?","?","?",None),
    ]
    for s in slots:
        db.execute("INSERT INTO bracket_slots VALUES(?,?,?,?,?,?)",s)
db.commit()

ROUNDS = ["1/16", "1/8", "1/4", "1/2", "3 место", "Финал"]

FLAGS={
    "Аргентина":"🇦🇷","Австралия":"🇦🇺","Австрия":"🇦🇹","Алжир":"🇩🇿",
    "Англия":"🏴󠁧󠁢󠁥󠁮󠁧󠁿","Бельгия":"🇧🇪","Босния и Герцеговина":"🇧🇦",
    "Бразилия":"🇧🇷","Гана":"🇬🇭","Германия":"🇩🇪","ДР Конго":"🇨🇩",
    "Египет":"🇪🇬","Испания":"🇪🇸","Кабо-Верде":"🇨🇻","Канада":"🇨🇦",
    "Колумбия":"🇨🇴","Кот-д'Ивуар":"🇨🇮","Марокко":"🇲🇦",
    "Мексика":"🇲🇽","Нидерланды":"🇳🇱","Норвегия":"🇳🇴",
    "Парагвай":"🇵🇾","Португалия":"🇵🇹","Сенегал":"🇸🇳",
    "США":"🇺🇸","Франция":"🇫🇷","Хорватия":"🇭🇷",
    "Швейцария":"🇨🇭","Швеция":"🇸🇪","Эквадор":"🇪🇨",
    "ЮАР":"🇿🇦","Япония":"🇯🇵",
}

TRANS={
    "Argentina":"Аргентина","Australia":"Австралия","Austria":"Австрия","Algeria":"Алжир",
    "England":"Англия","Belgium":"Бельгия","Bosnia-Herzegovina":"Босния и Герцеговина",
    "Brazil":"Бразилия","Ghana":"Гана","Germany":"Германия","Congo DR":"ДР Конго",
    "Egypt":"Египет","Spain":"Испания","Cape Verde Islands":"Кабо-Верде","Canada":"Канада",
    "Colombia":"Колумбия","Ivory Coast":"Кот-д'Ивуар","Morocco":"Марокко",
    "Mexico":"Мексика","Netherlands":"Нидерланды","Norway":"Норвегия",
    "Paraguay":"Парагвай","Portugal":"Португалия","Senegal":"Сенегал",
    "United States":"США","France":"Франция","Croatia":"Хорватия",
    "Switzerland":"Швейцария","Sweden":"Швеция","Ecuador":"Эквадор",
    "South Africa":"ЮАР","Japan":"Япония","South Korea":"Южная Корея",
}

def f(team):
    return FLAGS.get(team,"")+team

def tr(team):
    return TRANS.get(team, team)

slot_times={
    25: "2026-07-05 00:00", 26: "2026-07-04 22:00",
    27: "2026-07-06 22:00", 28: "2026-07-07 03:00",
    29: "2026-07-05 23:00", 30: "2026-07-06 03:00",
    31: "2026-07-07 19:00", 32: "2026-07-07 23:00",
    33: "2026-07-09 23:00", 34: "2026-07-10 22:00",
    35: "2026-07-12 00:00", 36: "2026-07-12 04:00",
    37: "2026-07-14 22:00", 38: "2026-07-15 22:00",
    39: "2026-07-19 22:00", 40: "2026-07-19 00:00",
}

def save_user(u):
    name = u.username if u.username else u.full_name
    db.execute("INSERT OR REPLACE INTO names VALUES(?,?)",(u.id, name))
    db.commit()

def get_name(uid):
    n=db.execute("SELECT name FROM names WHERE uid=?",(uid,)).fetchone()
    return n['name'] if n else str(uid)

def points_word(n):
    if 11 <= n % 100 <= 19: return "очков"
    if n % 10 == 1: return "очко"
    if 2 <= n % 10 <= 4: return "очка"
    return "очков"

async def start(u,c):
    save_user(u.effective_user)
    await u.message.reply_text("Добро пожаловать в прогнозы на плей-офф ЧМ-2026 ⚽️🏆. Жми Меню и погружайся в мир увлекательного футбола.")

async def matches(u,c):
    k=[]
    for rnd in ROUNDS:
        has=db.execute("SELECT COUNT(*) FROM m WHERE round=?",(rnd,)).fetchone()[0]
        if has>0:
            k.append([InlineKeyboardButton(f"📌 {rnd}", callback_data=f"mtch_{rnd}")])
    k.append([InlineKeyboardButton("❌ Закрыть", callback_data="close")])
    if not k: await u.message.reply_text("Нет матчей")
    else: await u.message.reply_text("Выбери раунд:", reply_markup=InlineKeyboardMarkup(k))

async def matches_callback(u,c):
    q=u.callback_query
    await q.answer()
    rn=q.data[5:]
    r=db.execute("SELECT * FROM m WHERE round=? ORDER BY tm",(rn,)).fetchall()
    t=f"📋 {rn}\n\n"
    pages=[]
    for x in r:
        sc = f"{x['s1']}:{x['s2']}" if x['st']=='fin' else "?:?"
        line=f"{x['id']}. {f(x['t1'])} vs {f(x['t2'])} | {x['tm']} | {sc}\n"
        if len(t)+len(line)>3500:
            pages.append(t)
            t=line
        else:
            t+=line
    if t: pages.append(t)
    c.user_data["mtch_pages"]=pages
    c.user_data["mtch_page"]=0
    k=[]
    if len(pages)>1:
        k.append([InlineKeyboardButton("Далее ▶️", callback_data="mtch_next")])
    k.append([InlineKeyboardButton("🔙 К раундам", callback_data="mtch_back")])
    await q.edit_message_text(pages[0], reply_markup=InlineKeyboardMarkup(k) if k else None)

async def mtch_next(u,c):
    q=u.callback_query; await q.answer()
    page=c.user_data.get("mtch_page",0)+1
    pages=c.user_data.get("mtch_pages",[])
    c.user_data["mtch_page"]=page
    k=[]
    if page<len(pages)-1: k.append([InlineKeyboardButton("Далее ▶️", callback_data="mtch_next")])
    if page>0: k.append([InlineKeyboardButton("◀️ Назад", callback_data="mtch_prev")])
    k.append([InlineKeyboardButton("🔙 К раундам", callback_data="mtch_back")])
    await q.edit_message_text(pages[page], reply_markup=InlineKeyboardMarkup(k))

async def mtch_prev(u,c):
    q=u.callback_query; await q.answer()
    page=c.user_data.get("mtch_page",1)-1
    pages=c.user_data.get("mtch_pages",[])
    c.user_data["mtch_page"]=page
    k=[]
    if page>0: k.append([InlineKeyboardButton("◀️ Назад", callback_data="mtch_prev")])
    if page<len(pages)-1: k.append([InlineKeyboardButton("Далее ▶️", callback_data="mtch_next")])
    k.append([InlineKeyboardButton("🔙 К раундам", callback_data="mtch_back")])
    await q.edit_message_text(pages[page], reply_markup=InlineKeyboardMarkup(k))

async def mtch_back(u,c):
    q=u.callback_query
    await q.answer()
    k=[]
    for rnd in ROUNDS:
        has=db.execute("SELECT COUNT(*) FROM m WHERE round=?",(rnd,)).fetchone()[0]
        if has>0:
            k.append([InlineKeyboardButton(f"📌 {rnd}", callback_data=f"mtch_{rnd}")])
    k.append([InlineKeyboardButton("❌ Закрыть", callback_data="close")])
    if not k: await q.edit_message_text("Нет матчей")
    else: await q.edit_message_text("Выбери раунд:", reply_markup=InlineKeyboardMarkup(k))

async def today(u,c):
    now = datetime.now()
    today_start = now.strftime("%Y-%m-%d") + " 18:00"
    tomorrow_end = (now + timedelta(days=1)).strftime("%Y-%m-%d") + " 06:00"
    r=db.execute("SELECT * FROM m WHERE tm >= ? AND tm <= ? ORDER BY tm", (today_start, tomorrow_end)).fetchall()
    if not r: await u.message.reply_text("Сегодня матчей нет"); return
    t=f"📅 Ближайшие матчи:\n\n"
    for x in r:
        rd = f" [{x['round']}]" if x['round'] else ""
        sc = f"{x['s1']}:{x['s2']}" if x['st']=='fin' else "?:?"
        tm_short = x['tm'][5:16]
        t+=f"{tm_short}{rd} {f(x['t1'])} vs {f(x['t2'])} | {sc}\n"
    await u.message.reply_text(t)

async def predict(u,c):
    save_user(u.effective_user)
    rounds_with_matches = db.execute("SELECT DISTINCT round FROM m WHERE st='up' AND round IS NOT NULL ORDER BY CASE WHEN round='1/16' THEN 1 WHEN round='1/8' THEN 2 WHEN round='1/4' THEN 3 WHEN round='1/2' THEN 4 WHEN round='3 место' THEN 5 WHEN round='Финал' THEN 6 END").fetchall()
    if not rounds_with_matches:
        await u.message.reply_text("Нет доступных матчей")
        return
    k=[]
    for rd in rounds_with_matches:
        rn=rd['round']
        k.append([InlineKeyboardButton(f"📌 {rn}", callback_data=f"rnd_{rn}")])
    k.append([InlineKeyboardButton("❌ Закрыть", callback_data="close")])
    await u.message.reply_text("Выбери раунд:", reply_markup=InlineKeyboardMarkup(k))

async def round_callback(u,c):
    q=u.callback_query; await q.answer()
    rn=q.data[4:]
    matches=db.execute("SELECT * FROM m WHERE round=? AND st='up' ORDER BY tm",(rn,)).fetchall()
    k=[]
    for x in matches:
        k.append([InlineKeyboardButton(f"{x['t1']} vs {x['t2']} | {x['tm']}", callback_data=f"pr_{x['id']}")])
    k.append([InlineKeyboardButton("🔙 Назад к раундам", callback_data="back_rounds")])
    k.append([InlineKeyboardButton("❌ Закрыть", callback_data="close")])
    await q.edit_message_text(f"Матчи {rn}:", reply_markup=InlineKeyboardMarkup(k))

async def back_rounds(u,c):
    q=u.callback_query; await q.answer()
    rounds_with_matches = db.execute("SELECT DISTINCT round FROM m WHERE st='up' AND round IS NOT NULL ORDER BY CASE WHEN round='1/16' THEN 1 WHEN round='1/8' THEN 2 WHEN round='1/4' THEN 3 WHEN round='1/2' THEN 4 WHEN round='3 место' THEN 5 WHEN round='Финал' THEN 6 END").fetchall()
    k=[]
    for rd in rounds_with_matches:
        rn=rd['round']
        k.append([InlineKeyboardButton(f"📌 {rn}", callback_data=f"rnd_{rn}")])
    k.append([InlineKeyboardButton("❌ Закрыть", callback_data="close")])
    await q.edit_message_text("Выбери раунд:", reply_markup=InlineKeyboardMarkup(k))

async def btn(u,c):
    q=u.callback_query; await q.answer()
    if q.data.startswith("pr_"):
        mid=int(q.data[3:])
        c.user_data["m"]=mid
        x=db.execute("SELECT t1,t2,round FROM m WHERE id=?",(mid,)).fetchone()
        await q.edit_message_text(f"[{x['round']}] {x['t1']} vs {x['t2']}\nВведи счёт (X-Y):")

async def txt(u,c):
    if "m" not in c.user_data: return
    mid=c.user_data.pop("m")
    uid=u.effective_user.id
    save_user(u.effective_user)
    m=db.execute("SELECT * FROM m WHERE id=?",(mid,)).fetchone()
    if m:
        match_time=datetime.strptime(m['tm'],"%Y-%m-%d %H:%M")
        if datetime.now()>=match_time:
            await u.message.reply_text("⏰ Матч уже начался, прогноз невозможен.")
            return
    try:
        a,b=u.message.text.strip().split("-")
        a,b=int(a),int(b)
    except: await u.message.reply_text("Формат: 2-1"); return
    db.execute("INSERT OR REPLACE INTO p VALUES(?,?,?,?)",(uid,mid,a,b))
    db.commit()
    await u.message.reply_text("✅ Принято!")

async def champion(u,c):
    save_user(u.effective_user)
    existing=db.execute("SELECT team FROM champion_pred WHERE uid=?",(u.effective_user.id,)).fetchone()
    if existing:
        res=db.execute("SELECT team FROM champion_result").fetchone()
        t=f"Твой прогноз на чемпиона: {existing['team']}"
        if res: t+=f"\nПобедитель ЧМ: {res['team']}"
        await u.message.reply_text(t)
        return
    teams=db.execute("SELECT DISTINCT t1 FROM m UNION SELECT DISTINCT t2 FROM m").fetchall()
    k=[]
    for t in teams:
        k.append([InlineKeyboardButton(t[0], callback_data=f"champ_{t[0]}")])
    await u.message.reply_text("Выбери чемпиона:", reply_markup=InlineKeyboardMarkup(k))

async def champion_callback(u,c):
    q=u.callback_query; await q.answer()
    existing=db.execute("SELECT team FROM champion_pred WHERE uid=?",(u.effective_user.id,)).fetchone()
    if existing:
        await q.answer("Ты уже выбрал чемпиона!", show_alert=True)
        return
    team=q.data[6:]
    db.execute("INSERT OR REPLACE INTO champion_pred VALUES(?,?)",(u.effective_user.id,team))
    db.commit()
    await q.edit_message_text(f"Твой прогноз на чемпиона: {team}")

async def all_predictions(u,c):
    r=db.execute("""
        SELECT m.id, m.t1, m.t2, m.tm, m.round, p.uid, p.p1, p.p2 
        FROM p JOIN m ON p.mid=m.id 
        WHERE m.st='up' 
        ORDER BY m.tm, p.uid
    """).fetchall()
    champs=db.execute("SELECT cp.uid, cp.team FROM champion_pred cp").fetchall()
    t="📋 Прогнозы участников:\n\n"
    if r:
        cur_match=None
        for x in r:
            mid=f"{f(x['t1'])} vs {f(x['t2'])}"
            if mid!=cur_match:
                cur_match=mid
                rd=f" [{x['round']}]" if x['round'] else ""
                t+=f"── {mid}{rd} | {x['tm']}\n"
            t+=f"{get_name(x['uid'])}: {x['p1']}-{x['p2']}\n"
    if champs:
        t+="\n── 🏆 Чемпион ──\n"
        for c in champs:
            t+=f"{get_name(c['uid'])}: {c['team']}\n"
    if not r and not champs: await u.message.reply_text("Нет прогнозов")
    else: await u.message.reply_text(t)

async def history(u,c):
    rounds_with_matches = db.execute("SELECT DISTINCT m.round FROM p JOIN m ON p.mid=m.id ORDER BY CASE WHEN m.round='1/16' THEN 1 WHEN m.round='1/8' THEN 2 WHEN m.round='1/4' THEN 3 WHEN m.round='1/2' THEN 4 WHEN m.round='3 место' THEN 5 WHEN m.round='Финал' THEN 6 END").fetchall()
    if not rounds_with_matches:
        await u.message.reply_text("Нет прогнозов")
        return
    k=[]
    for rd in rounds_with_matches:
        rn=rd['round']
        k.append([InlineKeyboardButton(f"📌 {rn}", callback_data=f"hist_{rn}")])
    k.append([InlineKeyboardButton("❌ Закрыть", callback_data="close")])
    await u.message.reply_text("Выбери раунд:", reply_markup=InlineKeyboardMarkup(k))

async def history_callback(u,c):
    q=u.callback_query
    await q.answer()
    rn=q.data[5:]
    c.user_data["hist_round"]=rn
    c.user_data["hist_page"]=0
    r=db.execute("""
        SELECT m.t1, m.t2, m.tm, p.uid, p.p1, p.p2, m.s1, m.s2, m.st
        FROM p JOIN m ON p.mid=m.id
        WHERE m.round=?
        ORDER BY m.tm DESC
    """,(rn,)).fetchall()
    if not r:
        await q.edit_message_text(f"Нет прогнозов на раунд {rn}")
        return
    pages=[]
    t=f"📜 История: {rn}\n\n"
    cur_match=None
    for x in r:
        mid=f"{f(x['t1'])} vs {f(x['t2'])}"
        line=""
        if mid!=cur_match:
            cur_match=mid
            sc=f" | Итог: {x['s1']}-{x['s2']}" if x['st']=='fin' else ""
            line=f"\n── {mid} | {x['tm']}{sc}\n"
        line+=f"{get_name(x['uid'])}: {x['p1']}-{x['p2']}\n"
        if len(t)+len(line)>3500:
            pages.append(t)
            t=line
        else:
            t+=line
    if t: pages.append(t)
    c.user_data["hist_pages"]=pages
    k=[]
    if len(pages)>1:
        k.append([InlineKeyboardButton("Далее ▶️", callback_data="hist_next")])
    k.append([InlineKeyboardButton("🔙 К раундам", callback_data="hist_back")])
    await q.edit_message_text(pages[0], reply_markup=InlineKeyboardMarkup(k) if k else None)

async def hist_next(u,c):
    q=u.callback_query; await q.answer()
    page=c.user_data.get("hist_page",0)+1
    pages=c.user_data.get("hist_pages",[])
    c.user_data["hist_page"]=page
    k=[]
    if page<len(pages)-1: k.append([InlineKeyboardButton("Далее ▶️", callback_data="hist_next")])
    if page>0: k.append([InlineKeyboardButton("◀️ Назад", callback_data="hist_prev")])
    k.append([InlineKeyboardButton("🔙 К раундам", callback_data="hist_back")])
    await q.edit_message_text(pages[page], reply_markup=InlineKeyboardMarkup(k))

async def hist_prev(u,c):
    q=u.callback_query; await q.answer()
    page=c.user_data.get("hist_page",1)-1
    pages=c.user_data.get("hist_pages",[])
    c.user_data["hist_page"]=page
    k=[]
    if page>0: k.append([InlineKeyboardButton("◀️ Назад", callback_data="hist_prev")])
    if page<len(pages)-1: k.append([InlineKeyboardButton("Далее ▶️", callback_data="hist_next")])
    k.append([InlineKeyboardButton("🔙 К раундам", callback_data="hist_back")])
    await q.edit_message_text(pages[page], reply_markup=InlineKeyboardMarkup(k))

async def hist_back(u,c):
    q=u.callback_query
    await q.answer()
    rounds_with_matches = db.execute("SELECT DISTINCT m.round FROM p JOIN m ON p.mid=m.id ORDER BY CASE WHEN m.round='1/16' THEN 1 WHEN m.round='1/8' THEN 2 WHEN m.round='1/4' THEN 3 WHEN m.round='1/2' THEN 4 WHEN m.round='3 место' THEN 5 WHEN m.round='Финал' THEN 6 END").fetchall()
    if not rounds_with_matches:
        await q.edit_message_text("Нет прогнозов")
        return
    k=[]
    for rd in rounds_with_matches:
        rn=rd['round']
        k.append([InlineKeyboardButton(f"📌 {rn}", callback_data=f"hist_{rn}")])
    k.append([InlineKeyboardButton("❌ Закрыть", callback_data="close")])
    await q.edit_message_text("Выбери раунд:", reply_markup=InlineKeyboardMarkup(k))

async def stats(u,c):
    k=[
        [InlineKeyboardButton("👤 Статистика игрока", callback_data="stat_menu_player")],
        [InlineKeyboardButton("📊 По раундам", callback_data="stat_menu_rounds")],
    ]
    await u.message.reply_text("Выбери тип статистики:", reply_markup=InlineKeyboardMarkup(k))

async def stats_menu(u,c):
    q=u.callback_query
    await q.answer()
    if q.data=="stat_menu_player":
        users=db.execute("SELECT DISTINCT uid FROM names").fetchall()
        if not users: await q.edit_message_text("Нет игроков"); return
        k=[]
        for u_row in users:
            name=get_name(u_row['uid'])
            k.append([InlineKeyboardButton(name, callback_data=f"stat_{u_row['uid']}")])
        await q.edit_message_text("Выбери игрока:", reply_markup=InlineKeyboardMarkup(k))
    elif q.data=="stat_menu_rounds":
        await q.delete_message()
        await roundstats(u,c)

async def show_stats(u,uid):
    r=db.execute("""
        SELECT m.t1,m.t2,m.round,p.p1,p.p2,m.s1,m.s2,m.st,
            CASE WHEN p.p1=m.s1 AND p.p2=m.s2 THEN 3 
                 WHEN (p.p1>p.p2 AND m.s1>m.s2) OR (p.p1=p.p2 AND m.s1=m.s2) OR (p.p1<p.p2 AND m.s1<m.s2) THEN 1 
                 ELSE 0 END as pts
        FROM p JOIN m ON p.mid=m.id WHERE p.uid=? ORDER BY m.tm
    """,(uid,)).fetchall()
    sp=db.execute("SELECT points FROM start_points WHERE uid=?",(uid,)).fetchone()
    cp=db.execute("SELECT team FROM champion_pred WHERE uid=?",(uid,)).fetchone()
    cr=db.execute("SELECT team FROM champion_result").fetchone()
    
    t=f"📊 Статистика {get_name(uid)}\n\n"
    total=0
    exact=0
    outcome=0
    played=0
    
    if sp and sp['points']>0:
        t+=f"📋 Групповой этап: {sp['points']} {points_word(sp['points'])}\n"
        total+=sp['points']
    
    if cp:
        champ_bonus=10 if (cr and cp['team']==cr['team']) else 0
        icon="🏆" if champ_bonus else "🕐"
        t+=f"{icon} Чемпион: прогноз «{cp['team']}»"
        if cr: t+=f" | победитель «{cr['team']}»"
        if champ_bonus: t+=f" +10"
        t+="\n"
        total+=champ_bonus
    
    t+="\n"
    
    if not r and not sp and not cp:
        await u.message.reply_text("Нет данных")
        return
    
    for x in r:
        if x['st']=='fin':
            played+=1
            if x['pts']==3:
                icon="✓"
                exact+=1
            elif x['pts']==1:
                icon="~"
                outcome+=1
            else:
                icon="✘"
            t+=f"{icon} {f(x['t1'])} vs {f(x['t2'])}\n"
            t+=f"   Прогноз: {x['p1']}-{x['p2']} | Итог: {x['s1']}-{x['s2']} | +{x['pts']}\n"
            total+=x['pts']
        else:
            t+=f"🕐 {f(x['t1'])} vs {f(x['t2'])}\n"
            t+=f"   Прогноз: {x['p1']}-{x['p2']} | Матч не сыгран\n"
    
    match_word = "матчей" if played != 1 else "матч"
    
    t+=f"\n📈 Итого:\n"
    t+=f"Сыграно {played} {match_word}\n"
    t+=f"Точных счётов: {exact} ({exact*3} {points_word(exact*3)})\n"
    t+=f"Угадано исходов: {outcome} ({outcome} {points_word(outcome)})\n"
    t+=f"💰 Всего: {total} {points_word(total)}"
    q=u.callback_query
    await q.edit_message_text(t)

async def stats_callback(u,c):
    q=u.callback_query
    await q.answer()
    uid=int(q.data[5:])
    await show_stats(u,uid)

async def roundstats(u,c):
    rounds_with_matches = db.execute("SELECT DISTINCT round FROM m WHERE st='fin' ORDER BY CASE WHEN round='1/16' THEN 1 WHEN round='1/8' THEN 2 WHEN round='1/4' THEN 3 WHEN round='1/2' THEN 4 WHEN round='3 место' THEN 5 WHEN round='Финал' THEN 6 END").fetchall()
    if not rounds_with_matches:
        await u.message.reply_text("Нет данных")
        return
    t="📊 СТАТИСТИКА ПО РАУНДАМ\n\n"
    for rd in rounds_with_matches:
        rn=rd['round']
        t+=f"═══ {rn} ═══\n"
        r=db.execute("""
            SELECT p.uid, 
                SUM(CASE WHEN p.p1=m.s1 AND p.p2=m.s2 THEN 3 WHEN (p.p1>p.p2 AND m.s1>m.s2) OR (p.p1=p.p2 AND m.s1=m.s2) OR (p.p1<p.p2 AND m.s1<m.s2) THEN 1 ELSE 0 END) as pts,
                SUM(CASE WHEN p.p1=m.s1 AND p.p2=m.s2 THEN 1 ELSE 0 END) as exact,
                SUM(CASE WHEN ((p.p1>p.p2 AND m.s1>m.s2) OR (p.p1=p.p2 AND m.s1=m.s2) OR (p.p1<p.p2 AND m.s1<m.s2)) AND NOT (p.p1=m.s1 AND p.p2=m.s2) THEN 1 ELSE 0 END) as outcome
            FROM p JOIN m ON p.mid=m.id
            WHERE m.round=? AND m.st='fin'
            GROUP BY p.uid
            ORDER BY pts DESC, exact DESC, outcome DESC
            LIMIT 10
        """,(rn,)).fetchall()
        if r:
            for i,x in enumerate(r):
                t+=f"{i+1}. {get_name(x['uid'])} — {x['pts']} очк (✓{x['exact'] or 0} ~{x['outcome'] or 0})\n"
        else:
            t+="Нет прогнозов\n"
        t+="\n"
    await u.message.reply_text(t)

async def compare(u,c):
    if len(c.args)<2:
        users=db.execute("SELECT DISTINCT uid FROM names").fetchall()
        if len(users)<2: await u.message.reply_text("Мало игроков"); return
        k=[]
        for u_row in users:
            name=get_name(u_row['uid'])
            k.append([InlineKeyboardButton(name, callback_data=f"cmp1_{u_row['uid']}")])
        await u.message.reply_text("Выбери первого игрока:", reply_markup=InlineKeyboardMarkup(k))
        return
    uid1=int(c.args[0])
    uid2=int(c.args[1])
    await show_compare(u,uid1,uid2)

async def compare_callback(u,c):
    q=u.callback_query
    await q.answer()
    data=q.data
    if data.startswith("cmp1_"):
        uid1=int(data[5:])
        users=db.execute("SELECT DISTINCT uid FROM names WHERE uid!=?",(uid1,)).fetchall()
        if not users:
            await q.edit_message_text("Нет других игроков")
            return
        k=[]
        for u_row in users:
            name=get_name(u_row['uid'])
            k.append([InlineKeyboardButton(name, callback_data=f"cmp2_{uid1}_{u_row['uid']}")])
        await q.edit_message_text("Выбери второго игрока:", reply_markup=InlineKeyboardMarkup(k))
    elif data.startswith("cmp2_"):
        rest=data[5:]
        idx=rest.find("_")
        uid1=int(rest[:idx])
        uid2=int(rest[idx+1:])
        await show_compare(u,uid1,uid2)

async def show_compare(u,uid1,uid2):
    r1=db.execute("""
        SELECT COUNT(*) as total,
            SUM(CASE WHEN p.p1=m.s1 AND p.p2=m.s2 THEN 1 ELSE 0 END) as exact,
            SUM(CASE WHEN ((p.p1>p.p2 AND m.s1>m.s2) OR (p.p1=p.p2 AND m.s1=m.s2) OR (p.p1<p.p2 AND m.s1<m.s2)) AND NOT (p.p1=m.s1 AND p.p2=m.s2) THEN 1 ELSE 0 END) as outcome,
            SUM(CASE WHEN p.p1=m.s1 AND p.p2=m.s2 THEN 3 WHEN (p.p1>p.p2 AND m.s1>m.s2) OR (p.p1=p.p2 AND m.s1=m.s2) OR (p.p1<p.p2 AND m.s1<m.s2) THEN 1 ELSE 0 END) as pts
        FROM p JOIN m ON p.mid=m.id WHERE p.uid=? AND m.st='fin'
    """,(uid1,)).fetchone()
    r2=db.execute("""
        SELECT COUNT(*) as total,
            SUM(CASE WHEN p.p1=m.s1 AND p.p2=m.s2 THEN 1 ELSE 0 END) as exact,
            SUM(CASE WHEN ((p.p1>p.p2 AND m.s1>m.s2) OR (p.p1=p.p2 AND m.s1=m.s2) OR (p.p1<p.p2 AND m.s1<m.s2)) AND NOT (p.p1=m.s1 AND p.p2=m.s2) THEN 1 ELSE 0 END) as outcome,
            SUM(CASE WHEN p.p1=m.s1 AND p.p2=m.s2 THEN 3 WHEN (p.p1>p.p2 AND m.s1>m.s2) OR (p.p1=p.p2 AND m.s1=m.s2) OR (p.p1<p.p2 AND m.s1<m.s2) THEN 1 ELSE 0 END) as pts
        FROM p JOIN m ON p.mid=m.id WHERE p.uid=? AND m.st='fin'
    """,(uid2,)).fetchone()
    sp1=db.execute("SELECT points FROM start_points WHERE uid=?",(uid1,)).fetchone()
    sp2=db.execute("SELECT points FROM start_points WHERE uid=?",(uid2,)).fetchone()
    pts1=(r1['pts'] or 0)+(sp1['points'] if sp1 else 0)
    pts2=(r2['pts'] or 0)+(sp2['points'] if sp2 else 0)
    t=f"⚔️ Сравнение\n\n"
    t+=f"{get_name(uid1)} vs {get_name(uid2)}\n\n"
    t+=f"📋 Групповой этап: {sp1['points'] if sp1 else 0} — {sp2['points'] if sp2 else 0}\n"
    t+=f"Сыграно матчей: {r1['total'] or 0} — {r2['total'] or 0}\n"
    t+=f"Точных счётов: {r1['exact'] or 0} — {r2['exact'] or 0}\n"
    t+=f"Угадано исходов: {r1['outcome'] or 0} — {r2['outcome'] or 0}\n"
    t+=f"💰 Всего: {pts1} — {pts2}\n"
    winner = get_name(uid1) if pts1>pts2 else (get_name(uid2) if pts2>pts1 else "Ничья")
    t+=f"\n🏆 {winner}" if winner!="Ничья" else "\n🤝 Ничья!"
    q=u.callback_query
    await q.edit_message_text(t)

async def lb(u,c):
    r=db.execute("""
        SELECT uid, SUM(pts) as total,
            SUM(exact) as exact,
            SUM(outcome) as outcome
        FROM (
            SELECT p.uid,
                SUM(CASE WHEN p.p1=m.s1 AND p.p2=m.s2 THEN 3 WHEN (p.p1>p.p2 AND m.s1>m.s2) OR (p.p1=p.p2 AND m.s1=m.s2) OR (p.p1<p.p2 AND m.s1<m.s2) THEN 1 ELSE 0 END) as pts,
                SUM(CASE WHEN p.p1=m.s1 AND p.p2=m.s2 THEN 1 ELSE 0 END) as exact,
                SUM(CASE WHEN ((p.p1>p.p2 AND m.s1>m.s2) OR (p.p1=p.p2 AND m.s1=m.s2) OR (p.p1<p.p2 AND m.s1<m.s2)) AND NOT (p.p1=m.s1 AND p.p2=m.s2) THEN 1 ELSE 0 END) as outcome
            FROM p JOIN m ON p.mid=m.id WHERE m.st='fin' GROUP BY p.uid
            UNION ALL
            SELECT uid, points, 0, 0 FROM start_points
            UNION ALL
            SELECT cp.uid, 10, 0, 0 FROM champion_pred cp JOIN champion_result cr ON cp.team=cr.team
        )
        GROUP BY uid
        ORDER BY total DESC, exact DESC, outcome DESC
        LIMIT 15
    """).fetchall()
    if not r: await u.message.reply_text("Нет данных"); return
    t="🏆 ТАБЛИЦА ЛИДЕРОВ\n\n"
    medals=["🥇","🥈","🥉"]
    for i,x in enumerate(r):
        medal=medals[i] if i<3 else f"{i+1}."
        t+=f"{medal} {get_name(x['uid'])} — {x['total']} очк (✓{x['exact']} ~{x['outcome']})\n"
    t+="\n✓ — точный счёт | ~ — угадан исход"
    await u.message.reply_text(t)

async def my(u,c):
    uid=u.effective_user.id
    save_user(u.effective_user)
    r=db.execute("SELECT m.t1,m.t2,p.p1,p.p2,m.s1,m.s2,m.st,m.round FROM p JOIN m ON p.mid=m.id WHERE p.uid=?",(uid,)).fetchall()
    sp=db.execute("SELECT points FROM start_points WHERE uid=?",(uid,)).fetchone()
    cp=db.execute("SELECT team FROM champion_pred WHERE uid=?",(uid,)).fetchone()
    t=f"📝 {get_name(uid)}\n"
    if sp and sp['points']>0: t+=f"Групповой этап: {sp['points']} очк\n"
    if cp: t+=f"Чемпион: {cp['team']}\n"
    t+="\n"
    for x in r:
        rd = f" [{x['round']}]" if x['round'] else ""
        rs = f" | итог {x['s1']}:{x['s2']}" if x['st']=='fin' else ""
        t+=f"{f(x['t1'])} vs {f(x['t2'])}{rd}: {x['p1']}-{x['p2']}{rs}\n"
    await u.message.reply_text(t)

async def bracket(u,c):
    db.execute("UPDATE bracket_slots SET t1='?', t2='?', winner='?' WHERE round!='1/16'")
    matches=db.execute("SELECT * FROM m WHERE st='fin'").fetchall()
    for m in matches:
        winner = m['t1'] if m['s1'] > m['s2'] else m['t2']
        slot=db.execute("SELECT * FROM bracket_slots WHERE round='1/16' AND t1=? AND t2=?",(m['t1'],m['t2'])).fetchone()
        if not slot:
            slot=db.execute("SELECT * FROM bracket_slots WHERE round='1/16' AND t1=? AND t2=?",(m['t2'],m['t1'])).fetchone()
        if slot:
            db.execute("UPDATE bracket_slots SET winner=?, t1=?, t2=? WHERE id=?",(winner,m['t1'],m['t2'],slot['id']))
    db.commit()
    
    for rnd in ["1/8","1/4","1/2"]:
        slots=db.execute("SELECT * FROM bracket_slots WHERE round=?",(rnd,)).fetchall()
        for s in slots:
            parents=db.execute("SELECT * FROM bracket_slots WHERE next_id=?",(s['id'],)).fetchall()
            if len(parents)==2:
                w1=parents[0]['winner']
                w2=parents[1]['winner']
                if w1!='?' and w2!='?' and w1!=w2:
                    db.execute("UPDATE bracket_slots SET t1=?, t2=? WHERE id=?",(w1,w2,s['id']))
    db.commit()
    
    t="🏆 СЕТКА ПЛЕЙ-ОФФ ЧМ-2026\n\n"
    prev_round=""
    slots=db.execute("SELECT * FROM bracket_slots ORDER BY id").fetchall()
    for s in slots:
        if s['round']!=prev_round:
            prev_round=s['round']
            t+=f"\n═══ {s['round']} ═══\n"
        if s['round'] in ("Финал","3 место"):
            sc = f" — {s['winner']}" if s['winner']!='?' else ""
            t+=f"{f(s['t1']) if s['t1']!='?' else '?'} vs {f(s['t2']) if s['t2']!='?' else '?'}{sc}\n"
        else:
            t1=f(s['t1']) if s['t1']!='?' else '?'
            t2=f(s['t2']) if s['t2']!='?' else '?'
            t+=f"{t1} vs {t2}"
            if s['winner']!='?': t+=f" → {f(s['winner'])}"
            t+="\n"
    await u.message.reply_text(t)

async def add(u,c):
    if u.effective_user.id!=ADMIN:
        await u.message.reply_text(f"Нет доступа. Твой ID: {u.effective_user.id}")
        return
    try:
        a=" ".join(c.args)
        parts=[x.strip() for x in a.split(",")]
        if len(parts)<3: await u.message.reply_text(f"Мало данных. Получено: {a}"); return
        t1,t2,tm=parts[0],parts[1],parts[2]
        rd=parts[3] if len(parts)>3 else ""
        db.execute("INSERT INTO m(t1,t2,tm,round) VALUES(?,?,?,?)",(t1,t2,tm,rd))
        db.commit()
        await u.message.reply_text(f"+ {t1} vs {t2} [{rd}]")
    except Exception as e: await u.message.reply_text(f"Ошибка: {e}")

async def res(u,c):
    if u.effective_user.id!=ADMIN: return
    try:
        mid=int(c.args[0])
        s1,s2=map(int,c.args[1].split("-"))
        db.execute("UPDATE m SET s1=?,s2=?,st='fin' WHERE id=?",(s1,s2,mid))
        db.commit()
        m=db.execute("SELECT * FROM m WHERE id=?",(mid,)).fetchone()
        winner = m['t1'] if s1 > s2 else m['t2']
        slot=db.execute("SELECT * FROM bracket_slots WHERE round='1/16' AND t1=? AND t2=?",(m['t1'],m['t2'])).fetchone()
        if not slot:
            slot=db.execute("SELECT * FROM bracket_slots WHERE round='1/16' AND t1=? AND t2=?",(m['t2'],m['t1'])).fetchone()
        if slot and slot['next_id']:
            next_slot=db.execute("SELECT * FROM bracket_slots WHERE id=?",(slot['next_id'],)).fetchone()
            if next_slot:
                if next_slot['t1']=='?':
                    db.execute("UPDATE bracket_slots SET t1=? WHERE id=?",(winner,next_slot['id']))
                elif next_slot['t2']=='?':
                    db.execute("UPDATE bracket_slots SET t2=? WHERE id=?",(winner,next_slot['id']))
                db.commit()
                updated=db.execute("SELECT * FROM bracket_slots WHERE id=?",(next_slot['id'],)).fetchone()
                if updated['t1']!='?' and updated['t2']!='?':
                    exist=db.execute("SELECT * FROM m WHERE t1=? AND t2=? AND round=?",(updated['t1'],updated['t2'],updated['round'])).fetchone()
                    if not exist:
                        exist=db.execute("SELECT * FROM m WHERE t1=? AND t2=? AND round=?",(updated['t2'],updated['t1'],updated['round'])).fetchone()
                    if not exist:
                        tm=slot_times.get(next_slot['id'],"2026-07-06 20:00")
                        db.execute("INSERT INTO m(t1,t2,tm,round) VALUES(?,?,?,?)",(updated['t1'],updated['t2'],tm,updated['round']))
                        db.commit()
                        await u.message.reply_text(f"OK\n✅ Автоматически создан матч {updated['round']}: {updated['t1']} vs {updated['t2']}")
                        return
        await u.message.reply_text("OK")
    except: await u.message.reply_text("/result ID 2-0")

async def setstart(u,c):
    if u.effective_user.id!=ADMIN: return
    try:
        uid=int(c.args[0])
        pts=int(c.args[1])
        db.execute("INSERT OR REPLACE INTO start_points VALUES(?,?)",(uid,pts))
        db.commit()
        await u.message.reply_text(f"Очки группового этапа {get_name(uid)}: {pts}")
    except: await u.message.reply_text("/setstart ID_игрока ОЧКИ")

async def setchampion(u,c):
    if u.effective_user.id!=ADMIN: return
    try:
        team=" ".join(c.args)
        db.execute("DELETE FROM champion_result")
        db.execute("INSERT INTO champion_result VALUES(?)",(team,))
        db.commit()
        await u.message.reply_text(f"Победитель ЧМ: {team}")
    except: await u.message.reply_text("/setchampion Команда")

async def force_predict(u,c):
    if u.effective_user.id!=ADMIN: return
    try:
        uid=int(c.args[0])
        mid=int(c.args[1])
        p1,p2=map(int,c.args[2].split("-"))
        db.execute("INSERT OR REPLACE INTO p VALUES(?,?,?,?)",(uid,mid,p1,p2))
        db.commit()
        await u.message.reply_text(f"Прогноз {get_name(uid)} на матч {mid}: {p1}-{p2}")
    except: await u.message.reply_text("/force ID_игрока ID_матча СЧЁТ")

async def remind(u,c):
    if u.effective_user.id!=ADMIN: return
    now = datetime.now()
    today_start = now.strftime("%Y-%m-%d") + " 18:00"
    tomorrow_end = (now + timedelta(days=1)).strftime("%Y-%m-%d") + " 06:00"
    today_matches = db.execute("SELECT * FROM m WHERE tm >= ? AND tm <= ? AND st='up'", (today_start, tomorrow_end)).fetchall()
    if not today_matches:
        await u.message.reply_text("Сегодня нет матчей")
        return
    users = db.execute("SELECT DISTINCT uid FROM names").fetchall()
    t = "🔔 Напоминание!\n\n"
    reminded = 0
    for match in today_matches:
        missing = []
        for user in users:
            pred = db.execute("SELECT * FROM p WHERE uid=? AND mid=?", (user["uid"], match["id"])).fetchone()
            if not pred:
                missing.append(get_name(user["uid"]))
        if missing:
            t += f"📌 {f(match['t1'])} vs {f(match['t2'])} ({match['tm']})\n"
            t += f"Не сделали прогноз: {', '.join(missing)}\n\n"
            for name in missing:
                uid_row = db.execute("SELECT uid FROM names WHERE name=?", (name,)).fetchone()
                if uid_row:
                    try:
                        await app.bot.send_message(uid_row["uid"], f"⚽ Не забудь сделать прогноз на матч {f(match['t1'])} vs {f(match['t2'])}!\nНачало: {match['tm']}\nЖми /predict")
                        reminded += 1
                    except: pass
    if reminded > 0:
        t += f"✅ Уведомления отправлены: {reminded}"
    else:
        t += "✅ Все сделали прогнозы!"
    await u.message.reply_text(t)

async def update(u,c):
    import requests
    headers = {"X-Auth-Token": API_KEY}
    url = "https://api.football-data.org/v4/competitions/WC/matches"
    try:
        resp = requests.get(url, headers=headers)
        data = resp.json()
        updated = 0
        for match in data.get("matches", []):
            if match["status"] == "FINISHED":
                home = tr(match["homeTeam"]["name"])
                away = tr(match["awayTeam"]["name"])
                s1 = match["score"]["fullTime"]["home"]
                s2 = match["score"]["fullTime"]["away"]
                if s1 is not None and s2 is not None:
                    m = db.execute("SELECT * FROM m WHERE st='up' AND ((t1=? AND t2=?) OR (t1=? AND t2=?))", 
                                   (home, away, away, home)).fetchone()
                    if m:
                        db.execute("UPDATE m SET s1=?,s2=?,st='fin' WHERE id=?", (s1, s2, m["id"]))
                        db.commit()
                        updated += 1
        await u.message.reply_text(f"✅ Обновлено: {updated} результатов")
    except Exception as e:
        await u.message.reply_text(f"Ошибка: {e}")

async def close(u,c):
    q=u.callback_query
    await q.answer()
    await q.delete_message()

application = Flask(__name__)

@application.route('/')
def home():
    return "Bot is running"

@application.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        update = Update.de_json(request.get_json(force=True), app.bot)
        import asyncio
        asyncio.run(app.process_update(update))
    return 'ok'

def run_bot():
    global app
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start",start))
    app.add_handler(CommandHandler("matches",matches))
    app.add_handler(CommandHandler("today",today))
    app.add_handler(CommandHandler("predict",predict))
    app.add_handler(CommandHandler("champion",champion))
    app.add_handler(CommandHandler("all",all_predictions))
    app.add_handler(CommandHandler("history",history))
    app.add_handler(CommandHandler("stats",stats))
    app.add_handler(CommandHandler("compare",compare))
    app.add_handler(CommandHandler("leaderboard",lb))
    app.add_handler(CommandHandler("my",my))
    app.add_handler(CommandHandler("bracket",bracket))
    app.add_handler(CommandHandler("add",add))
    app.add_handler(CommandHandler("result",res))
    app.add_handler(CommandHandler("setstart",setstart))
    app.add_handler(CommandHandler("setchampion",setchampion))
    app.add_handler(CommandHandler("force",force_predict))
    app.add_handler(CommandHandler("remind",remind))
    app.add_handler(CommandHandler("update",update))
    app.add_handler(CallbackQueryHandler(close,pattern="^close$"))
    app.add_handler(CallbackQueryHandler(stats_menu,pattern="^stat_menu_"))
    app.add_handler(CallbackQueryHandler(stats_callback,pattern="^stat_"))
    app.add_handler(CallbackQueryHandler(compare_callback,pattern="^cmp"))
    app.add_handler(CallbackQueryHandler(history_callback,pattern="^hist_"))
    app.add_handler(CallbackQueryHandler(hist_next,pattern="^hist_next$"))
    app.add_handler(CallbackQueryHandler(hist_prev,pattern="^hist_prev$"))
    app.add_handler(CallbackQueryHandler(hist_back,pattern="^hist_back$"))
    app.add_handler(CallbackQueryHandler(matches_callback,pattern="^mtch_"))
    app.add_handler(CallbackQueryHandler(mtch_next,pattern="^mtch_next$"))
    app.add_handler(CallbackQueryHandler(mtch_prev,pattern="^mtch_prev$"))
    app.add_handler(CallbackQueryHandler(mtch_back,pattern="^mtch_back$"))
    app.add_handler(CallbackQueryHandler(champion_callback,pattern="^champ_"))
    app.add_handler(CallbackQueryHandler(round_callback,pattern="^rnd_"))
    app.add_handler(CallbackQueryHandler(back_rounds,pattern="^back_rounds$"))
    app.add_handler(CallbackQueryHandler(btn,pattern="^pr_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,txt))
    
    app.run_webhook(listen="0.0.0.0", port=int(os.environ.get("PORT", 5000)), webhook_url=WEBHOOK_URL + "/webhook")

threading.Thread(target=run_bot, daemon=True).start()
