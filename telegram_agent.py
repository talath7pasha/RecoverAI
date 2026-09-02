import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from db_logger import log_transaction

BOT_TOKEN = "8888498228:AAEHn4piF6dzTgHyou1saA_fdZdKUfs8abo"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

BASE_AMOUNT = 6500.0
CALCULATED_COINS = int(BASE_AMOUNT * 0.10)  # 650 Coins (10%)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 RecoverAI Smart Payment Assistant\n\n"
        f"We noticed your payment of ₹{BASE_AMOUNT:,.2f} for Order #REC-9821 failed.\n\n"
        "How would you like to resolve this?\n"
        f"• Reply 'Coins' -> Earn {CALCULATED_COINS} RecoverCoins (₹{CALCULATED_COINS/10:,.2f} on next order)\n"
        "• Reply 'Split' -> Pay in 2 zero-interest installments\n"
        "• Reply 'UPI' -> Get direct 1-Tap payment link"
    )
    await update.message.reply_text(welcome_text)

def process_nlp_and_log(user_text: str):
    text = user_text.lower().strip()
    
    # 1. RecoverCoins & Loyalty Perks
    if any(k in text for k in ["coin", "point", "reward", "offer", "discount", "cashback", "perk", "deal"]):
        log_transaction("Telegram", user_text, "RECOVER_COINS_APPLIED", BASE_AMOUNT, BASE_AMOUNT, 0.96)
        return (
            f"🪙 RecoverCoins Loyalty Perk Unlocked!\n\n"
            f"Complete your order of ₹{BASE_AMOUNT:,.2f} now and get:\n"
            f"🎁 +{CALCULATED_COINS} RecoverCoins credited to your wallet!\n"
            f"💰 Cash Value: ₹{CALCULATED_COINS/10:,.2f} redeemable on your NEXT purchase\n"
            f"🚀 FREE Priority Express Dispatch included\n\n"
            f"👉 Claim Coins & Pay: http://localhost:8501/?checkout_id=rec_tg_coins&amt={BASE_AMOUNT}&coins={CALCULATED_COINS}"
        )
    
    # 2. Split-Payment
    elif any(k in text for k in ["split", "part", "half", "two", "install"]):
        part_amount = BASE_AMOUNT / 2
        log_transaction("Telegram", user_text, "SPLIT_PAYMENT_RECOVERY", BASE_AMOUNT, part_amount, 0.95)
        return (
            f"✅ Split-Pay Approved!\n\n"
            f"• Part 1: ₹{part_amount:,.2f} (Due now)\n"
            f"• Part 2: ₹{part_amount:,.2f} (Due in 14 days)\n"
            f"🪙 You will still earn {CALCULATED_COINS} coins upon completion!\n\n"
            f"👉 Pay Part 1: http://localhost:8501/?checkout_id=rec_tg_01&amt={BASE_AMOUNT}&split=true&coins={CALCULATED_COINS}"
        )
        
    # 3. Direct 1-Tap UPI
    elif any(k in text for k in ["upi", "link", "pay", "gpay", "phonepe", "qr"]):
        log_transaction("Telegram", user_text, "ONE_TAP_UPI_ROUTING", BASE_AMOUNT, BASE_AMOUNT, 0.98)
        return (
            f"⚡ Direct 1-Tap UPI Link Generated:\n\n"
            f"👉 Pay via UPI: http://localhost:8501/?checkout_id=rec_tg_03&amt={BASE_AMOUNT}&coins={CALCULATED_COINS}"
        )
    
    # Fallback
    else:
        log_transaction("Telegram", user_text, "FALLBACK_GUIDANCE", BASE_AMOUNT, BASE_AMOUNT, 0.65, status="PENDING")
        return (
            f"I can help resolve your failed payment of ₹{BASE_AMOUNT:,.2f}.\n\n"
            f"1. Reply 'Coins' to earn {CALCULATED_COINS} wallet points\n"
            "2. Reply 'Split' to pay in two installments\n"
            "3. Reply 'UPI' for instant checkout"
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text
    bot_reply = process_nlp_and_log(user_msg)
    await update.message.reply_text(bot_reply)

def main():
    print("🚀 RecoverAI Telegram Agent is live and listening on Telegram...")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()