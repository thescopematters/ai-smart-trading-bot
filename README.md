# 🚀 AI Crypto Chatbot: Voice-Enabled Paper Trading Assistant

A production-grade, voice-first AI cryptocurrency assistant with a dedicated **Admin Control Panel**. This project combines real-time market data, blockchain analytics, and a professional-grade **Paper Trading Engine** into a stunning, futuristic interface.

![Crypto Chatbot Interface](assets/image.png)

## ✨ Key Features

*   **🎙️ Voice-First Interaction**: Full Speech-to-Text (via local Whisper) and Text-to-Speech support for a hands-free experience.
*   **📈 Real-time Market Data**: Live prices, 24h changes, and market trends via CoinMarketCap integration.
*   **🔗 Blockchain Analytics**: Deep on-chain stats (blocks, hashrate, transactions) for BTC, ETH, and more via Blockchair.
*   **💎 Paper Trading Simulator**: Virtual $100,000 cash balance with Market/Limit order support and portfolio tracking.
*   **📚 RAG Knowledge Base**: Advanced Retrieval-Augmented Generation (RAG) allowing the bot to learn from uploaded PDFs, TXT, and Markdown files.
*   **🛡️ Multi-Tier Architecture**: Separate Admin and User interfaces with dedicated authentication and security.
*   **🎨 Premium UI/UX**: 
    *   **Chatbot**: Futuristic Glassmorphism dark-mode interface.
    *   **Admin Panel**: Modern, clean Light-Theme SaaS dashboard for professional management.

---

## 🏗️ System Architecture

The ecosystem consists of three decoupled components:

1.  **Shared Backend (FastAPI)**:
    *   **AI Engine**: Powered by Google Gemini 2.0 Flash for intelligent, context-aware responses.
    *   **Vector Store**: ChromaDB for high-speed document retrieval and RAG.
    *   **Database**: MySQL for persistent storage of users, sessions, trades, and configurations.
    *   **Communication**: Real-time streaming via WebSockets.

2.  **Chatbot UI (React)**:
    *   The primary user-facing interface.
    *   Supports voice interaction, real-time trading, and personalized session history.
    *   Built with Tailwind CSS and Framer Motion for smooth animations.

3.  **Admin Panel UI (React)**:
    *   A professional, high-contrast light-themed dashboard.
    *   **User Management**: Monitor and manage all registered accounts and guest sessions.
    *   **Chat Monitoring**: Real-time auditing of full conversation histories.
    *   **Knowledge Management**: Centralized RAG control for uploading and indexing documents.
    *   **System Oversight**: Live monitoring of API latencies and system performance.

---

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.10+)
- **LLM**: Google Gemini 2.0 Flash
- **Persistence**: SQLAlchemy (MySQL) + ChromaDB (Vector)
- **Voice**: Local Whisper (STT) + Offline TTS

### Frontend
- **Library**: React 18+ (Vite)
- **Styling**: Tailwind CSS (Custom Design System)
- **Icons**: Lucide React
- **Animations**: Framer Motion

---

## 🚀 Installation & Setup

### 1. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

#### Configuration (.env)
Create a `.env` file in `backend/`:
```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_secure_password
GOOGLE_API_KEY=your_gemini_api_key
COINMARKETCAP_API_KEY=your_cmc_key
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/crypto_db
```

### 2. Frontend Setup
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

**Terminal 1: Backend**
```bash
cd backend
python -m uvicorn main:app --port 8000 --reload
```

**Terminal 2: Chatbot UI**
```bash
cd chatbot-ui
npm run dev
```

**Terminal 3: Admin UI**
```bash
cd admin-ui
npm run dev
```

---

## 🛡️ Admin Capabilities
- **Overview**: Real-time stats and infrastructure health monitoring.
- **Users**: Search, filter, and audit user accounts.
- **Documents**: Upload and index knowledge for the AI agent.
- **Chats**: Full transparency into user-agent interactions.
- **Questions**: Manage default quick-start suggestions.

---

## 📄 License
MIT License - See [LICENSE](LICENSE) for details.
