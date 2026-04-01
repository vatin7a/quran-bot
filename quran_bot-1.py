#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🕌 بوت تليجرام قرآني
القرآن الكريم - رواية حفص عن عاصم
API: api.alquran.cloud (مجاني، بدون مفتاح)
"""

import logging
import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    JobQueue,
)
import datetime
import random

# ══════════════════════════════════════════
#  ضع هنا توكن البوت من @BotFather
# ══════════════════════════════════════════
BOT_TOKEN = "8797629021:AAHRb0Uimo29bUQyRMtVVj92qtMiKL3T-u4"

# ══════════════════════════════════════════
#  آيات يومية مجدولة (اختياري)
#  ضع chat_id الخاص بك هنا لاستقبالها
# ══════════════════════════════════════════
DAILY_CHAT_ID = None          # مثال: 123456789
DAILY_HOUR    = 6             # الساعة 6 صباحاً
DAILY_MINUTE  = 0

BASE_URL = "https://api.alquran.cloud/v1"
EDITION  = "quran-uthmani"   # النص العثماني (حفص)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# ─────────────────────────────────────────
# دوال مساعدة
# ─────────────────────────────────────────

def get_ayah(surah: int, ayah: int) -> str:
    """جلب آية واحدة"""
    url = f"{BASE_URL}/ayah/{surah}:{ayah}/{EDITION}"
    r = requests.get(url, timeout=10)
    data = r.json()
    if data["code"] == 200:
        a = data["data"]
        return (
            f"📖 *{a['surah']['name']}* — الآية {a['numberInSurah']}\n\n"
            f"{a['text']}\n\n"
            f"┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄\n"
            f"_﴿ {a['surah']['englishName']} — Verse {a['numberInSurah']} ﴾_"
        )
    return "⚠️ لم أجد الآية، تأكد من الرقم."


def get_surah_info(surah: int) -> dict | None:
    """جلب معلومات السورة"""
    url = f"{BASE_URL}/surah/{surah}"
    r = requests.get(url, timeout=10)
    data = r.json()
    if data["code"] == 200:
        return data["data"]
    return None


def get_surah_text(surah: int) -> list[str]:
    """جلب السورة كاملة وتقسيمها لرسائل (تليجرام: 4096 حرف)"""
    url = f"{BASE_URL}/surah/{surah}/{EDITION}"
    r = requests.get(url, timeout=15)
    data = r.json()
    if data["code"] != 200:
        return ["⚠️ لم أجد السورة."]

    s = data["data"]
    header = f"📖 *سورة {s['name']}*  ({s['englishName']})\n"
    header += f"عدد الآيات: {s['numberOfAyahs']} | النوع: {'مكية' if s['revelationType']=='Meccan' else 'مدنية'}\n\n"

    body = ""
    chunks = []
    first = True
    for a in s["ayahs"]:
        line = f"﴿{a['text']}﴾ [{a['numberInSurah']}]\n"
        if len(body) + len(line) > 3800:
            chunks.append((header if first else "") + body)
            first = False
            body = line
        else:
            body += line
    if body:
        chunks.append((header if first else "") + body)
    return chunks


def search_quran(keyword: str) -> list[str]:
    """البحث في القرآن بكلمة"""
    url = f"{BASE_URL}/search/{keyword}/all/ar"
    r = requests.get(url, timeout=15)
    data = r.json()
    if data["code"] != 200 or not data["data"]["matches"]:
        return [f"🔍 لا توجد نتائج للكلمة: *{keyword}*"]

    matches = data["data"]["matches"][:10]  # أول 10 نتائج
    total = data["data"]["count"]
    header = f"🔍 نتائج البحث عن *{keyword}* — ({total} نتيجة، أول 10):\n\n"

    body = ""
    chunks = []
    first = True
    for m in matches:
        ref = f"• *{m['surah']['name']}* [{m['surah']['number']}:{m['numberInSurah']}]\n"
        text = f"  {m['text']}\n\n"
        entry = ref + text
        if len(body) + len(entry) > 3800:
            chunks.append((header if first else "") + body)
            first = False
            body = entry
        else:
            body += entry
    if body:
        chunks.append((header if first else "") + body)
    return chunks


def random_ayah() -> str:
    """آية عشوائية"""
    num = random.randint(1, 6236)
    url = f"{BASE_URL}/ayah/{num}/{EDITION}"
    r = requests.get(url, timeout=10)
    data = r.json()
    if data["code"] == 200:
        a = data["data"]
        return (
            f"🌟 *آية اليوم*\n\n"
            f"📖 *{a['surah']['name']}* — الآية {a['numberInSurah']}\n\n"
            f"{a['text']}\n\n"
            f"_﴿ {a['surah']['englishName']} — Verse {a['numberInSurah']} ﴾_"
        )
    return "⚠️ خطأ في جلب الآية."


# ─────────────────────────────────────────
# أوامر البوت
# ─────────────────────────────────────────

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = (
        "🕌 *بوت القرآن الكريم* — رواية حفص عن عاصم\n\n"
        "الأوامر المتاحة:\n\n"
        "📌 `/ayah 2 255` — جلب آية الكرسي (سورة 2، آية 255)\n"
        "📖 `/surah 36` — سورة يس كاملة\n"
        "🔍 `/search الصبر` — البحث بكلمة في القرآن\n"
        "🌟 `/random` — آية عشوائية\n"
        "ℹ️ `/info 1` — معلومات سورة الفاتحة\n"
        "❓ `/help` — المساعدة\n\n"
        "مثال: أرسل `/ayah 1 1` لجلب الفاتحة."
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await start(update, ctx)


async def ayah_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """
    /ayah <رقم_السورة> <رقم_الآية>
    مثال: /ayah 2 255
    """
    args = ctx.args
    if len(args) != 2 or not args[0].isdigit() or not args[1].isdigit():
        await update.message.reply_text(
            "⚠️ الاستخدام الصحيح:\n`/ayah <رقم_السورة> <رقم_الآية>`\n\nمثال: `/ayah 2 255`",
            parse_mode="Markdown",
        )
        return
    s, a = int(args[0]), int(args[1])
    if not (1 <= s <= 114):
        await update.message.reply_text("⚠️ رقم السورة يجب أن يكون بين 1 و 114.")
        return
    await update.message.reply_text("⏳ جارٍ الجلب...")
    text = get_ayah(s, a)
    await update.message.reply_text(text, parse_mode="Markdown")


async def surah_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """
    /surah <رقم_السورة>
    مثال: /surah 1
    """
    args = ctx.args
    if not args or not args[0].isdigit():
        await update.message.reply_text(
            "⚠️ الاستخدام الصحيح:\n`/surah <رقم_السورة>`\n\nمثال: `/surah 36`",
            parse_mode="Markdown",
        )
        return
    s = int(args[0])
    if not (1 <= s <= 114):
        await update.message.reply_text("⚠️ رقم السورة يجب أن يكون بين 1 و 114.")
        return
    await update.message.reply_text("⏳ جارٍ تحميل السورة...")
    chunks = get_surah_text(s)
    for chunk in chunks:
        await update.message.reply_text(chunk, parse_mode="Markdown")


async def search_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """
    /search <كلمة>
    مثال: /search الصبر
    """
    if not ctx.args:
        await update.message.reply_text(
            "⚠️ الاستخدام الصحيح:\n`/search <كلمة>`\n\nمثال: `/search الصبر`",
            parse_mode="Markdown",
        )
        return
    kw = " ".join(ctx.args)
    await update.message.reply_text(f"🔍 جارٍ البحث عن: *{kw}*...", parse_mode="Markdown")
    chunks = search_quran(kw)
    for chunk in chunks:
        await update.message.reply_text(chunk, parse_mode="Markdown")


async def random_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """آية عشوائية"""
    await update.message.reply_text("🎲 جارٍ اختيار آية...")
    text = random_ayah()
    await update.message.reply_text(text, parse_mode="Markdown")


async def info_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """
    /info <رقم_السورة>
    مثال: /info 2
    """
    args = ctx.args
    if not args or not args[0].isdigit():
        await update.message.reply_text(
            "⚠️ الاستخدام الصحيح:\n`/info <رقم_السورة>`",
            parse_mode="Markdown",
        )
        return
    s = int(args[0])
    info = get_surah_info(s)
    if not info:
        await update.message.reply_text("⚠️ لم أجد السورة.")
        return
    ntype = "مكية" if info["revelationType"] == "Meccan" else "مدنية"
    msg = (
        f"📋 *معلومات السورة*\n\n"
        f"🔢 الرقم: {info['number']}\n"
        f"📛 الاسم: {info['name']} ({info['englishName']})\n"
        f"📜 النوع: {ntype}\n"
        f"🔢 عدد الآيات: {info['numberOfAyahs']}\n\n"
        f"_اكتب /surah {info['number']} لقراءة السورة كاملة_"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def unknown_msg(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❓ اكتب /help لعرض الأوامر المتاحة.",
        parse_mode="Markdown",
    )


# ─────────────────────────────────────────
# الإرسال اليومي المجدول (اختياري)
# ─────────────────────────────────────────

async def daily_ayah_job(ctx: ContextTypes.DEFAULT_TYPE):
    """ترسل آية عشوائية كل يوم في الوقت المحدد"""
    if DAILY_CHAT_ID:
        text = random_ayah()
        await ctx.bot.send_message(
            chat_id=DAILY_CHAT_ID,
            text=text,
            parse_mode="Markdown",
        )


# ─────────────────────────────────────────
# تشغيل البوت
# ─────────────────────────────────────────

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start",  start))
    app.add_handler(CommandHandler("help",   help_cmd))
    app.add_handler(CommandHandler("ayah",   ayah_cmd))
    app.add_handler(CommandHandler("surah",  surah_cmd))
    app.add_handler(CommandHandler("search", search_cmd))
    app.add_handler(CommandHandler("random", random_cmd))
    app.add_handler(CommandHandler("info",   info_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_msg))

    # ── الإرسال اليومي ──
    if DAILY_CHAT_ID:
        app.job_queue.run_daily(
            daily_ayah_job,
            time=datetime.time(hour=DAILY_HOUR, minute=DAILY_MINUTE),
        )
        print(f"✅ الإرسال اليومي مفعّل — {DAILY_HOUR:02d}:{DAILY_MINUTE:02d}")

    print("🕌 البوت يعمل الآن... اضغط Ctrl+C للإيقاف.")
    app.run_polling()


if __name__ == "__main__":
    main()
