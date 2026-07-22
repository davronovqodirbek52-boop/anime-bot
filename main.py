import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

# ==========================================================
#  SOZLAMALAR (shu joyларni o'zingizga moslab to'ldiring)
# ==========================================================

# ⚠️ Tokenni to'g'ridan-to'g'ri kodga yozmang! Eski token GitHub'da oshkor
# bo'lgani uchun @BotFather'dan /revoke qilib, yangisini oling va uni
# muhit o'zgaruvchisi (environment variable) qilib bering:
#   export BOT_TOKEN="yangi_token"
BOT_TOKEN = os.getenv("BOT_TOKEN", "BU_YERGA_YANGI_TOKEN_QOYING")

# Sizning (bot egasi) Telegram ID'ingiz — to'lov skrinshotlari va
# shikoyatlar shu ID'ga yuboriladi. O'zingizning ID'ingizni bilish uchun
# @userinfobot ga /start bosing.
OWNER_ID = 123456789  # <-- O'ZGARTIRING

# Treylerlar avtomatik joylanadigan MAXFIY kanal ID'si.
# Botni shu kanalga admin qilib qo'shib qo'yish kerak (bir marta).
# Kanal ID odatda -100 bilan boshlanadi.
TRAILER_CHANNEL_ID = -1001234567890  # <-- O'ZGARTIRING

# To'lov qabul qilinadigan kartalar
CARDS = [
    {"bank": "Uzcard", "number": "8600 1234 5678 9012", "owner": "F.I.Sh."},
    {"bank": "Humo", "number": "9860 1234 5678 9012", "owner": "F.I.Sh."},
]

# VIP tariflari
VIP_PLANS = {
    "1oy": {"name": "1 oylik VIP", "price": "20 000 so'm"},
    "3oy": {"name": "3 oylik VIP", "price": "50 000 so'm"},
    "12oy": {"name": "1 yillik VIP", "price": "150 000 so'm"},
}

# ==========================================================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Ma'lumotlar bazasi (Xotirada)
VIP_USERS = set()
MOVIES = {}
BLOCKED_USERS = set()

# Kanal haqida bildirishnoma faqat 1 marta chiqishi uchun bayroq
CHANNEL_NOTICE_SHOWN = False


# ----------------------------------------------------------
#  FSM holatlari
# ----------------------------------------------------------
class AddMovieState(StatesGroup):
    waiting_for_code = State()
    waiting_for_title = State()
    waiting_for_video = State()
    waiting_for_trailer = State()


class VipState(StatesGroup):
    waiting_for_screenshot = State()


class ComplaintState(StatesGroup):
    waiting_for_text = State()


# ----------------------------------------------------------
#  Klaviaturalar
# ----------------------------------------------------------
admin_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="⚡ Kino Qo'shish & Treyler"), KeyboardButton(text="🗑️ Kino o'chirish")],
        [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="💎 VIP Boshqaruv")],
        [KeyboardButton(text="👨‍💼 Adminlar"), KeyboardButton(text="💬 Kanallar")],
        [KeyboardButton(text="🔴 Blocklash"), KeyboardButton(text="🟢 Blockdan olish")],
    ],
    resize_keyboard=True,
    input_field_placeholder="Kerakli bo'limni tanlang...",
)

user_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔍 Kino Qidirish"), KeyboardButton(text="💎 VIP Obuna Haqida")],
        [KeyboardButton(text="🆘 Shikoyat / Muammo")],
    ],
    resize_keyboard=True,
)

back_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="⬅️ Ortga")]],
    resize_keyboard=True,
)


def vip_plans_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=f"{p['name']} — {p['price']}", callback_data=f"vipplan_{key}")]
        for key, p in VIP_PLANS.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ----------------------------------------------------------
#  /start
# ----------------------------------------------------------
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    welcome_text = (
        f"<b>Assalomu alaykum, {message.from_user.first_name}!</b> ✨\n\n"
        "🍿 <b>Anime & Cinema Botiga xush kelibsiz!</b>\n"
        "Kino kodini yuboring va tomosha qiling!\n\n"
        "<i>VIP a'zolar esa eng yangi premyera treylerlarini 1-bo'lib olishadi!</i>"
    )
    kb = admin_keyboard if message.from_user.id == OWNER_ID else user_keyboard
    await message.answer(welcome_text, reply_markup=kb, parse_mode="HTML")


# ============================================================
#  🎬 KINO QO'SHISH JARAYONI (orqaga tugmasi + validatsiya bilan)
# ============================================================

@dp.message(F.text == "⚡ Kino Qo'shish & Treyler")
async def start_add_movie(message: types.Message, state: FSMContext):
    await state.set_state(AddMovieState.waiting_for_code)
    await message.answer(
        "🔑 <b>Yangi kino uchun KOD kiriting:</b>\n<i>(Faqat raqam, masalan: 101)</i>",
        reply_markup=back_keyboard,
        parse_mode="HTML",
    )


async def cancel_add_movie(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("↩️ Kino qo'shish bekor qilindi.", reply_markup=admin_keyboard)


# --- KOD bosqichi ---
@dp.message(AddMovieState.waiting_for_code, F.text == "⬅️ Ortga")
async def code_back(message: types.Message, state: FSMContext):
    await cancel_add_movie(message, state)


@dp.message(AddMovieState.waiting_for_code)
async def process_code(message: types.Message, state: FSMContext):
    code = (message.text or "").strip()
    if not code.isdigit():
        await message.answer(
            "⚠️ <b>Xato buyruq!</b> Kod faqat raqamlardan iborat bo'lishi kerak.\n"
            "🔑 Iltimos, kino KODINI qayta kiriting:",
            reply_markup=back_keyboard,
            parse_mode="HTML",
        )
        return
    await state.update_data(code=code)
    await state.set_state(AddMovieState.waiting_for_title)
    await message.answer(
        "📝 <b>Kino NOMINI kiriting:</b>\n<i>(Masalan: Attack on Titan)</i>",
        reply_markup=back_keyboard,
        parse_mode="HTML",
    )


# --- NOM bosqichi ---
@dp.message(AddMovieState.waiting_for_title, F.text == "⬅️ Ortga")
async def title_back(message: types.Message, state: FSMContext):
    await cancel_add_movie(message, state)


@dp.message(AddMovieState.waiting_for_title, F.text)
async def process_title(message: types.Message, state: FSMContext):
    title = message.text.strip()
    await state.update_data(title=title)
    await state.set_state(AddMovieState.waiting_for_video)
    await message.answer(
        "📹 <b>Kino VIDEO faylini yuboring:</b>",
        reply_markup=back_keyboard,
        parse_mode="HTML",
    )


@dp.message(AddMovieState.waiting_for_title)
async def process_title_invalid(message: types.Message):
    await message.answer(
        "⚠️ <b>Xato buyruq!</b> Kino nomini matn ko'rinishida yuboring.\n"
        "📝 Kino NOMINI qayta kiriting:",
        reply_markup=back_keyboard,
        parse_mode="HTML",
    )


# --- VIDEO bosqichi ---
@dp.message(AddMovieState.waiting_for_video, F.text == "⬅️ Ortga")
async def video_back(message: types.Message, state: FSMContext):
    await cancel_add_movie(message, state)


@dp.message(AddMovieState.waiting_for_video, F.video)
async def process_video(message: types.Message, state: FSMContext):
    await state.update_data(file_id=message.video.file_id)
    await state.set_state(AddMovieState.waiting_for_trailer)
    await message.answer(
        "🍿 <b>Endi kino TREYLERINI (video fayl) yuboring:</b>\n"
        "<i>Havola emas, to'g'ridan-to'g'ri treyler videosini yuboring.</i>",
        reply_markup=back_keyboard,
        parse_mode="HTML",
    )


@dp.message(AddMovieState.waiting_for_video)
async def process_video_invalid(message: types.Message):
    await message.answer(
        "⚠️ <b>Xato buyruq!</b> Bu bosqichda faqat VIDEO fayl yuborilishi kerak.\n"
        "📹 Kino VIDEO faylini qayta yuboring:",
        reply_markup=back_keyboard,
        parse_mode="HTML",
    )


# --- TREYLER bosqichi ---
@dp.message(AddMovieState.waiting_for_trailer, F.text == "⬅️ Ortga")
async def trailer_back(message: types.Message, state: FSMContext):
    await cancel_add_movie(message, state)


@dp.message(AddMovieState.waiting_for_trailer, F.video)
async def process_trailer(message: types.Message, state: FSMContext):
    global CHANNEL_NOTICE_SHOWN

    trailer_file_id = message.video.file_id
    data = await state.get_data()
    code = data["code"]
    title = data["title"]
    file_id = data["file_id"]

    MOVIES[code] = {
        "title": title,
        "file_id": file_id,
        "trailer_file_id": trailer_file_id,
    }

    await state.clear()
    await message.answer(
        f"✅ <b>Kino muvaffaqiyatli saqlandi!</b>\n\n🔑 Kodi: <code>{code}</code>\n🎬 Nomi: {title}",
        reply_markup=admin_keyboard,
        parse_mode="HTML",
    )

    # Treylerni maxfiy kanalga avtomatik joylash
    try:
        await bot.send_video(
            chat_id=TRAILER_CHANNEL_ID,
            video=trailer_file_id,
            caption=f"🍿 <b>{title}</b>\n🔑 Kod: <code>{code}</code>",
            parse_mode="HTML",
        )
        if not CHANNEL_NOTICE_SHOWN:
            await message.answer(
                "ℹ️ Bundan buyon barcha treylerlar avtomatik ravishda maxfiy kanalga "
                "joylanadi. Bu haqda faqat shu safar xabar beriladi."
            )
            CHANNEL_NOTICE_SHOWN = True
    except Exception as e:
        await message.answer(
            f"⚠️ Treylerni kanalga joylashda xatolik yuz berdi: {e}\n"
            "Bot kanalga admin qilib qo'shilganini va TRAILER_CHANNEL_ID to'g'ri "
            "ekanini tekshiring."
        )

    # VIP a'zolarga bildirishnoma
    vip_text = (
        "🎉 <b>YANGI PREMYERA YUKLANDI!</b> (VIP Bildirishnoma)\n\n"
        f"🎬 <b>Nomi:</b> {title}\n"
        f"🔑 <b>Kino kodi:</b> <code>{code}</code>\n\n"
        "<i>Siz VIP a'zo bo'lganingiz uchun bu bildirishnoma 1-bo'lib sizga yetib keldi!</i> 🚀"
    )
    for vip_id in VIP_USERS:
        try:
            await bot.send_message(chat_id=vip_id, text=vip_text, parse_mode="HTML")
        except Exception:
            pass


@dp.message(AddMovieState.waiting_for_trailer)
async def process_trailer_invalid(message: types.Message):
    await message.answer(
        "⚠️ <b>Xato buyruq!</b> Bu bosqichda faqat TREYLER VIDEOsi yuborilishi kerak "
        "(havola emas).\n🍿 Treyler videosini qayta yuboring:",
        reply_markup=back_keyboard,
        parse_mode="HTML",
    )


# ============================================================
#  💎 VIP OBUNA JARAYONI (narx -> ulash -> karta -> skrinshot -> tasdiqlash)
# ============================================================

@dp.message(F.text == "💎 VIP Obuna Haqida")
async def vip_info(message: types.Message):
    await message.answer(
        "💎 <b>VIP obuna</b> orqali siz eng yangi premyera treylerlarini birinchi "
        "bo'lib olasiz!\n\nQuyidagi tariflardan birini tanlang:",
        reply_markup=vip_plans_kb(),
        parse_mode="HTML",
    )


@dp.callback_query(F.data.startswith("vipplan_"))
async def vip_plan_selected(callback: types.CallbackQuery):
    plan_key = callback.data.split("_", 1)[1]
    plan = VIP_PLANS.get(plan_key)
    if not plan:
        await callback.answer("Xatolik yuz berdi", show_alert=True)
        return
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Ulash", callback_data=f"vipbuy_{plan_key}")],
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="vipback")],
        ]
    )
    await callback.message.edit_text(
        f"💎 <b>{plan['name']}</b>\nNarxi: <b>{plan['price']}</b>\n\n"
        "Ushbu tarifga obuna bo'lish uchun \"💳 Ulash\" tugmasini bosing.",
        reply_markup=kb,
        parse_mode="HTML",
    )
    await callback.answer()


@dp.callback_query(F.data == "vipback")
async def vip_back(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "💎 <b>VIP obuna</b> orqali siz eng yangi premyera treylerlarini birinchi "
        "bo'lib olasiz!\n\nQuyidagi tariflardan birini tanlang:",
        reply_markup=vip_plans_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("vipbuy_"))
async def vip_buy(callback: types.CallbackQuery, state: FSMContext):
    plan_key = callback.data.split("_", 1)[1]
    plan = VIP_PLANS.get(plan_key)
    if not plan:
        await callback.answer("Xatolik yuz berdi", show_alert=True)
        return

    cards_text = "\n".join(
        f"💳 <b>{c['bank']}</b>: <code>{c['number']}</code> ({c['owner']})" for c in CARDS
    )
    text = (
        f"💎 <b>{plan['name']}</b> — {plan['price']}\n\n"
        f"To'lovni quyidagi kartalardan biriga o'tkazing:\n\n{cards_text}\n\n"
        "✅ To'lovni amalga oshirgach, <b>chek skrinshotini shu yerga rasm qilib yuboring.</b>"
    )
    await state.update_data(vip_plan=plan_key)
    await state.set_state(VipState.waiting_for_screenshot)
    await callback.message.answer(text, reply_markup=back_keyboard, parse_mode="HTML")
    await callback.answer()


@dp.message(VipState.waiting_for_screenshot, F.text == "⬅️ Ortga")
async def vip_screenshot_back(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("↩️ Bekor qilindi.", reply_markup=user_keyboard)


@dp.message(VipState.waiting_for_screenshot, F.photo)
async def vip_screenshot(message: types.Message, state: FSMContext):
    data = await state.get_data()
    plan = VIP_PLANS.get(data.get("vip_plan"), {"name": "Noma'lum", "price": "-"})
    await state.clear()

    await message.answer(
        "✅ Skrinshot qabul qilindi! Tez orada tekshirib, VIP obunangiz faollashtiriladi.",
        reply_markup=user_keyboard,
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"vipok_{message.from_user.id}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"vipno_{message.from_user.id}"),
            ]
        ]
    )
    caption = (
        "💳 <b>Yangi VIP to'lov so'rovi!</b>\n\n"
        f"👤 Foydalanuvchi: {message.from_user.full_name}\n"
        f"🆔 ID: <code>{message.from_user.id}</code>\n"
        f"💎 Tarif: {plan['name']} — {plan['price']}"
    )
    try:
        await bot.send_photo(
            chat_id=OWNER_ID,
            photo=message.photo[-1].file_id,
            caption=caption,
            reply_markup=kb,
            parse_mode="HTML",
        )
    except Exception as e:
        await message.answer(f"⚠️ Administratorga yuborishda xatolik: {e}")


@dp.message(VipState.waiting_for_screenshot)
async def vip_screenshot_invalid(message: types.Message):
    await message.answer(
        "⚠️ <b>Xato buyruq!</b> Iltimos, to'lov chekining skrinshotini RASM ko'rinishida yuboring.",
        reply_markup=back_keyboard,
        parse_mode="HTML",
    )


@dp.callback_query(F.data.startswith("vipok_"))
async def vip_approve(callback: types.CallbackQuery):
    if callback.from_user.id != OWNER_ID:
        await callback.answer("Sizda ruxsat yo'q", show_alert=True)
        return
    user_id = int(callback.data.split("_", 1)[1])
    VIP_USERS.add(user_id)

    old_caption = callback.message.caption or ""
    await callback.message.edit_caption(caption=old_caption + "\n\n✅ <b>TASDIQLANDI</b>", parse_mode="HTML")
    try:
        await bot.send_message(user_id, "🎉 Tabriklaymiz! Sizning VIP obunangiz faollashtirildi.")
    except Exception:
        pass
    await callback.answer("Tasdiqlandi ✅")


@dp.callback_query(F.data.startswith("vipno_"))
async def vip_reject(callback: types.CallbackQuery):
    if callback.from_user.id != OWNER_ID:
        await callback.answer("Sizda ruxsat yo'q", show_alert=True)
        return
    user_id = int(callback.data.split("_", 1)[1])

    old_caption = callback.message.caption or ""
    await callback.message.edit_caption(caption=old_caption + "\n\n❌ <b>RAD ETILDI</b>", parse_mode="HTML")
    try:
        await bot.send_message(
            user_id,
            "❌ Afsuski, to'lovingiz tasdiqlanmadi.\n"
            "Agar bu xato deb hisoblasangiz, \"🆘 Shikoyat / Muammo\" tugmasi orqali "
            "administratorga yozing.",
        )
    except Exception:
        pass
    await callback.answer("Rad etildi ❌")


# ============================================================
#  🆘 SHIKOYAT / MUAMMO
# ============================================================

@dp.message(F.text == "🆘 Shikoyat / Muammo")
async def start_complaint(message: types.Message, state: FSMContext):
    await state.set_state(ComplaintState.waiting_for_text)
    await message.answer(
        "✍️ Muammoyingiz yoki shikoyatingizni yozing, men uni administratorga yuboraman:",
        reply_markup=back_keyboard,
    )


@dp.message(ComplaintState.waiting_for_text, F.text == "⬅️ Ortga")
async def complaint_back(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("↩️ Bekor qilindi.", reply_markup=user_keyboard)


@dp.message(ComplaintState.waiting_for_text, F.text)
async def process_complaint(message: types.Message, state: FSMContext):
    await state.clear()
    try:
        await bot.send_message(
            OWNER_ID,
            "🆘 <b>Yangi shikoyat/muammo!</b>\n\n"
            f"👤 Foydalanuvchi: {message.from_user.full_name}\n"
            f"🆔 ID: <code>{message.from_user.id}</code>\n\n"
            f"✉️ Xabar:\n{message.text}",
            parse_mode="HTML",
        )
        await message.answer("✅ Xabaringiz administratorga yuborildi. Tez orada javob berishadi.", reply_markup=user_keyboard)
    except Exception as e:
        await message.answer(f"⚠️ Yuborishda xatolik: {e}", reply_markup=user_keyboard)


@dp.message(ComplaintState.waiting_for_text)
async def process_complaint_invalid(message: types.Message):
    await message.answer("⚠️ Iltimos, shikoyatingizni matn ko'rinishida yozing.", reply_markup=back_keyboard)


# ============================================================
#  🛠 ESKI BO'LIMLAR
# ============================================================

@dp.message(F.text == "📊 Statistika")
async def show_stats(message: types.Message):
    await message.answer(
        f"📊 <b>Bot statistikasi:</b>\n\n"
        f"🎬 Jami kinolar: <b>{len(MOVIES)} ta</b>\n"
        f"💎 VIP foydalanuvchilar: <b>{len(VIP_USERS)} ta</b>\n"
        f"🚫 Bloklanganlar: <b>{len(BLOCKED_USERS)} ta</b>",
        parse_mode="HTML",
    )


@dp.message(F.text == "🗑️ Kino o'chirish")
async def delete_movie(message: types.Message):
    await message.answer(
        "🗑️ Kino o'chirish bo'limi...\n<i>O'chirmoqchi bo'lgan kino kodini kiriting.</i>",
        parse_mode="HTML",
    )


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
        parse_mode="HTML",
    )


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
    code = (message.text or "").strip()
    if code in MOVIES:
        movie = MOVIES[code]
        await message.answer_video(
            video=movie["file_id"],
            caption=f"🎬 <b>{movie['title']}</b>\n\n🍿 Maroqli hordiq chiqaring!",
            parse_mode="HTML",
        )
    else:
        await message.answer(
            f"Siz yozdingiz: {message.text}\n\n<i>Kino kodi kiritilsa kino chiqarib beriladi!</i>",
            parse_mode="HTML",
        )


# ----------------------------------------------------------
async def main():
    logging.basicConfig(level=logging.INFO)
    print("Bot ishga tushdi...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
