import os
import re
import json
import logging
import asyncio
import requests
import ccxt
import httpx
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    ContextTypes, PicklePersistence, CallbackQueryHandler
)
from dotenv import load_dotenv

# ==================== CONFIGURATION ====================
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
CMC_API_KEY = os.getenv("CMC_API_KEY")
BITGET_API_KEY = os.getenv("BITGET_API_KEY")
BITGET_SECRET = os.getenv("BITGET_SECRET")

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== DATA FETCHING ====================

async def fetch_cmc_data(coin_symbol):
    """Get coin info from CoinMarketCap by symbol (e.g., 'BTC')."""
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    params = {"symbol": coin_symbol.upper(), "convert": "USD"}
    headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            data = response.json()
            if response.status_code == 200:
                coin_data = data["data"][coin_symbol.upper()]
                quote = coin_data["quote"]["USD"]
                return {
                    "price": quote["price"],
                    "volume_24h": quote["volume_24h"],
                    "percent_change_24h": quote["percent_change_24h"],
                    "market_cap": quote["market_cap"],
                    "cmc_rank": coin_data["cmc_rank"]
                }
            else:
                logger.error(f"CMC error: {data}")
                return None
    except Exception as e:
        logger.error(f"CMC fetch exception: {e}")
        return None

async def fetch_bitget_data(symbol):
    """Get ticker from Bitget for a trading pair like 'BTC/USDT'."""
    try:
        exchange = ccxt.bitget({
            'apiKey': BITGET_API_KEY,
            'secret': BITGET_SECRET,
            'enableRateLimit': True,
        })
        ticker = exchange.fetch_ticker(symbol)
        return {
            "price": ticker["last"],
            "high_24h": ticker["high"],
            "low_24h": ticker["low"],
            "volume": ticker["baseVolume"],
            "bid": ticker["bid"],
            "ask": ticker["ask"]
        }
    except Exception as e:
        logger.error(f"Bitget error: {e}")
        return None

async def fetch_data_for_coins(symbols):
    """Fetch CMC and Bitget data for a list of coin symbols."""
    tasks = []
    for sym in symbols:
        cmc_task = fetch_cmc_data(sym)
        bitget_task = fetch_bitget_data(f"{sym}/USDT")
        tasks.append((sym, cmc_task, bitget_task))

    results = []
    for sym, cmc_task, bitget_task in tasks:
        cmc_data, bitget_data = await asyncio.gather(cmc_task, bitget_task, return_exceptions=True)
        if isinstance(cmc_data, Exception) or cmc_data is None:
            cmc_data = None
        if isinstance(bitget_data, Exception) or bitget_data is None:
            bitget_data = None
        results.append((sym, cmc_data, bitget_data))
    return results

# ==================== COIN DETECTION ====================

def extract_coin_symbols(text):
    """Extract likely coin symbols (2-5 uppercase letters) from text."""
    candidates = re.findall(r'\b([A-Z]{2,5})\b', text)
    # Common non‑coin words to ignore
    ignore = {"I", "A", "TO", "IN", "ON", "AT", "BY", "FOR", "THE", "AND", "OR"}
    return [c for c in candidates if c not in ignore]

# ==================== GROQ AI ====================

async def call_groq(prompt):
    """Send prompt to Groq and return Burmese response."""
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    messages = [
        {"role": "system", "content": "You are a helpful crypto assistant. Always respond in Burmese (Myanmar language)."},
        {"role": "user", "content": prompt}
    ]
    payload = {
        "model": "groq/compound",  # Working free model (change if needed)
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 800
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            result = resp.json()
            return result["choices"][0]["message"]["content"].strip()
    except httpx.HTTPStatusError as e:
        logger.error(f"Groq HTTP error: {e.response.status_code} - {e.response.text}")
        return "စနစ်အမှားရှိနေပါသည်။ နောက်မှထပ်ကြိုးစားပါ။"
    except Exception as e:
        logger.error(f"Groq error: {e}", exc_info=True)
        return "စနစ်အမှားရှိနေပါသည်။ နောက်မှထပ်ကြိုးစားပါ။"

# ==================== COMMAND HANDLERS ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Inline keyboard
    keyboard = [
        [InlineKeyboardButton("💰 Price", callback_data='price'),
         InlineKeyboardButton("📊 Portfolio", callback_data='portfolio')],
        [InlineKeyboardButton("🏆 Top 10", callback_data='top'),
         InlineKeyboardButton("📈 Fear & Greed", callback_data='fng')],
        [InlineKeyboardButton("🔔 Alerts", callback_data='alerts'),
         InlineKeyboardButton("❓ Help", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "မင်္ဂလာပါ! ကျွန်ုပ်သည် crypto အကူအညီပေးသော bot ဖြစ်ပါသည်။\n"
        "သင်ဘာသိချင်ပါသလဲ? ဥပမာ - BTC ဈေးနှုန်း၊ ETH ရှယ်လိုလား၊ SOL ခွဲခြမ်းစိတ်ဖြာချက် စသည်ဖြင့် မေးမြန်းနိုင်ပါသည်။\n"
        "ကျွန်ုပ်သည် မြန်မာလိုဖြေကြားပေးပါမည်။",
        reply_markup=reply_markup
    )

async def alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Usage: /alert BTC above 50000"""
    try:
        coin = context.args[0].upper()
        direction = context.args[1].lower()  # "above" or "below"
        target_price = float(context.args[2])
        
        if direction not in ("above", "below"):
            await update.message.reply_text("Direction must be 'above' or 'below'.")
            return
        
        if 'alerts' not in context.user_data:
            context.user_data['alerts'] = []
        
        context.user_data['alerts'].append({
            'coin': coin,
            'direction': direction,
            'target': target_price,
            'created': datetime.now().isoformat()
        })
        
        await update.message.reply_text(f"✅ Alert set: {coin} {direction} ${target_price}")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /alert BTC above 50000")

async def check_alerts(context: ContextTypes.DEFAULT_TYPE):
    """Background task to check price alerts (call every minute)."""
    logger.info("Checking alerts...")
    # Implement actual checking logic here if needed

async def add_holding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add a holding: /add 0.5 BTC at 40000"""
    try:
        args = context.args
        if len(args) < 3:
            raise ValueError
        
        amount = float(args[0])
        coin = args[1].upper()
        if args[2].lower() == "at":
            price_index = 3
        else:
            price_index = 2
        buy_price = float(args[price_index])
        
        if 'portfolio' not in context.user_data:
            context.user_data['portfolio'] = []
        
        context.user_data['portfolio'].append({
            'coin': coin,
            'amount': amount,
            'buy_price': buy_price,
            'date': datetime.now().isoformat()
        })
        
        await update.message.reply_text(f"✅ Added {amount} {coin} at ${buy_price}")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /add 0.5 BTC at 40000 (or /add 0.5 BTC 40000)")

async def portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show portfolio with current P/L"""
    if 'portfolio' not in context.user_data or not context.user_data['portfolio']:
        await update.message.reply_text("Your portfolio is empty. Use /add to add holdings.")
        return
    
    total_value = 0
    total_cost = 0
    response = "📊 **Your Portfolio**\n\n"
    
    for holding in context.user_data['portfolio']:
        cmc_data = await fetch_cmc_data(holding['coin'])
        if cmc_data:
            current_price = cmc_data['price']
            current_value = holding['amount'] * current_price
            cost_basis = holding['amount'] * holding['buy_price']
            profit = current_value - cost_basis
            profit_pct = (profit / cost_basis) * 100 if cost_basis else 0
            
            response += f"• {holding['amount']} {holding['coin']}\n"
            response += f"  Buy: ${holding['buy_price']:.2f} | Now: ${current_price:.2f}\n"
            response += f"  P/L: ${profit:.2f} ({profit_pct:+.1f}%)\n\n"
            
            total_value += current_value
            total_cost += cost_basis
        else:
            response += f"• {holding['amount']} {holding['coin']} – price unavailable\n"
    
    if total_cost:
        total_profit = total_value - total_cost
        total_profit_pct = (total_profit / total_cost) * 100
        response += f"**Total Value:** ${total_value:.2f}\n"
        response += f"**Total P/L:** ${total_profit:.2f} ({total_profit_pct:+.1f}%)"
    
    await update.message.reply_text(response, parse_mode='Markdown')

async def fng(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show Fear & Greed Index"""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get("https://api.alternative.me/fng/?limit=1")
            data = resp.json()
            
            value = int(data['data'][0]['value'])
            classification = data['data'][0]['value_classification']
            
            bar = "█" * (value // 10) + "░" * (10 - (value // 10))
            
            response = f"**Fear & Greed Index**\n\n"
            response += f"{bar} {value}/100\n"
            response += f"**Classification:** {classification}\n"
            response += f"**Date:** {data['data'][0]['timestamp']}"
            
            await update.message.reply_text(response, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"FNG error: {e}")
        await update.message.reply_text("Failed to fetch Fear & Greed Index")

async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show top 10 cryptocurrencies"""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.coingecko.com/api/v3/coins/markets",
                params={
                    'vs_currency': 'usd',
                    'order': 'market_cap_desc',
                    'per_page': 10,
                    'page': 1,
                    'sparkline': False
                }
            )
            coins = resp.json()
            
            response = "🏆 **Top 10 Cryptocurrencies**\n\n"
            for i, coin in enumerate(coins, 1):
                change = coin['price_change_percentage_24h']
                arrow = "🟢" if change and change > 0 else "🔴"
                response += f"{i}. {coin['symbol'].upper()}\n"
                response += f"   ${coin['current_price']:,.2f} {arrow} {change:+.2f}%\n"
                response += f"   MCap: ${coin['market_cap']:,.0f}\n\n"
            
            await update.message.reply_text(response, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Top coins error: {e}")
        await update.message.reply_text("Failed to fetch top coins")

async def myprofile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data:
        lines = []
        if 'favorite_coin' in context.user_data:
            lines.append(f"• Favorite coin: {context.user_data['favorite_coin']}")
        if 'alerts' in context.user_data:
            lines.append(f"• Alerts: {len(context.user_data['alerts'])} active")
        if 'portfolio' in context.user_data:
            lines.append(f"• Portfolio: {len(context.user_data['portfolio'])} holdings")
        if not lines:
            lines = ["No data stored."]
        await update.message.reply_text("📋 သင်၏ သိမ်းဆည်းထားချက်များ:\n" + "\n".join(lines))
    else:
        await update.message.reply_text("📭 သင့်အတွက် သိမ်းဆည်းထားချက် မရှိပါ။")

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("🔄 သင်၏ သိမ်းဆည်းထားချက်များကို ရှင်းလင်းပြီးပါပြီ။")

# ==================== MESSAGE HANDLER ====================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    logger.info(f"Received message: {user_text}")

    # Detect if user is setting a favorite coin
    favorite_phrases = ["my favorite coin", "i like", "i prefer", "favorite is"]
    lower_text = user_text.lower()
    for phrase in favorite_phrases:
        if phrase in lower_text:
            symbols = extract_coin_symbols(user_text)
            if symbols:
                context.user_data['favorite_coin'] = symbols[0]
                await update.message.reply_text(
                    f"✅ သင်နှစ်သက်သော coin ကို {symbols[0]} အဖြစ် မှတ်သားပြီးပါပြီ။"
                )
            else:
                await update.message.reply_text(
                    "❌ coin အတိအကျ ဖော်ပြပေးပါ။ (ဥပမာ - BTC, ETH)"
                )
                return
            break

    # Extract coin symbols from the whole message
    symbols = extract_coin_symbols(user_text)
    if not symbols and 'favorite_coin' in context.user_data:
        symbols = [context.user_data['favorite_coin']]
        await update.message.reply_text(
            f"⭐ သင်သိမ်းဆည်းထားသော {context.user_data['favorite_coin']} အတွက် အချက်အလက်ပြပေးပါမည်။"
        )

    # Fetch data for the detected coins
    data_text = ""
    if symbols:
        await update.message.reply_text("🔄 ဒေတာရယူနေပါသည်...")
        fetched = await fetch_data_for_coins(symbols)
        for sym, cmc, bitget in fetched:
            data_text += f"\n--- {sym} Data ---\n"
            if cmc:
                data_text += (
                    f"• CMC: ${cmc['price']:.2f} | 24h: {cmc['percent_change_24h']:.2f}% | "
                    f"Rank: #{cmc['cmc_rank']}\n"
                )
            else:
                data_text += "• CMC data unavailable.\n"
            if bitget:
                data_text += (
                    f"• Bitget: ${bitget['price']:.2f} | 24h High/Low: "
                    f"${bitget['high_24h']:.2f}/${bitget['low_24h']:.2f}\n"
                )
            else:
                data_text += "• Bitget data unavailable.\n"
    else:
        data_text = "No specific coin data requested."

    # Build the AI prompt with context
    fav_info = f"User's favorite coin: {context.user_data.get('favorite_coin', 'not set')}."
    prompt = f"""User query: {user_text}
{fav_info}
Available market data:
{data_text}

Answer conversationally, using the data if relevant. If analysis or trading suggestions are asked, give insights. Always respond in Burmese.
"""
    reply = await call_groq(prompt)
    await update.message.reply_text(reply)

# ==================== CALLBACK QUERY HANDLER (for inline keyboards) ====================
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data == 'price':
        await query.edit_message_text("💰 Use /price [coin] to get current price.\nExample: /price BTC")
    elif data == 'portfolio':
        await query.edit_message_text("📊 Use /portfolio to view your holdings.\nAdd holdings with /add 0.5 BTC at 40000")
    elif data == 'top':
        await query.edit_message_text("🏆 Use /top to see top 10 cryptocurrencies.")
    elif data == 'fng':
        await query.edit_message_text("📈 Use /fng to see the Fear & Greed Index.")
    elif data == 'alerts':
        await query.edit_message_text("🔔 Use /alert [coin] above/below [price] to set alerts.\nExample: /alert BTC above 50000")
    elif data == 'help':
        await query.edit_message_text(
            "❓ **Available Commands**\n\n"
            "/price [coin] - Get current price\n"
            "/alert [coin] above/below [price] - Set price alert\n"
            "/add [amount] [coin] at [price] - Add holding\n"
            "/portfolio - View portfolio\n"
            "/top - Top 10 cryptocurrencies\n"
            "/fng - Fear & Greed Index\n"
            "/myprofile - Your saved data\n"
            "/reset - Clear all your data\n"
            "/start - Show welcome menu"
        )

# ==================== MAIN ====================

def main():
    # Enable persistence so user_data survives restarts
    persistence = PicklePersistence(filepath="bot_data.pickle")
    app = Application.builder().token(TELEGRAM_TOKEN).persistence(persistence).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("myprofile", myprofile))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("alert", alert))
    app.add_handler(CommandHandler("add", add_holding))
    app.add_handler(CommandHandler("portfolio", portfolio))
    app.add_handler(CommandHandler("fng", fng))
    app.add_handler(CommandHandler("top", top))

    # Message handler for all text messages (non-command)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Callback query handler for inline keyboard
    app.add_handler(CallbackQueryHandler(button_callback))

    # Optional: background job to check alerts every 60 seconds
    # job_queue = app.job_queue
    # job_queue.run_repeating(check_alerts, interval=60, first=10)

    logger.info("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
