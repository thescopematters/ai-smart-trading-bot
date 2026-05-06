# 🚀 AI Crypto Chatbot: Voice-Enabled Paper Trading Assistant

A production-grade, voice-first AI cryptocurrency assistant with a dedicated **Admin Control Panel**. This project combines real-time market data, blockchain analytics, and a professional-grade **Paper Trading Engine** into a stunning, futuristic interface.

![Crypto Chatbot Interface](assets/image.png)

## ✨ Key Features

*   **🎙️ Voice-First Interaction**: Full Speech-to-Text (via local Whisper) and Text-to-Speech (offline) support.
*   **📈 Real-time Market Data**: Live prices and 24h changes via CoinMarketCap integration.
*   **🔗 Blockchain Analytics**: On-chain stats (blocks, hashrate, transactions) for BTC, ETH, and more via Blockchair.
*   **💎 Paper Trading Engine**: Virtual $100,000 cash balance, Market/Limit orders, and Portfolio tracking.
*   **🛡️ Multi-Tier Architecture**: Separate Admin and User interfaces with dedicated authentication.
*   **🌊 Glassmorphism UI**: A responsive, dark-mode React interface with smooth animations.

---

## 🏗️ System Architecture

The system is split into three main components:

1.  **Shared Backend (FastAPI)**: A single API layer serving both interfaces, handling AI logic, RAG, and Paper Trading.
2.  **Chatbot UI (React)**: The end-user interface for chat, sessions, and trading. (Port 3000)
3.  **Admin Panel UI (React)**: A secure control dashboard for managing users, monitoring chats, and RAG knowledge. (Port 3001)

---

## 🛠️ Tech Stack

### Backend (Python/FastAPI)
- **AI Orchestration**: Google ADK + Gemini 2.0 Flash.
- **Database**: MySQL (SQLAlchemy) + ChromaDB (Vector Store).
- **Security**: Dual OAuth2 flows (Admin vs User), JWT, and Rate Limiting.

### Frontend (React/Vite)
- **Styling**: Vanilla CSS + Tailwind + Framer Motion.
- **Communication**: WebSockets for real-time streaming.

---

## 🚀 Installation & Setup

### 1. Clone & Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate # or .\venv\Scripts\activate on Windows
pip install -r requirements.txt
```

#### Configuration (.env)
Create a `.env` file in `backend/`:
```env
# Admin Master Credentials
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_secure_password

# API Keys
GOOGLE_API_KEY=your_gemini_api_key
COINMARKETCAP_API_KEY=your_cmc_key
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/crypto_db
```

### 2. Frontend Setup (Both UIs)
```bash
# Setup Chatbot UI
cd chatbot-ui
npm install

# Setup Admin UI
cd ../admin-ui
npm install
```

---

## ▶️ Running the Application

You need three terminals:

**Terminal 1: Backend**
```bash
cd backend
python -m uvicorn main:app --port 8000 --reload
```

**Terminal 2: Chatbot UI (User-facing)**
```bash
cd chatbot-ui
npm run dev # Runs on http://localhost:3000
```

**Terminal 3: Admin UI (Control Dashboard)**
```bash
cd admin-ui
npm run dev # Runs on http://localhost:3001
```

---

## 🛡️ Admin Capabilities
- **Dashboard**: Real-time stats on users, messages, and RAG documents.
- **User Management**: Monitor all registered accounts and guest sessions.
- **Chat Monitoring**: Audit full conversation histories across the system.
- **RAG Control**: Upload PDFs/Docs, trigger vector indexing, and manage knowledge.
- **Default Questions**: Configure the quick-start questions shown to users.

---

## 📄 License
MIT License - See [LICENSE](LICENSE) for details.
