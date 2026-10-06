# 🤖 AI Sales Agent

A multi-channel AI-powered Sales Qualification Agent built in Python. It qualifies inbound leads via natural conversation, scores them, saves them to a database, and sends a follow-up email — all automatically.

Currently supports:
- **Telegram Bot** (Live 24/7 via Railway)
- **Twilio Voice Call** (Phone)
- **Local Terminal Chat**

## 🚀 Deployment (Railway)

The easiest way to keep the Telegram bot running 24/7 is to deploy it to [Railway](https://railway.app/). The project is pre-configured for it!

### 1. Connect to Railway
1. Go to [railway.app](https://railway.app/) and sign in with GitHub.
2. Click **New Project** → **Deploy from GitHub repo**.
3. Select this repository.

### 2. Configure Environment Variables
Go to your project's **Variables** tab on Railway and add the following keys (get these from your local `.env` file):

```
GROQ_API_KEY=your_groq_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
GMAIL_ADDRESS=your_gmail_address
GMAIL_APP_PASSWORD=your_gmail_app_password
DB_PATH=/data/sales.db
```

### 3. Add Persistent Storage (Crucial!)
By default, Railway wipes files on every restart. We need a persistent Volume so our `sales.db` (leads) and `chroma_db` (RAG vector store) aren't deleted.

1. Go to the **Volumes** tab in your Railway project.
2. Create a new Volume.
3. Mount the volume at `/data` (this matches the `DB_PATH` we set above).

### 4. Wait for Build
Railway will read the `Procfile`, run `startup.py`, automatically build the database and ChromaDB vector store, and then start the Telegram bot.

---

## 💻 Local Development

### 1. Setup
```bash
python -m venv venv
source venv/Scripts/activate  # Or venv\Scripts\activate on Windows
pip install -r requirement.txt
```

### 2. Environment Variables
Copy `.env.example` to `.env` and fill in your keys.

### 3. Initialize Database & RAG
```bash
python database.py
python rag.py
```

### 4. Run
- **Terminal Chat:** `python main.py`
- **Telegram Bot:** `python telegram_bot.py`
- **Voice Agent:** `python voice_agent.py` (requires ngrok on port 5000)
