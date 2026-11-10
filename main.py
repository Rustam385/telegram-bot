import logging
import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    LabeledPrice,
    PreCheckoutQuery
)

# ---------------- CONFIGURATION ----------------
BOT_TOKEN = "9296255738:AAGN8p1UNznhtx2iAESCnmsPkK0tPmmHoWg"
ADMIN_ID = 7640043499
ADMIN_USERNAME = "@mdvc1"

# Bot va Dispatcher yaratish
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

# Foydalanuvchilar balansi (Formati: {user_id: stars_balance})
user_balances = {}

# Giftlar ro'yxati (Nomi, Stars narxi)
GIFTS = {
    "gift_1": {"name": "Delicious Cake 🍰", "price": 15},
    "gift_2": {"name": "Red Rose 🌹", "price": 25},
    "gift_3": {"name": "Golden Star ⭐", "price": 50},
    "gift_4": {"name": "Diamond Ring 💍", "price": 100},
}

# ---------------- KEYBOARDS ----------------
def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎁 Giftlarni tanlash")],
            [KeyboardButton(text="💰 Balans"), KeyboardButton(text="ℹ️ Yordam")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_gifts_inline_keyboard():
    buttons = []
    for code, info in GIFTS.items():
        buttons.append([InlineKeyboardButton(text=f"{info['name']} — {info['price']} Stars ⭐", callback_data=f"buy_{code}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_balance_inline_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⭐ Telegram Stars orqali to'ldirish", callback_data="topup_stars")],
            [InlineKeyboardButton(text="💳 Karta orqali to'ldirish", callback_data="topup_card")]
        ]
    )

# ---------------- HANDLERS ----------------

# /start buyrug'i
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_balances:
        user_balances[user_id] = 0
        
    await message.answer(
        f"Xush kelibsiz, {message.from_user.first_name}!
"
        f"Bot orqali Telegram Giftlarini xarid qilishingiz mumkin.",
        reply_markup=get_main_keyboard()
    )

# 1-menyu: Giftlarni tanlash
@dp.message(F.text == "🎁 Giftlarni tanlash")
async def show_gifts(message: types.Message):
    await message.answer(
        "Mavjud Giftlar ro'yxati:
Sotib olmoqchi bo'lgan giftingizni tanlang:",
        reply_markup=get_gifts_inline_keyboard()
    )

# 2-menyu: Balans
@dp.message(F.text == "💰 Balans")
async def show_balance(message: types.Message):
    user_id = message.from_user.id
    balance = user_balances.get(user_id, 0)
    
    await message.answer(
        f"Sizning balansingiz: <b>{balance} Stars ⭐</b>

"
        f"Balansni to'ldirish usulini tanlang:",
        parse_mode="HTML",
        reply_markup=get_balance_inline_keyboard()
    )

# 3-menyu: Yordam
@dp.message(F.text == "ℹ️ Yordam")
async def show_help(message: types.Message):
    await message.answer(
        f"Shtatli va texnik savollar bo'yicha administratorga murojaat qiling:

"
        f"👤 Admin: {ADMIN_USERNAME}"
    )

# ---------------- GIFT SOTIB OLISH MANTIQLARI ----------------
@dp.callback_query(F.data.startswith("buy_"))
async def process_gift_buy(callback: types.CallbackQuery):
    gift_code = callback.data.split("_")[1] + "_" + callback.data.split("_")[2]
    user_id = callback.from_user.id
    user_balance = user_balances.get(user_id, 0)
    
    gift_info = GIFTS.get(gift_code)
    if not gift_info:
        await callback.answer("Gift topilmadi!", show_alert=True)
        return

    price = gift_info["price"]
    
    if user_balance < price:
        await callback.answer(f"Balansingizda yetarli Stars yo'q! Kerak: {price} Stars", show_alert=True)
        return
    
    # Balansdan yechish
    user_balances[user_id] -= price
    
    # Foydalanuvchiga tasdiq
    await callback.message.edit_text(
        f"✅ <b>{gift_info['name']}</b> uchun buyurtma qabul qilindi!
"
        f"Balansingizdan {price} Stars yechildi.

"
        f"Gift tez orada profilingizga yuboriladi.",
        parse_mode="HTML"
    )
    
    # Adminga xabar yuborish
    await bot.send_message(
        chat_id=ADMIN_ID,
        text=f"🛒 <b>Yangi Gift Buyurtmasi!</b>

"
             f"👤 Xaridor: @{callback.from_user.username} (ID: <code>{user_id}</code>)
"
             f"🎁 Gift: {gift_info['name']}
"
             f"💰 Narxi: {price} Stars",
        parse_mode="HTML"
    )
    await callback.answer()

# ---------------- BALANS TO'LDIRISH MANTIQLARI ----------------

# Stars orqali to'ldirish
@dp.callback_query(F.data == "topup_stars")
async def topup_stars_handler(callback: types.CallbackQuery):
    prices = [LabeledPrice(label="50 Stars Balans", amount=50)]
    
    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title="Bot balansini Stars bilan to'ldirish",
        description="50 Stars o'tkazish orqali bot balansingizni to'ldiring.",
        payload="topup_50_stars",
        currency="XTR",
        prices=prices
    )
    await callback.answer()

# Pre-checkout query
@dp.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

# Muvaffaqiyatli Stars to'lovi
@dp.message(F.successful_payment)
async def process_successful_payment(message: types.Message):
    user_id = message.from_user.id
    stars_added = message.successful_payment.total_amount
    
    user_balances[user_id] = user_balances.get(user_id, 0) + stars_added
    
    await message.answer(
        f"🎉 To'lov muvaffaqiyatli amalga oshirildi!
"
        f"Balansingizga <b>+{stars_added} Stars</b> qo'shildi.",
        parse_mode="HTML"
    )

# Karta orqali to'ldirish
@dp.callback_query(F.data == "topup_card")
async def topup_card_handler(callback: types.CallbackQuery):
    await callback.message.edit_text(
        f"💳 <b>Karta orqali to'ldirish:</b>

"
        f"Karta raqami: <code>8600 0000 0000 0000</code>
"
        f"Ega: Rustamjon M.

"
        f"<i>Izoh: 1 Star = 300 so'm deb hisoblanadi.</i>

"
        f"To'lov qilgach, chekni admin {ADMIN_USERNAME} ga yuboring. Balansingiz adminga tasdiqlangach Stars ko'rinishida qo'shiladi.",
        parse_mode="HTML"
    )
    await callback.answer()

# ---------------- BOTNI ISHGA TUSHIRISH ----------------
async def main():
    print("Bot muvaffaqiyatli ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
