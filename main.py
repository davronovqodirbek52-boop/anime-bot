import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Bot tokeningiz
BOT_TOKEN = "8969086805:AAFj-zP5r_pavuU-HGey1r06s9aeZfDZer4"

# Bot va Dispatcher yaratish
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Admin panel tugmalari (Keyboard)
admin_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📊 Statistika")],
        [KeyboardButton(text="🎬 Kino qo'shish"), KeyboardButton(text="🗑️ Kino o'chirish")],
        [KeyboardButton(text="👨‍💼 Adminlar"), KeyboardButton(text="💬 Kanallar")],
        [KeyboardButton(text="🔴 Blocklash"), KeyboardButton(text="🟢 Blockdan olish")]
    ],
    resize_keyboard=True
)

# /start komandasi uchun handler
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "<b>Xush kelibsiz!</b>\n\nAdmin panel tugmalaridan foydalanishingiz mumkin:",
        reply_markup=admin_keyboard,
        parse_mode="HTML"
    )

# Tugmalar bosilganda qaytariladigan javoblar
@dp.message(F.text == "📊 Statistika")
async def show_stats(message: types.Message):
    await message.answer("📊 <b>Bot statistikasi:</b>\n\nJami foydalanuvchilar: 1 ta", parse_mode="HTML")

@dp.message(F.text == "🎬 Kino qo'shish")
async def add_movie(message: types.Message):
    await message.answer("🎬 Kino qo'shish bo'limi...")

@dp.message(F.text == "🗑️ Kino o'chirish")
async def delete_movie(message: types.Message):
    await message.answer("🗑️ Kino o'chirish bo'limi...")

@dp.message(F.text == "👨‍💼 Adminlar")
async def manage_admins(message: types.Message):
    await message.answer("👨‍💼 Adminlar boshqaruvi...")

@dp.message(F.text == "💬 Kanallar")
async def manage_channels(message: types.Message):
    await message.answer("💬 Majburiy obuna kanallari...")

@dp.message(F.text == "🔴 Blocklash")
async def block_user(message: types.Message):
    await message.answer("🔴 Bloklash bo'limi...")

@dp.message(F.text == "🟢 Blockdan olish")
async def unblock_user(message: types.Message):
    await message.answer("🟢 Blokdan chiqarish bo'limi...")

# Qolgan barcha matnlar uchun
@dp.message()
async def echo_all(message: types.Message):
    await message.answer(f"Siz yozdingiz: {message.text}")

# Botni ishga tushirish funksiyasi
async def main():
    logging.basicConfig(level=logging.INFO)
    print("Bot ishga tushdi...")
    # Eski so'rovlarni o'chirish (webhookni tozalash)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())