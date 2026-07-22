import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton
)

# Bot tokeningiz
BOT_TOKEN = "8969086805:AAFj-zP5r_pavuU-HGey1r06s9aeZfDZer4"

# Bot va Dispatcher yaratish
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Vaqtinchalik VIP foydalanuvchilar va Kinolar bazasi (Soddalashtirilgan)
VIP_USERS = set()  # VIP foydalanuvchilar Telegram ID'lari saqlanadi
MOVIES = {}         # Kinolar kodi va ma'lumotlari

# 🎨 Zamonaviy Admin menyu tugmalari
admin_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="⚡ Kino Qo'shish & Treyler"), KeyboardButton(text="🗑️ O'chirish")],
        [KeyboardButton(text="💎 VIP Boshqaruv"), KeyboardButton(text="📊 Statistika")],
        [KeyboardButton(text="📢 Majburiy Obuna"), KeyboardButton(text="👥 Adminlar")],
        [KeyboardButton(text="🛡️ Bloklash"), KeyboardButton(text="🔓 Blokdan Olish")]
    ],
    resize_keyboard=True,
    input_field_placeholder="Kerakli bo'limni tanlang..."
)

# 🎬 Oddiy foydalanuvchilar uchun chiroyli menyu
user_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔍 Kino Qidirish"), KeyboardButton(text="🍿 Treylerlar")],
        [KeyboardButton(text="💎 VIP Obuna Haqida"), KeyboardButton(text="📞 Yordam / Aloqa")]
    ],
    resize_keyboard=True
)

# /start komandasi
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    welcome_text = (
        f"<b>Assalomu alaykum, {message.from_user.first_name}!</b> ✨\n\n"
        "🍿 <b>Anime & Cinema Botiga xush kelibsiz!</b>\n"
        "Barcha kinolar, multfilmlar va animelar siz uchun <b>butunlay bepul</b>!\n\n"
        "<i>VIP a'zolar esa eng yangi premyera treylerlarini birinchilardan bo'lib qabul qilishadi!</i>"
    )
    await message.answer(welcome_text, reply_markup=user_keyboard, parse_mode="HTML")

# 💎 VIP qo'shish va o'chirish (Admin komandalari: /addvip ID va /delvip ID)
@dp.message(Command("addvip"))
async def add_vip_user(message: types.Message):
    try:
        user_id = int(message.text.split()[1])
        VIP_USERS.add(user_id)
        await message.answer(f"✅ <b>{user_id}</b> muvaffaqiyatli VIP a'zolar ro'yxatiga qo'shildi!", parse_mode="HTML")
    except (IndexError, ValueError):
        await message.answer("⚠️ Qullanilishi: <code>/addvip USER_ID</code>", parse_mode="HTML")

@dp.message(Command("delvip"))
async def del_vip_user(message: types.Message):
    try:
        user_id = int(message.text.split()[1])
        VIP_USERS.discard(user_id)
        await message.answer(f"❌ <b>{user_id}</b> VIP statusidan olib tashlandi!", parse_mode="HTML")
    except (IndexError, ValueError):
        await message.answer("⚠️ Qullanilishi: <code>/delvip USER_ID</code>", parse_mode="HTML")

# ⚡ Admin: Yangi kino va treyler qo meytida tarqatish
@dp.message(F.text == "⚡ Kino Qo'shish & Treyler")
async def add_movie_with_trailer(message: types.Message):
    # Misol uchun yangi kino ma'lumotlari
    movie_title = "AOT: Final Season"
    movie_code = "105"
    trailer_url = "https://youtube.com" # Treyler havolasi

    # VIP foydalanuvchilar uchun chiroyli inline tugma
    trailer_inline_btn = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🍿 Treylerni Tomosha Qilish", url=trailer_url)],
            [InlineKeyboardButton(text="⚡ Kinoni Botdan Olish", callback_data=f"get_{movie_code}")]
        ]
    )

    # VIP a'zolarga eksklyuziv bildirishnoma yuborish
    vip_count = 0
    for vip_id in VIP_USERS:
        try:
            vip_text = (
                "🎉 <b>YANGI PREMYERA YUKLANDI!</b> (VIP Bildirishnoma)\n\n"
                f"🎬 <b>Nomi:</b> {movie_title}\n"
                f"🔑 <b>Kino kodi:</b> <code>{movie_code}</code>\n\n"
                "<i>Siz VIP a'zo bo'lganingiz uchun bu xabar birinchilardan bo'lib sizga yetib keldi!</i> 🚀"
            )
            await bot.send_message(chat_id=vip_id, text=vip_text, reply_markup=trailer_inline_btn, parse_mode="HTML")
            vip_count += 1
        except Exception as e:
            logging.error(f"VIP {vip_id} ga xabar yuborishda xatolik: {e}")

    await message.answer(
        f"✅ <b>Kino va treyler saqlandi!</b>\n"
        f"📩 {vip_count} ta VIP a'zoga bildirishnoma yuborildi.",
        reply_markup=admin_keyboard,
        parse_mode="HTML"
    )

# 📊 Statistika va Admin tugmalari
@dp.message(F.text == "📊 Statistika")
async def show_stats(message: types.Message):
    await message.answer(
        f"📊 <b>Bot Statistikasi:</b>\n\n"
        f"👥 VIP A'zolar: <b>{len(VIP_USERS)} ta</b>\n"
        f"🎬 Jami Kinolar: <b>{len(MOVIES)} ta</b>", 
        parse_mode="HTML"
    )

@dp.message(F.text == "💎 VIP Obuna Haqida")
async def vip_info(message: types.Message):
    info_text = (
        "💎 <b>VIP Obuna afzalliklari:</b>\n\n"
        "1. 🎬 Barcha yangi premyera kinolar treyleri darhol sizga yetib boradi.\n"
        "2. ⚡ Kinolarni 1-bo'lib ko'rish imkoniyati.\n"
        "3. 🚫 Reklamasiz va qulay foydalanish!\n\n"
        "<i>Barcha kinolar esa har doim bepul bo'lib qoladi!</i>"
    )
    await message.answer(info_text, parse_mode="HTML")

# Qolgan matnlar uchun (kino kodi kiritilganda)
@dp.message()
async def echo_all(message: types.Message):
    await message.answer(f"Siz yozdingiz: {message.text}\n\n<i>Kino kodini kiritsangiz kino chiqarib beriladi!</i>", parse_mode="HTML")

# Botni ishga tushirish
async def main():
    logging.basicConfig(level=logging.INFO)
    print("Bot ishga tushdi...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    # Eski so'rovlarni o'chirish (webhookni tozalash)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
