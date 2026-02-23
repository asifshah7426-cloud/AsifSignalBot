import logging
import json
import os
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)

# CONFIG
TOKEN = os.environ.get("BOT_TOKEN", "8694307351:AAEcxuNraLocVxmCBjrexD3CgAWDfBYMdFs")
ACCOUNT = 10000
RISK_PCT = 0.002
MAX_TRADES = 2
DAILY_LIMIT = 299.68

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_FILE = "trades.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"trades": []}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_today_trades():
    data = load_data()
    today = datetime.now().strftime("%Y-%m-%d")
    return [t for t in data["trades"] if t.get("date") == today]

def get_risk():
    trades = get_today_trades()
    pnl = sum(t.get("pnl", 0) for t in trades)
    return round((ACCOUNT + pnl) * RISK_PCT, 2)

def get_daily_pnl():
    return sum(t.get("pnl", 0) for t in get_today_trades())

def progress_bar(used, total):
    pct = min(used / total, 1.0)
    filled = int(pct * 10)
    return "▓" * filled + "░" * (10 - filled)

# CONVERSATION STATES
(ASK_PAIR, ASK_DIR, ASK_BIAS, ASK_EMA, ASK_INTERNAL,
 ASK_LQ, ASK_POI, ASK_SWEEP, ASK_BOS, ASK_FVG,
 ASK_MITIGATE, ASK_BLIND, ASK_LTF, ASK_RR,
 ASK_ENTRY, ASK_SL, CONFIRM_TRADE) = range(17)

user_data_store = {}

# ── START ────────────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    trades = get_today_trades()
    pnl = get_daily_pnl()
    risk = get_risk()
    daily_loss = abs(min(0, pnl))
    bar = progress_bar(daily_loss, DAILY_LIMIT)
    await update.message.reply_text(
        f"🤖 *ASIF SMART SIGNAL BOT*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👋 Salam Asif! Ready to find A+ setups!\n\n"
        f"📊 *TODAY'S STATUS*\n"
        f"💰 Balance: ${ACCOUNT + pnl:,.2f}\n"
        f"📈 Daily P&L: ${pnl:+.2f}\n"
        f"📋 Trades: {len(trades)}/{MAX_TRADES}\n"
        f"⚡ Risk/Trade: ${risk:.2f} (0.2%)\n"
        f"🛡 Daily Limit: {bar} ${daily_loss:.2f}/${DAILY_LIMIT}\n\n"
        f"*COMMANDS:*\n"
        f"/check — Run A+ Setup Checklist ✅\n"
        f"/status — Account status 📊\n"
        f"/performance — Win rate & stats 🏆\n"
        f"/log — Today's trades 📋\n"
        f"/rules — Your strategy 📖\n"
        f"/psychology — Brad Trades mindset 🧠\n"
        f"/help — All commands\n\n"
        f"_ICT/SMC + Brad Trades | Discipline = Edge_ 💪",
        parse_mode='Markdown'
    )

# ── HELP ─────────────────────────────────────────────────
async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 *ALL COMMANDS*\n"
        "━━━━━━━━━━━━━━━━\n"
        "/check — A+ Setup Checklist\n"
        "/status — Daily account status\n"
        "/performance — Win rate tracker\n"
        "/log — Today's trade log\n"
        "/rules — Full strategy rules\n"
        "/psychology — Mindset reminders\n"
        "/start — Welcome & overview\n"
        "/help — This menu",
        parse_mode='Markdown'
    )

# ── STATUS ───────────────────────────────────────────────
async def status_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    trades = get_today_trades()
    pnl = get_daily_pnl()
    daily_loss = abs(min(0, pnl))
    loss_pct = (daily_loss / DAILY_LIMIT) * 100
    risk = get_risk()
    bar = progress_bar(daily_loss, DAILY_LIMIT)
    emoji = "🚨" if loss_pct >= 80 else "⚠️" if loss_pct >= 50 else "✅"
    limit_msg = "🚨 TRADE LIMIT REACHED — NO MORE TRADES TODAY!" if len(trades) >= MAX_TRADES else f"✅ {MAX_TRADES - len(trades)} trade slot(s) available"
    await update.message.reply_text(
        f"{emoji} *ACCOUNT STATUS*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Balance: *${ACCOUNT + pnl:,.2f}*\n"
        f"📈 Daily P&L: *${pnl:+.2f}*\n"
        f"⚡ Risk/Trade: *${risk:.2f}* (0.2%)\n\n"
        f"📊 *DAILY LOSS METER*\n"
        f"{bar} {loss_pct:.1f}%\n"
        f"Used: ${daily_loss:.2f} / ${DAILY_LIMIT}\n\n"
        f"📋 Trades Today: *{len(trades)}/{MAX_TRADES}*\n"
        f"{limit_msg}",
        parse_mode='Markdown'
    )

# ── PERFORMANCE ──────────────────────────────────────────
async def performance_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    all_trades = [t for t in data["trades"] if t.get("pnl") is not None]
    wins = [t for t in all_trades if t.get("pnl", 0) > 0]
    losses = [t for t in all_trades if t.get("pnl", 0) < 0]
    total_profit = sum(t["pnl"] for t in wins)
    total_loss = abs(sum(t["pnl"] for t in losses))
    net = total_profit - total_loss
    wr = round((len(wins) / len(all_trades)) * 100, 1) if all_trades else 0
    wr_status = "✅ TARGET REACHED! Ready for funded!" if wr >= 65 else f"📈 Need {round(65 - wr, 1)}% more to reach 65%"
    sample = "🏆 VALID SAMPLE — READY FOR FUNDED ACCOUNT!" if wr >= 65 and len(all_trades) >= 20 else f"⏳ Need {max(0, 20 - len(all_trades))} more trades for valid sample"
    await update.message.reply_text(
        f"📊 *DEMO PERFORMANCE TRACKER*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 Target Win Rate: *65%*\n"
        f"📈 Current Win Rate: *{wr}%*\n"
        f"{wr_status}\n\n"
        f"📋 Total Trades: *{len(all_trades)}*\n"
        f"✅ Wins: *{len(wins)}*\n"
        f"❌ Losses: *{len(losses)}*\n\n"
        f"💰 Total Profit: *+${total_profit:.2f}*\n"
        f"🔻 Total Loss: *-${total_loss:.2f}*\n"
        f"💵 Net P&L: *${net:+.2f}*\n\n"
        f"{sample}",
        parse_mode='Markdown'
    )

# ── LOG ──────────────────────────────────────────────────
async def log_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    trades = get_today_trades()
    if not trades:
        await update.message.reply_text("📭 No trades logged today.\n\nUse /check to run your A+ checklist!")
        return
    msg = "📋 *TODAY'S TRADES*\n━━━━━━━━━━━━━━━━\n"
    for i, t in enumerate(trades, 1):
        pnl_str = f"${t['pnl']:+.2f}" if t.get("pnl") is not None else "🔄 OPEN"
        msg += (
            f"\n*Trade {i}:* {t.get('pair','?')} {t.get('direction','?')}\n"
            f"Entry: {t.get('entry','?')} | SL: {t.get('sl','?')}\n"
            f"TP: {t.get('tp','?')} | Risk: -${t.get('risk','?')}\n"
            f"Target: +${t.get('target','?')} | Result: {pnl_str}\n"
        )
    await update.message.reply_text(msg, parse_mode='Markdown')

# ── RULES ────────────────────────────────────────────────
async def rules_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *ASIF'S A+ SETUP RULES*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "*ICT/SMC + Brad Trades Framework*\n\n"
        "1️⃣ *BIAS FIRST*\n"
        "• HTF bullish (HH+HL) → BUY only\n"
        "• HTF bearish (LH+LL) → SELL only\n"
        "• 200 EMA confirms direction\n\n"
        "2️⃣ *IDENTIFY LIQUIDITY*\n"
        "• Mark swing highs/lows & trendlines\n"
        "• Trendline LQ = strongest form\n"
        "• POI must have LQ near it\n\n"
        "3️⃣ *WAIT FOR LQ SWEEP + BOS*\n"
        "• Price sweeps LQ then breaks structure\n"
        "• Strong displacement candle required\n\n"
        "4️⃣ *FVG FORMATION*\n"
        "• Imbalance left by displacement move\n"
        "• This is your entry zone (POI)\n\n"
        "5️⃣ *FVG MITIGATION*\n"
        "• Price returns to FVG (min 50%)\n"
        "• Watch for LTF LQ sweeps inside FVG\n\n"
        "6️⃣ *LTF ENTRY*\n"
        "• Aggressive: enter on LQ sweep candle\n"
        "• Conservative: wait for MS/Flip\n\n"
        "💰 *RISK: 0.2% = $20 | RR: 1:5 min*\n"
        "📋 *MAX 2 TRADES PER DAY*",
        parse_mode='Markdown'
    )

# ── PSYCHOLOGY ───────────────────────────────────────────
async def psychology_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🧠 *BRAD TRADES GOLDEN RULES*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "💡 The market is always right. Flow with it, not against it.\n\n"
        "⚡ When setup aligns — just execute. Stop overthinking!\n\n"
        "😴 Embrace boredom. Most losses come from trading choppy markets.\n\n"
        "🏆 Professional traders wait DAYS for the right setup.\n\n"
        "🚫 Never trade to prove yourself. Trade to make money.\n\n"
        "💸 You don't blow up from one bad trade. You bleed from trading after it.\n\n"
        "🔍 Always check blind spots — map every POI on 15M, 1H, 4H.\n\n"
        "🎯 Forget perfect entry. If momentum is strong and Rexcept:
        await update.message.reply_text("❌ Invalid price. Please enter a number like: 3285.50")
        return ASK_ENTRY

async def ask_sl(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    try:
        entry = user_data_store[uid]["entry"]
        sl = float(update.message.text.strip())
        user_data_store[uid]["sl"] = sl
        risk = get_risk()
        dist = abs(entry - sl)
        direction = user_data_store[uid]["direction"]
        tp1 = entry + dist * 5 if direction == "BUY" else entry - dist * 5
        tp2 = entry + dist * 6 if direction == "BUY" else entry - dist * 6
        target = round(risk * 5, 2)
        user_data_store[uid]["tp"] = round(tp1, 2)
        user_data_store[uid]["tp2"] = round(tp2, 2)
        user_data_store[uid]["risk"] = risk
        user_data_store[uid]["target"] = target

        await update.message.reply_text(
            f"📊 *TRADE SUMMARY*\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"Pair: *{user_data_store[uid]['pair']}*\n"
            f"Direction: *{direction}*\n"
            f"Entry: *{entry}*\n"
            f"Stop Loss: *{sl}*\n"
            f"TP1 (1:5): *{round(tp1, 2)}*\n"
            f"TP2 (1:6): *{round(tp2, 2)}*\n"
            f"Risk: *-${risk}*\n"
            f"Target: *+${target}*\n\n"
            f"✅ Confirm and log this trade?",
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardMarkup([["✅ YES — LOG TRADE", "❌ NO — CANCEL"]], one_time_keyboard=True, resize_keyboard=True)
        )
        return CONFIRM_TRADE
    except:
        await update.message.reply_text("❌ Invalid price. Please enter a number like: 3280.00")
        return ASK_SL

async def confirm_trade(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if "YES" in update.message.text:
        data = load_data()
        t = user_data_store[uid]
        trade = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%H:%M"),
            "pair": t["pair"],
            "direction": t["direction"],
            "entry": t["entry"],
            "sl": t["sl"],
            "tp": t["tp"],
            "risk": t["risk"],
            "target": t["target"],
            "result": "OPEN",
            "pnl": None
        }
        data["trades"].append(trade)
        save_data(data)
        trades_today = get_today_trades()
        await update.message.reply_text(
            f"✅ *TRADE LOGGED!*\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"{t['pair']} {t['direction']} @ {t['entry']}\n"
            f"SL: {t['sl']} | TP: {t['tp']}\n"
            f"Risk: -${t['risk']} | Target: +${t['target']}\n\n"
            f"📋 Trades today: {len(trades_today)}/{MAX_TRADES}\n"
            f"{'🚨 TRADE LIMIT REACHED — NO MORE TRADES TODAY!' if len(trades_today) >= MAX_TRADES else f'⚡ {MAX_TRADES - len(trades_today)} slot(s) remaining'}\n\n"
            f"_Use /log to view trades | /performance to track stats_",
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        await update.message.reply_text(
            "❌ Trade cancelled.\n\n_Stay patient — only A+ setups!_ 💪",
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardRemove()
        )
    user_data_store.pop(uid, None)
    return ConversationHandler.END

async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user_data_store.pop(uid, None)
    await update.message.reply_text("❌ Checklist cancelled.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# ── MAIN ─────────────────────────────────────────────────
def main():
    app = Application.builder().token(TOKEN).build()

    checklist_handler = ConversationHandler(
        entry_points=[CommandHandler("check", check_start)],
        states={
            ASK_PAIR:     [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_pair)],
            ASK_DIR:      [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_dir)],
            ASK_BIAS:     [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_bias)],
            ASK_EMA:      [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_ema)],
            ASK_INTERNAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_internal)],
            ASK_LQ:       [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_lq)],
            ASK_POI:      [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_poi)],
            ASK_SWEEP:    [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_sweep)],
            ASK_BOS:      [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_bos)],
            ASK_FVG:      [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_fvg)],
            ASK_MITIGATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_mitigate)],
            ASK_BLIND:    [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_blind)],
            ASK_LTF:      [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_ltf)],
            ASK_RR:       [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_rr)],
            ASK_ENTRY:    [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_entry)],
            ASK_SL:       [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_sl)],
            CONFIRM_TRADE:[MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_trade)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("performance", performance_cmd))
    app.add_handler(CommandHandler("log", log_cmd))
    app.add_handler(CommandHandler("rules", rules_cmd))
    app.add_handler(CommandHandler("psychology", psychology_cmd))
    app.add_handler(checklist_handler)

    print("🤖 Asif Signal Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
