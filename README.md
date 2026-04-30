# 🚀 AI Crypto Chatbot: Voice-Enabled Paper Trading Assistant

A production-grade, voice-first AI cryptocurrency assistant. This project combines real-time market data, blockchain analytics, and a professional-grade **Paper Trading Engine** into a stunning, futuristic interface.

![Crypto Chatbot Interface](assets/image.png)

## ✨ Key Features

*   **🎙️ Voice-First Interaction**: Full Speech-to-Text (via local Whisper) and Text-to-Speech (offline) support.
*   **📈 Real-time Market Data**: Live prices and 24h changes via CoinMarketCap integration.
*   **🔗 Blockchain Analytics**: On-chain stats (blocks, hashrate, transactions) for BTC, ETH, and more via Blockchair.
*   **💎 Paper Trading Engine**: 
    *   Virtual $100,000 cash balance to practice trading.
    *   Market Buy/Sell, Limit Orders, and Stop-Loss functionality.
    *   Portfolio tracking with Realized/Unrealized P&L.
    *   Risk management (Max position limits, daily loss caps).
*   **📚 RAG Knowledge Base**: AI can query local PDFs/documents for deep project research using ChromaDB.
*   **🛡️ Hardened Security**: Rate limiting, audit logging, and sensitive data sanitization for all AI tool calls.
*   **🌊 Glassmorphism UI**: A responsive, dark-mode React interface with smooth animations and streaming text responses.

---

## 🛠️ Tech Stack

### Backend (Python/FastAPI)
- **AI Orchestration**: Google Agent Development Kit (ADK) + Gemini 2.0 Flash.
- **Tools Engine**: Model Context Protocol (MCP) server for extensible tool integration.
- **Database**: MySQL with SQLAlchemy (Portfolio, Trades, Wallets).
- **Voice**: OpenAI Whisper (STT) + pyttsx3 (TTS) + FFmpeg.
- **Search**: ChromaDB + Sentence Transformers (RAG).

### Frontend (React/Vite)
- **Styling**: Tailwind CSS + Framer Motion.
- **Communication**: WebSockets for real-time, low-latency streaming of voice and text.

---

## ⚙️ Prerequisites

1.  **Node.js** (v18+)
2.  **Python** (v3.10 or v3.11)
3.  **MySQL Server** (Running locally or remotely)
4.  **FFmpeg**: Required for audio processing.
    - *Windows*: `winget install Gyan.FFmpeg`
    - *Mac*: `brew install ffmpeg`

---

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/ai-crypto-chatbot.git
cd ai-crypto-chatbot
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv
# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### Configuration (.env)
Create a `.env` file in the `backend` folder:
```env
GOOGLE_API_KEY=your_gemini_api_key
COINMARKETCAP_API_KEY=your_cmc_key
COINMARKETCAP_URL=https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest
CRYPTOPANIC_API_KEY=your_cryptopanic_key
CRYPTOPANIC_URL=https://cryptopanic.com/api/developer/v2/posts/
BLOCKCHAIR_BASE_URL=https://api.blockchair.com
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/crypto_db
```

#### Voice Binaries (Whisper)
Ensure you have the Whisper binaries in `backend/whisper-cli/`. These are excluded from Git to keep the repo small. You can download the `whisper-cli.exe` and `ggml-base.en.bin` model from the whisper.cpp releases.

#### Initialize Database
```bash
python setup_db_v3.py
python setup_paper_trading.py
```

### 3. Frontend Setup
```bash
cd ../frontend
npm install
```

---

## ▶️ Running the Application

You need two terminals running simultaneously:

**Terminal 1: Backend**
```bash
cd backend
python -m uvicorn main:app --port 8000 --reload
# python main.py
```

**Terminal 2: Frontend**
```bash
cd frontend
npm run dev
```

Visit **http://localhost:5173** to start chatting!

---

## 💡 How It Works

1.  **User Input**: You can type or click the microphone icon to speak.
2.  **Voice Processing**: If you speak, the React frontend streams audio to the FastAPI backend via WebSockets. The backend uses **FFmpeg** to normalize the audio and **Whisper** to transcribe it.
3.  **AI Reasoning**: The transcript is sent to **Google Gemini**. Gemini decides if it needs to use a tool (e.g., "What's the price of BTC?").
4.  **MCP Tools**: The agent calls tools defined in `mcp_server.py`. This server handles the logic for fetching prices, checking the database, or executing trades.
5.  **Streaming Response**: The AI response is streamed back to the frontend chunk-by-chunk for a fast, responsive feel. If enabled, the frontend will also use **Text-to-Speech** to read the answer aloud.

---

## 📄 License
MIT License - See [LICENSE](LICENSE) for details.
