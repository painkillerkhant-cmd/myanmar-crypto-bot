🤖 Myanmar Crypto Assistant Bot
A Telegram bot that provides cryptocurrency analysis, price alerts, portfolio tracking, and market insights – all in Myanmar (Burmese) language. Built with Python, it fetches live data from CoinMarketCap and Bitget, and uses Groq's groq/compound model (with unlimited tokens) to generate intelligent, conversational responses.

✨ Features
💬 Conversational AI – Chat naturally about any crypto topic; the bot responds in Burmese.

💰 Real‑time prices – Get current prices from CoinMarketCap and Bitget.

📊 Portfolio tracker – Add your holdings and see profit/loss instantly.

🔔 Price alerts – Set alerts for coins above/below a target price.

🏆 Top 10 cryptocurrencies – View market leaders with 24h changes.

📈 Fear & Greed Index – Gauges market sentiment.

⭐ Favorite coin memory – Tell the bot your favorite coin once, and it will use it when you forget to mention one.

📋 User profile – See your stored data (favorites, alerts, portfolio) with /myprofile.

🔄 Reset data – Clear all your preferences with /reset.

🎛️ Inline keyboard – Handy menu in the /start command.

🛠️ Technologies Used
Python 3.10+

python‑telegram‑bot – Telegram Bot API wrapper

Groq API – Fast inference with custom groq/compound model (unlimited tokens)

CoinMarketCap API – Market data (price, volume, rank)

Bitget (CCXT) – Exchange ticker data

CoinGecko API – Top 10 cryptocurrencies

Alternative.me API – Fear & Greed Index

python‑dotenv – Environment variable management

httpx & asyncio – Asynchronous HTTP requests

🚀 Getting Started
Prerequisites
Python 3.10 or higher

A Telegram Bot Token (from @BotFather)

A Groq API key (with access to groq/compound model) – sign up at console.groq.com

CoinMarketCap API key – free tier from coinmarketcap.com/api

(Optional) Bitget API key & secret – for exchange data (create with “read” permissions)

Installation
Clone the repository

bash
git clone https://github.com/yourusername/myanmar-crypto-bot.git
cd myanmar-crypto-bot
Create and activate a virtual environment

bash
python -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate
Install dependencies

bash
pip install python-telegram-bot httpx ccxt python-dotenv requests
Create a .env file in the project root with your API keys:

env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
GROQ_API_KEY=your_groq_api_key
CMC_API_KEY=your_coinmarketcap_api_key
BITGET_API_KEY=your_bitget_api_key      # optional
BITGET_SECRET=your_bitget_secret        # optional
Run the bot

bash
python bot.py
Start chatting with your bot on Telegram. Send /start to see the menu.

📱 Usage
Commands
Command	Description
/start	Welcome message with inline keyboard
/price BTC	Get current price of a coin
/alert BTC above 50000	Set a price alert
/add 0.5 BTC at 40000	Add a holding to your portfolio
/portfolio	Show your portfolio with profit/loss
/top	Display top 10 cryptocurrencies
/fng	Show Fear & Greed Index
/myprofile	View your stored data (favorites, alerts, portfolio)
/reset	Clear all your data
Natural Language Examples
“What’s the price of ETH?”

“I like Solana” (sets favorite coin)

“Should I buy Bitcoin now?”

“Compare BTC and ETH”

“Set alert for XRP above $2.5”

The bot will automatically detect coin symbols, fetch relevant data, and reply in Burmese.

⚙️ Configuration
All settings are managed via environment variables in the .env file. If you don't have Bitget keys, the bot will still work using only CoinMarketCap data.

Customizing the AI Model
By default, the bot uses the groq/compound model (as shown in your Groq account). If you prefer a different model, change the "model" field in the call_groq function inside bot.py:

python
payload = {
    "model": "your-preferred-model",   # e.g., "llama-3.3-70b-versatile"
    "messages": messages,
    "temperature": 0.7,
    "max_tokens": 800
}
🧪 Testing
After starting the bot, open Telegram and send messages. Check the terminal for logs – they will show received messages, API calls, and any errors. Use /myprofile to verify that user data is being persisted.

🚢 Deployment
For 24/7 operation, deploy the bot to a cloud platform like Railway, Heroku, or a VPS.

Railway (recommended)
Push your code to a GitHub repository.

Create a new project on Railway and link your repo.

Add all environment variables from your .env in Railway's dashboard.

Deploy – Railway will automatically install dependencies and run python bot.py.

VPS (DigitalOcean, etc.)
Transfer your project to the server.

Install Python and dependencies.

Use screen or systemd to keep the bot running.

🤝 Contributing
Contributions are welcome! Feel free to open issues or submit pull requests for new features, bug fixes, or documentation improvements.

📄 License
This project is licensed under the MIT License – see the LICENSE file for details.

🙏 Acknowledgements
Groq for the incredibly fast inference API.

CoinMarketCap for market data.

python-telegram-bot for the excellent library.

All open‑source contributors whose libraries made this project possible.

📬 Contact
For questions or suggestions, please open an issue on GitHub or reach out via Telegram @jasperkhant.

Enjoy your Burmese crypto assistant! 🇲🇲📈
