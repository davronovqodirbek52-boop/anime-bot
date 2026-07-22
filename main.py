import os
import asyncio
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton
)

# ----------------- SOZLAMALAR (SIZNING MA'LUMOTLARINGIZ) -----------------
BOT_TOKEN = "8969086805:AAFj-zP5r_pavuU-HGey1r06s9aeZfDZer4"

ADMIN_ID = 5573432777  # Telegram ID ingiz
ADMIN_USERNAME = "@fx_davronov"

CARD_NUMBER_1 = "9860 3501 4415 0116"
CARD_NUMBER_2 = "9860 1966 1783 5455"
CARD_OWNER = "Davronov"
VIP_PRICE = "15,000 so'm / oyiga"

# Treylerlar boradigan maxfiy kanal ID'si (Kanalingiz ID'sini o'zingiznikiga almashtiring)
PRIVATE_CHANNEL_ID = -100123456789  
# ----------------------------------------------------------------------

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Ma'lumotlar bazasi (Vaqtinchalik xotirada)
VIP_USERS = set()         
SUBSCRIBED_USERS = set()  
MOVIES = {}               

# FSM Bosqichlari
class AddMovieState(StatesGroup):
    waiting_for_code = State()
    waiting_for_title = State()
    waiting_for_video = State()
    waiting_for_trailer_video = State()

class VIPPaymentState(StatesGroup):
    waiting_for_screenshot = State()

# --- TUGMALAR ---
cancel_btn = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="⬅️ Ortga")]],
    resize_keyboard=True
)

admin_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="⚡ Kino Qo'shish & Treyler"), KeyboardButton(text="🗑️ Kino o'chirish")],
        [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="💎 VIP Boshqaruv")],
        [KeyboardButton(text="👨‍💼 Adminlar"), KeyboardButton(text="💬 Kanallar")],
        [KeyboardButton(text="🔴 Blocklash"), KeyboardButton(text="🟢 Blockdan olish")]
    ],
    resize_keyboard=True
)

user_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔍 Kino Qidirish"), KeyboardButton(text="🍿 VIP Obuna Bo'lish")],
        [KeyboardButton(text="✍️ Adminga Yozish / Shikoyat")]
    ],
    resize_keyboard=True
)

# /start komandasi
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    
    # Administratorni tanish
    if user_id == ADMIN_ID:
        await message.answer(f"<b>Xush kelibsiz, Admin {message.from_user.first_name}!</b> 👑", reply_markup=admin_keyboard, parse_mode="HTML")
        return

    # Foydalanuvchiga 1 MARTA majburiy obunani ko'rsatish
    if user_id not in SUBSCRIBED_USERS:
        SUBSCRIBED_USERS.add(user_id)
        inline_sub = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📢 Rasmiy Kanalga Ulanish", url="https://t.me/fx_davronov")],
                [InlineKeyboardButton(text="✅ A'zo bo'ldim", callback_data="check_sub")]
            ]
        )
        await message.answer("⚠️ Botdan foydalanish uchun rasmiy kanalimizga a'zo bo'ling:", reply_markup=inline_sub)
        return

    await message.answer(
        f"<b>Assalomu alaykum, {message.from_user.first_name}!</b> ✨\n\n"
        "🍿 <b>Anime & Cinema Botiga xush kelibsiz!</b>\n"
        "Kino kodini yuboring va tomosha qiling!",
        reply_markup=user_keyboard, parse_mode="HTML"
    )

@dp.callback_query(F.data == "check_sub")
async def sub_callback(callback: types.CallbackQuery):
    await callback.message.delete()
    await callback.message.answer("✅ Rahmat! Endi botdan to'liq foydalanishingiz mumkin.", reply_markup=user_keyboard)

# ⬅️ Ortga tugmasi
@dp.message(F.text == "⬅️ Ortga")
async def cancel_handler(message: types.Message, state: FSMContext):
    await state.clear()
    kb = admin_keyboard if message.from_user.id == ADMIN_ID else user_keyboard
    await message.answer("Bosh menyuga qaytdingiz.", reply_markup=kb)

# --- 🎬 KINO QO'SHISH VA TREYLER (QAT'IY TEKSHIRUV) ---

@dp.message(F.text == "⚡ Kino Qo'shish & Treyler")
async def start_add_movie(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.set_state(AddMovieState.waiting_for_code)
    await message.answer("🔑 <b>Kino uchun FAQAT SONLARDAN iborat KOD kiriting:</b>\n<i>(Masalan: 101)</i>", reply_markup=cancel_btn, parse_mode="HTML")

# 1. Kodni tekshirish
@dp.message(AddMovieState.waiting_for_code)
async def process_code(message: types.Message, state: FSMContext):
    if not message.text or not message.text.isdigit():
        await message.answer("❌ <b>Xato buyruq!</b> Iltimos, faqat raqamlardan iborat kod kiriting (masalan: 101):", reply_markup=cancel_btn, parse_mode="HTML")
        return
    
    await state.update_data(code=message.text.strip())
    await state.set_state(AddMovieState.waiting_for_title)
    await message.answer("📝 <b>Kino NOMINI kiriting:</b>", reply_markup=cancel_btn, parse_mode="HTML")

# 2. Nomini tekshirish
@dp.message(AddMovieState.waiting_for_title)
async def process_title(message: types.Message, state: FSMContext):
    if not message.text or message.text == "⬅️ Ortga":
        await message.answer("❌ <b>Xato buyruq!</b> Matn shaklida kino nomini kiriting:", reply_markup=cancel_btn, parse_mode="HTML")
        return
    
    await state.update_data(title=message.text.strip())
    await state.set_state(AddMovieState.waiting_for_video)
    await message.answer("📹 <b>Kino VIDEO faylini yuboring:</b>", reply_markup=cancel_btn, parse_mode="HTML")

# 3. Kino videosini tekshirish
@dp.message(AddMovieState.waiting_for_video)
async def process_video(message: types.Message, state: FSMContext):
    if not message.video:
        await message.answer("❌ <b>Xato buyruq!</b> Iltimos, kino video faylini yuboring:", reply_markup=cancel_btn, parse_mode="HTML")
        return

    await state.update_data(file_id=message.video.file_id)
    await state.set_state(AddMovieState.waiting_for_trailer_video)
    await message.answer("🍿 <b>Endi Kino TREYLER faylini (video shaklida) yuboring:</b>", reply_markup=cancel_btn, parse_mode="HTML")

# 4. Treyler videosini tekshirish va kanalga tashlash
@dp.message(AddMovieState.waiting_for_trailer_video)
async def process_trailer_video(message: types.Message, state: FSMContext):
    if not message.video:
        await message.answer("❌ <b>Xato buyruq!</b> Iltimos, treylerning VIDEO faylini yuboring:", reply_markup=cancel_btn, parse_mode="HTML")
        return

    data = await state.get_data()
    code = data['code']
    title = data['title']
    file_id = data['file_id']
    trailer_file_id = message.video.file_id

    # Maxfiy kanalga treylerni tashlash
    try:
        await bot.send_video(
            chat_id=PRIVATE_CHANNEL_ID,
            video=trailer_file_id,
            caption=f"🍿 <b>{title}</b> - Treyler\n🔑 Kodi: <code>{code}</code>",
            parse_mode="HTML"
        )
    except Exception as e:
        logging.error(f"Kanalga yuborishda xato: {e}")

    # Bazaga saqlash
    MOVIES[code] = {
        "title": title,
        "file_id": file_id,
        "trailer_id": trailer_file_id
    }
    
    await state.clear()
    await message.answer(f"✅ <b>Kino va Treyler muvaffaqiyatli saqlandi!</b>\n\n🔑 Kodi: <code>{code}</code>\n🎬 Nomi: {title}", reply_markup=admin_keyboard, parse_mode="HTML")

    # VIP obunachilarga treylerni yuborish
    for vip_id in VIP_USERS:
        try:
            vip_text = (
                "🎉 <b>YANGI PREMYERA TREYLERI!</b> (VIP Bildirishnoma)\n\n"
                f"🎬 <b>Nomi:</b> {title}\n"
                f"🔑 <b>Kino kodi:</b> <code>{code}</code>"
            )
            await bot.send_video(chat_id=vip_id, video=trailer_file_id, caption=vip_text, parse_mode="HTML")
        except Exception:
            pass

# --- 💎 VIP OBUNA VA TO'LOV TIZIMI ---

@dp.message(F.text == "🍿 VIP Obuna Bo'lish")
async def vip_info(message: types.Message):
    info_text = (
        f"💎 <b>VIP Obuna afzalliklari:</b>\n"
        f"• Yangi kinolar treylerlarini 1-bo'lib olasiz!\n"
        f"• Maxsus eksklyuziv premyeralarni tomosha qilasiz.\n\n"
        f"💵 <b>Narxi:</b> {VIP_PRICE}\n\n"
        f"Ulanish uchun pastdagi <b>'💳 Ulash va To'lov'</b> tugmasini bosing."
    )
    btn = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="💳 Ulash va To'lov", callback_data="buy_vip")]]
    )
    await message.answer(info_text, reply_markup=btn, parse_mode="HTML")

@dp.callback_query(F.data == "buy_vip")
async def buy_vip_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.set_state(VIPPaymentState.waiting_for_screenshot)
    
    pay_text = (
        f"💳 <b>To'lov ma'lumotlari:</b>\n\n"
        f"1️⃣ Karta: <code>{CARD_NUMBER_1}</code>\n"
        f"2️⃣ Karta: <code>{CARD_NUMBER_2}</code>\n"
        f"👤 Egasining ismi: <b>{CARD_OWNER}</b>\n"
        f"💵 Summa: <b>{VIP_PRICE}</b>\n\n"
        f"To'lovni amalga oshirib, <b>chek (skrinshot) faylini yuboring!</b>"
    )
    await callback.message.answer(pay_text, reply_markup=cancel_btn, parse_mode="HTML")

# Skrinshotni qabul qilish
@dp.message(VIPPaymentState.waiting_for_screenshot)
async def process_screenshot(message: types.Message, state: FSMContext):
    if not message.photo:
        await message.answer("❌ <b>Xato buyruq!</b> Iltimos, to'lov cheki skrinshotini (rasm shaklida) yuboring:", reply_markup=cancel_btn, parse_mode="HTML")
        return

    photo_id = message.photo[-1].file_id
    user = message.from_user

    admin_btn = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash (VIP berish)", callback_data=f"approve_{user.id}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_{user.id}")
            ]
        ]
    )

    caption = (
        f"💳 <b>Yangi VIP to'lov cheki!</b>\n\n"
        f"👤 Foydalanuvchi: {user.full_name} (@{user.username})\n"
        f"🆔 ID: <code>{user.id}</code>"
    )

    await bot.send_photo(chat_id=ADMIN_ID, photo=photo_id, caption=caption, reply_markup=admin_btn, parse_mode="HTML")
    await state.clear()
    await message.answer("⏳ <b>To'lov cheki adminga yuborildi!</b>\nTekshirib bo'lingach, VIP obunangiz faollashtiriladi.", reply_markup=user_keyboard, parse_mode="HTML")

@dp.callback_query(F.data.startswith("approve_"))
async def approve_vip(callback: types.CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    VIP_USERS.add(user_id)
    
    await callback.message.edit_caption(caption=callback.message.caption + "\n\n✅ <b>VIP TASDIQLANDI!</b>", parse_mode="HTML")
    await bot.send_message(chat_id=user_id, text="🎉 <b>Tabriklaymiz! VIP obunangiz faollashtirildi!</b>", reply_markup=user_keyboard, parse_mode="HTML")

@dp.callback_query(F.data.startswith("reject_"))
async def reject_vip(callback: types.CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    
    await callback.message.edit_caption(caption=callback.message.caption + "\n\n❌ <b>TO'LOV RAD ETILDI!</b>", parse_mode="HTML")
    await bot.send_message(chat_id=user_id, text="❌ Siz yuborgan to'lov cheki rad etildi. Savollaringiz bo'lsa adminga murojaat qiling.", reply_markup=user_keyboard, parse_mode="HTML")

# --- ✍️ ADMINGA YOZISH / SHIKOYAT ---

@dp.message(F.text == "✍️ Adminga Yozish / Shikoyat")
async def contact_admin(message: types.Message):
    await message.answer(f"💬 Savol yoki murojaatingiz bo'lsa adminga yozing:\n\n👨‍💻 Admin: {ADMIN_USERNAME}", parse_mode="HTML")

# --- 📊 STATISTIKA ---

@dp.message(F.text == "📊 Statistika")
async def show_stats(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer(
        f"📊 <b>Bot statistikasi:</b>\n\n"
        f"🎬 Jami kinolar: <b>{len(MOVIES)} ta</b>\n"
        f"💎 VIP a'zolar: <b>{len(VIP_USERS)} ta</b>", 
        parse_mode="HTML"
    )

# --- 🎬 KINO QIDIRISH ---

@dp.message()
async def get_movie_by_code(message: types.Message):
    code = message.text.strip()
    if code in MOVIES:
        movie = MOVIES[code]
        await message.answer_video(
            video=movie['file_id'],
            caption=f"🎬 <b>{movie['title']}</b>\n\n🍿 Maroqli hordiq chiqaring!",
            parse_mode="HTML"
        )
    else:
        await message.answer("❌ Bunday kodli kino topilmadi. Qaytadan tekshirib ko'ring!")

# --- RENDER UCHUN DUMMY WEB SERVER ---
async def handle_ping(request):
    return web.Response(text="Bot ishlayapti!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

# Main ishga tushirish
async def main():
    logging.basicConfig(level=logging.INFO)
    await start_web_server()  # Port ochish
    await bot.delete_webhook(drop_pending_updates=True)
    print("Bot muvaffaqiyatli ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
