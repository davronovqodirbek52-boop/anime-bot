import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton
)

# Bot tokeningiz
BOT_TOKEN = "8969086805:AAFj-zP5r_pavuU-HGey1r06s9aeZfDZer4"

# Bot va Dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Ma'lumotlar bazasi (Xotirada)
VIP_USERS = set()      # VIP foydalanuvchilar ID'lari
MOVIES = {}            # Kinolar kodi va ma'lumotlari
BLOCKED_USERS = set()  # Bloklangan foydalanuvchilar

# Kino qo'shish bosqichlari (FSM)
class AddMovieState(StatesGroup):
    waiting_for_code = State()
    waiting_for_title = State()
    waiting_for_video = State()
    waiting_for_trailer = State()

# 🎨 Zamonaviy Admin menyu tugmalari (Sizning barcha eski tugmalaringiz bilan)
admin_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="⚡ Kino Qo'shish & Treyler"), KeyboardButton(text="🗑️ Kino o'chirish")],
        [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="💎 VIP Boshqaruv")],
        [KeyboardButton(text="👨‍💼 Adminlar"), KeyboardButton(text="💬 Kanallar")],
        [KeyboardButton(text="🔴 Blocklash"), KeyboardButton(text="🟢 Blockdan olish")]
    ],
    resize_keyboard=True,
    input_field_placeholder="Kerakli bo'limni tanlang..."
)

# 🎬 Oddiy foydalanuvchi tugmalari
user_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔍 Kino Qidirish"), KeyboardButton(text="💎 VIP Obuna Haqida")]
    ],
    resize_keyboard=True
)

# /start komandasi
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    welcome_text = (
        f"<b>Assalomu alaykum, {message.from_user.first_name}!</b> ✨\n\n"
        "🍿 <b>Anime & Cinema Botiga xush kelibsiz!</b>\n"
        "Kino kodini yuboring va tomosha qiling!\n\n"
        "<i>VIP a'zolar esa eng yangi premyera treylerlarini 1-bo'lib olishadi!</i>"
    )
    await message.answer(welcome_text, reply_markup=admin_keyboard, parse_mode="HTML")

# --- 🎬 KINO QO'SHISH JARAYONI ---

@dp.message(F.text == "⚡ Kino Qo'shish & Treyler")
async def start_add_movie(message: types.Message, state: FSMContext):
    await state.set_state(AddMovieState.waiting_for_code)
    await message.answer("🔑 <b>Yangi kino uchun KOD kiriting:</b>\n<i>(Masalan: 101)</i>", parse_mode="HTML")

@dp.message(AddMovieState.waiting_for_code)
async def process_code(message: types.Message, state: FSMContext):
    await state.update_data(code=message.text.strip())
    await state.set_state(AddMovieState.waiting_for_title)
    await message.answer("📝 <b>Kino NOMINI kiriting:</b>\n<i>(Masalan: Attack on Titan)</i>", parse_mode="HTML")

@dp.message(AddMovieState.waiting_for_title)
async def process_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await state.set_state(AddMovieState.waiting_for_video)
    await message.answer("📹 <b>Kino VIDEO faylini yuboring:</b>", parse_mode="HTML")

@dp.message(AddMovieState.waiting_for_video, F.video)
async def process_video(message: types.Message, state: FSMContext):
    await state.update_data(file_id=message.video.file_id)
    await state.set_state(AddMovieState.waiting_for_trailer)
    await message.answer("🍿 <b>Kino TREYLER havolasini (linkini) yuboring:</b>\n<i>(Masalan: https://youtube.com/...)</i>", parse_mode="HTML")

@dp.message(AddMovieState.waiting_for_trailer)
async def process_trailer(message: types.Message, state: FSMContext):
    trailer_url = message.text.strip()
    data = await state.get_data()
    
    code = data['code']
    title = data['title']
    file_id = data['file_id']

    # Bazaga saqlash
    MOVIES[code] = {
        "title": title,
        "file_id": file_id,
        "trailer": trailer_url
    }
    
    await state.clear()
    await message.answer(f"✅ <b>Kino muvaffaqiyatli saqlandi!</b>\n\n🔑 Kodi: <code>{code}</code>\n🎬 Nomi: {title}", parse_mode="HTML")

    # VIP a'zolarga bildirishnoma yuborish
    trailer_inline_btn = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🍿 Treylerni Ko'rish", url=trailer_url)]
        ]
    )

    vip_count = 0
    for vip_id in VIP_USERS:
        try:
            vip_text = (
                "🎉 <b>YANGI PREMYERA YUKLANDI!</b> (VIP Bildirishnoma)\n\n"
                f"🎬 <b>Nomi:</b> {title}\n"
                f"🔑 <b>Kino kodi:</b> <code>{code}</code>\n\n"
                "<i>Siz VIP a'zo bo'lganingiz uchun bu bildirishnoma 1-bo'lib sizga yetib keldi!</i> 🚀"
            )
            await bot.send_message(chat_id=vip_id, text=vip_text, reply_markup=trailer_inline_btn, parse_mode="HTML")
            vip_count += 1
        except Exception:
            pass

# --- 🛠 ESKI BO'LIMLAR (SIZNING TUGMALARINGIZ) ---

@dp.message(F.text == "📊 Statistika")
async def show_stats(message: types.Message):
    await message.answer(
        f"📊 <b>Bot statistikasi:</b>\n\n"
        f"🎬 Jami kinolar: <b>{len(MOVIES)} ta</b>\n"
        f"💎 VIP foydalanuvchilar: <b>{len(VIP_USERS)} ta</b>\n"
        f"🚫 Bloklanganlar: <b>{len(BLOCKED_USERS)} ta</b>", 
        parse_mode="HTML"
    )

@dp.message(F.text == "🗑️ Kino o'chirish")
async def delete_movie(message: types.Message):
    await message.answer("🗑️ Kino o'chirish bo'limi...\n<i>O'chirmoqchi bo'lgan kino kodini kiriting.</i>", parse_mode="HTML")

@dp.message(F.text == "👨‍💼 Adminlar")
async def manage_admins(message: types.Message):
    await message.answer("👨‍💼 Adminlar boshqaruvi bo'limi.")

@dp.message(F.text == "💬 Kanallar")
async def manage_channels(message: types.Message):
    await message.answer("💬 Majburiy obuna kanallari sozlamalari.")

@dp.message(F.text == "🔴 Blocklash")
async def block_user(message: types.Message):
    await message.answer("🔴 Bloklash bo'limi...")

@dp.message(F.text == "🟢 Blockdan olish")
async def unblock_user(message: types.Message):
    await message.answer("🟢 Blokdan chiqarish bo'limi...")

@dp.message(F.text == "💎 VIP Boshqaruv")
async def vip_management(message: types.Message):
    await message.answer(
        "💎 <b>VIP Boshqaruv:</b>\n\n"
        "VIP qo'shish uchun: <code>/addvip USER_ID</code>\n"
        "VIP o'chirish uchun: <code>/delvip USER_ID</code>", 
        parse_mode="HTML"
    )

# --- 💎 VIP QO'SHISH VA O'CHIRISH COMMANDALARI ---

@dp.message(Command("addvip"))
async def add_vip_user(message: types.Message):
    try:
        user_id = int(message.text.split()[1])
        VIP_USERS.add(user_id)
        await message.answer(f"✅ <b>{user_id}</b> VIP a'zolarga qo'shildi!", parse_mode="HTML")
    except Exception:
        await message.answer("⚠️ Qo'llanilishi: <code>/addvip USER_ID</code>", parse_mode="HTML")

@dp.message(Command("delvip"))
async def del_vip_user(message: types.Message):
    try:
        user_id = int(message.text.split()[1])
        VIP_USERS.discard(user_id)
        await message.answer(f"❌ <b>{user_id}</b> VIP ro'yxatidan olib tashlandi!", parse_mode="HTML")
    except Exception:
        await message.answer("⚠️ Qo'llanilishi: <code>/delvip USER_ID</code>", parse_mode="HTML")

# Foydalanuvchi kino kodini yuborganda kinoni chiqarish
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
        await message.answer(f"Siz yozdingiz: {message.text}\n\n<i>Kino kodi kiritilsa kino chiqarib beriladi!</i>", parse_mode="HTML")

# Botni ishga tushirish funksiyasi
async def main():
    logging.basicConfig(level=logging.INFO)
    print("Bot ishga tushdi...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
