import os
import asyncio
import logging
import json
import re
import subprocess
import tempfile
import traceback
import time
import random
import uvicorn
import uuid
from typing import List, Dict, Optional
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status, Request, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.genai import types
import google.genai as genai

# Import agent and RAG service
from agent import root_agent
try:
    import rag_service
except ImportError:
    from . import rag_service

# Import DB and Auth
from database import get_db, SessionLocal, User, AdminUser, ChatSession, ChatMessage, DefaultQuestion, Document
from auth import get_password_hash, verify_password, create_access_token, get_current_user, get_current_admin, limiter

# Import Gemini error types for smart retry logic
try:
    from google.genai.errors import ServerError as GeminiServerError
except ImportError:
    GeminiServerError = None

# Initialize Professional Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("CryptoBackend")

from database import engine, Base
logger.info("Initializing database tables...")
Base.metadata.create_all(bind=engine)

def sync_rag_documents(db: Session):
    """Scans ./data folder and syncs with MySQL crypto_rag_documents table."""
    data_folder = "./data"
    if not os.path.exists(data_folder):
        os.makedirs(data_folder, exist_ok=True)
        return

    # Valid extensions
    valid_exts = ('.pdf', '.txt', '.md', '.docx')
    files = [f for f in os.listdir(data_folder) if f.lower().endswith(valid_exts)]
    
    # Get existing filenames from DB
    existing_docs = db.query(Document.file_name).all()
    existing_filenames = {d[0] for d in existing_docs}

    synced_count = 0
    for filename in files:
        if filename not in existing_filenames:
            new_doc = Document(
                file_name=filename,
                source="system",
                status="processed"
            )
            db.add(new_doc)
            synced_count += 1
            logger.info(f"Sync: Added {filename} to RAG Knowledge tracking (Source: system)")
    
    if synced_count > 0:
        db.commit()
    return synced_count

load_dotenv()

# Add FFmpeg to PATH (required for webm -> wav conversion)
ffmpeg_path = r"C:\Users\rites\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0.1-full_build\bin"
if os.path.exists(ffmpeg_path):
    os.environ["PATH"] += os.pathsep + ffmpeg_path

# --- Whisper.cpp Configuration ---
WHISPER_DIR = os.path.join(os.path.dirname(__file__), "whisper-cli", "whisper-cublas-12.4.0-bin-x64", "Release")
WHISPER_EXE = os.path.join(WHISPER_DIR, "whisper-cli.exe")
WHISPER_MODEL = os.path.join(WHISPER_DIR, "ggml-base.en.bin")

if os.path.exists(WHISPER_EXE):
    logger.info(f"whisper-cli.exe found: {WHISPER_EXE}")
else:
    logger.warning(f"whisper-cli.exe NOT found at: {WHISPER_EXE}")

app = FastAPI(title="CryptoAI Backend")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://ai-smart-trading-bot-j6ry.vercel.app",
    "https://ai-smart-trading-bot.vercel.app", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Apply Rate Limiter
app.state.limiter = limiter

# Initialize ADK Services
session_service = InMemorySessionService()
artifact_service = InMemoryArtifactService()

# Initialize Runner
runner = Runner(
    agent=root_agent,
    app_name="CryptoBackend",
    session_service=session_service,
    artifact_service=artifact_service
)

@app.get("/")
def health_check():
    """Health check endpoint — reports MCP server and agent status."""
    return {
        "status": "ok",
        "agent": root_agent.name,
        "mcp_transport": "STDIO",
        "whisper": os.path.exists(WHISPER_EXE),
    }

# ==========================================
# REST API - AUTHENTICATION
# ==========================================

class LoginRequest(BaseModel):
    email: str
    password: str
    client_id: Optional[str] = None

class RegisterRequest(BaseModel):
    email: str
    username: str
    password: str
    display_name: str = ""
    client_id: Optional[str] = None

class AdminCreateRequest(BaseModel):
    username: str
    password: str
    display_name: str = ""

@app.post("/api/auth/register")
@limiter.limit("5/minute")
def register(request: Request, data: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = User(
        email=data.email,
        username=data.username,
        password_hash=get_password_hash(data.password),
        display_name=data.display_name or data.username,
        role="user",
        is_guest=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Handle Session Migration
    # Session migration disabled
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer", "user": {"id": user.id, "email": user.email, "username": user.username, "role": "user"}}

@app.post("/api/auth/login")
@limiter.limit("10/minute")
def login(request: Request, data: LoginRequest, db: Session = Depends(get_db)):
    # Check for Admin Credentials from .env as fallback
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASSWORD")
    
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        # Fallback to username
        user = db.query(User).filter(User.username == data.email).first()

    # If it matches the ENV admin credentials, we can manually authenticate
    if not user and data.email == admin_email and data.password == admin_password:
        # Check if admin exists in DB, if not, create a temporary session user
        # Note: In a real app, you'd ensure the admin is in the DB, but for now we fallback.
        access_token = create_access_token(data={"sub": admin_email})
        return {
            "access_token": access_token, 
            "token_type": "bearer", 
            "user": {"id": 999, "email": admin_email, "username": "admin", "role": "admin"}
        }
        
    if not user or not user.password_hash or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    access_token = create_access_token(data={"sub": user.email or user.username})
    return {"access_token": access_token, "token_type": "bearer", "user": {"id": user.id, "email": user.email, "username": user.username, "role": "user"}}

@app.post("/api/auth/guest")
@limiter.limit("20/minute")
def create_guest(request: Request, db: Session = Depends(get_db)):
    guest_username = f"guest_{uuid.uuid4().hex[:12]}"
    user = User(
        username=guest_username,
        display_name="Guest User",
        role="user",
        is_guest=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer", "user": {"id": user.id, "username": user.username, "role": "user"}}

@app.get("/api/auth/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "email": current_user.email, "username": current_user.username, "role": "user", "display_name": current_user.display_name}

@app.get("/api/sessions")
def list_sessions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Retrieves all chat sessions for the logged-in user from the database."""
    sessions = db.query(ChatSession).filter(ChatSession.user_id == current_user.id).order_by(ChatSession.last_message_at.desc()).all()
    
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    return [{
        "id": s.id,
        "preview": s.last_message or "New Conversation",
        "last_message_at": s.last_message_at.replace(tzinfo=timezone.utc).timestamp() * 1000 if s.last_message_at else 0,
        "is_ended": (
            s.last_message_at is not None and 
            (now - s.last_message_at.replace(tzinfo=timezone.utc)).total_seconds() >= 300
        )
    } for s in sessions]

@app.delete("/api/sessions/{session_id}")
def delete_session(session_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    db.delete(session)
    db.commit()
    return {"status": "success", "message": "Session deleted"}

# ==========================================
# REST API - PUBLIC CHAT & QUESTIONS
# ==========================================

@app.get("/api/questions")
def get_active_questions(db: Session = Depends(get_db)):
    questions = db.query(DefaultQuestion).filter(DefaultQuestion.is_active == True).order_by(DefaultQuestion.created_at.desc()).all()
    return [{"id": q.id, "text": q.question_text} for q in questions]


async def transcribe_with_whisper(webm_bytes: bytes) -> str:
    """
    Converts raw .webm bytes to 16kHz WAV using ffmpeg,
    then runs whisper-cli.exe to transcribe.
    Returns the clean transcript text.
    """
    temp_webm = None
    temp_wav = None
    try:
        # 1. Write the raw webm bytes to a temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as f:
            f.write(webm_bytes)
            temp_webm = f.name

        temp_wav = temp_webm.replace(".webm", ".wav")

        # 2. Convert webm → 16kHz mono WAV using ffmpeg (required by whisper.cpp)
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-i", temp_webm,
            "-ar", "16000",    # 16kHz sample rate
            "-ac", "1",        # Mono channel
            "-c:a", "pcm_s16le",  # 16-bit PCM
            temp_wav
        ]
        logger.info("Converting audio: webm → 16kHz WAV via ffmpeg...")
        result = await asyncio.to_thread(
            subprocess.run,
            ffmpeg_cmd,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            logger.error(f"ffmpeg conversion failed: {result.stderr}")
            return ""

        # 3. Run whisper-cli.exe on the wav file
        whisper_cmd = [
            WHISPER_EXE,
            "-m", WHISPER_MODEL,
            "-f", temp_wav,
            "--no-timestamps",   # Clean output without timestamps
            "-l", "en",          # Enforce English
            "--threads", "4",    # Use 4 threads for speed
        ]
        logger.info(f"Running whisper-cli on {os.path.basename(temp_wav)}...")
        whisper_result = await asyncio.to_thread(
            subprocess.run,
            whisper_cmd,
            capture_output=True,
            text=True,
            cwd=WHISPER_DIR  # Run from whisper dir so DLLs are found
        )
        
        if whisper_result.returncode != 0:
            logger.error(f"whisper-cli failed: {whisper_result.stderr}")
            return ""

        # 4. Clean the output: strip timestamps like [00:00:00.000 --> 00:00:02.000]
        raw_output = whisper_result.stdout.strip()
        # Remove any remaining timestamp brackets if --no-timestamps doesn't catch them all
        cleaned = re.sub(r'\[[\d:.,\s>-]+\]', '', raw_output).strip()
        # Remove leading/trailing whitespace from each line and join
        lines = [l.strip() for l in cleaned.splitlines() if l.strip()]
        transcript = " ".join(lines)
        logger.info(f"Whisper.cpp transcript: '{transcript}'")
        return transcript

    except Exception as e:
        logger.error(f"transcribe_with_whisper error: {e}", exc_info=True)
        return ""
    finally:
        # Cleanup temp files
        for f in [temp_webm, temp_wav]:
            if f and os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass



# --- WebSocket Streaming ---

client_cooldowns = {}
session_connection_counts = {} # Tracks how many times a session has connected: {client_id: count}

# --- Predefined Follow-Up Message Pools ---
COLD_START_MESSAGES = [
    "_Hey there! 👋 I can help you with live crypto prices, market news, or paper trading. What sounds good?_",
    "_Welcome! Want me to check Bitcoin's price or show you today's trending coins?_",
    "_I'm your crypto AI assistant! Ask me about any coin, or try our paper trading simulator._",
    "_Need a quick market update? Just name a coin and I'll pull the latest data for you._",
    "_Ready when you are! I can fetch prices, network stats, news, or manage your paper trades._",
    "_Not sure where to start? Try asking 'What is the price of Ethereum?' or 'Show me crypto news'._",
    "_I've got live data from CoinMarketCap, blockchain stats, and a full paper trading engine. What would you like?_",
    "_Curious about any coin? Just type its name and I'll give you a complete breakdown._",
    "_Welcome aboard! Popular questions: BTC price, top gainers, portfolio balance, or latest crypto headlines._",
    "_I'm here to help you navigate the crypto market. Fire away with any question!_",
    "_Want to practice trading risk-free? Ask me to buy or sell any coin with our paper trading system!_",
]

FALLBACK_MESSAGES = [
    "_The crypto market never sleeps! Anything you want to look into?_",
    "_I can pull up live prices or the latest news for you. Where should we start?_",
    "_Want to see which coins are trending in the last 24 hours?_",
    "_I'm ready to analyze any coin you're curious about. Just name it!_",
    "_Need a quick update on your paper trading portfolio?_",
    "_We could look at some network stats for Bitcoin or Doge if you like._",
    "_The charts are moving! Want me to check for any major price changes?_",
    "_I've got the latest crypto headlines ready. Want to hear the top stories?_",
    "_Should we check how the overall market sentiment is looking today?_",
    "_Still here if you need a hand navigating the crypto space!_",
    "_I can help you simulate a trade — want to see how much 1 ETH would cost right now?_",
    "_Your paper portfolio might have changed since we last checked. Want an update?_",
]




async def generate_ai_followup(last_bot_message: str) -> str:
    """Generate a context-aware follow-up using Gemini. Returns empty string on failure."""
    try:
        client = genai.Client()
        prompt = (
            "You are a crypto chatbot assistant. The user went idle after your last message. "
            "Generate a SHORT, friendly, single-sentence follow-up nudge (max 20 words) "
            "that is contextually relevant to your last message. "
            "Do NOT repeat the last message. Do NOT use greetings. "
            "Make it feel natural and helpful. Return ONLY the nudge text, nothing else.\n\n"
            f"Your last message was:\n{last_bot_message[-300:]}"
        )
        response = await asyncio.wait_for(
            asyncio.to_thread(
                lambda: client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt,
                )
            ),
            timeout=5.0  # Hard 5-second timeout
        )
        text = response.text.strip().strip('"').strip("'")
        if text and len(text) < 150:
            return f"_{text}_"
        return ""
    except asyncio.TimeoutError:
        logger.warning("AI follow-up timed out (5s limit)")
        return ""
    except Exception as e:
        logger.warning(f"AI follow-up generation failed: {e}")
        return ""

async def prime_adk_session_from_db(session_id: str, user_id_ai: str):
    """
    Loads last 30 messages from MySQL and injects them into the ADK SessionService
    if the runtime session is currently empty. Ensures AI memory survives restarts.
    """
    session = await session_service.get_session(
        app_name="CryptoBackend", user_id=user_id_ai, session_id=session_id
    )
    
    # If session already has messages in RAM, don't re-prime (prevents duplicates)
    if session and hasattr(session, 'history') and len(session.history) > 0:
        return 
    
    db = SessionLocal()
    try:
        # Fetch last 30 messages to provide deep context without token explosion
        history = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.desc()).limit(30).all()
        history.reverse() # Order chronologically
        
        if not history:
            return
            
        adk_messages = []
        for msg in history:
            # Map DB roles to Gemini/ADK expected roles
            role = "user" if msg.role == "user" else "model"
            content = types.Content(role=role, parts=[types.Part(text=msg.content)])
            adk_messages.append(content)
            
        if not session:
            await session_service.create_session(
                app_name="CryptoBackend", user_id=user_id_ai, session_id=session_id
            )
            session = await session_service.get_session(
                app_name="CryptoBackend", user_id=user_id_ai, session_id=session_id
            )
            
        if session:
            session.history = adk_messages
            logger.info(f"✅ Primed ADK session {session_id} with {len(adk_messages)} messages from DB")
    except Exception as e:
        logger.error(f"❌ Failed to prime session {session_id}: {e}")
    finally:
        db.close()

@app.websocket("/ws/chat/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str, token: Optional[str] = None):
    await websocket.accept()
    
    from database import SessionLocal, User
    
    # Auth Logic
    current_user = None
    if token and token != "null" and token != "undefined":
        try:
            from jose import jwt
            from auth import SECRET_KEY, ALGORITHM
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            sub: str = payload.get("sub")
            if sub:
                db = SessionLocal()
                # Try email then username
                current_user = db.query(User).filter(User.email == sub).first()
                if not current_user:
                    current_user = db.query(User).filter(User.username == sub).first()
                db.close()
        except Exception as e:
            logger.warning(f"WS Auth Failed: {e}")

    # Enforce Authentication: No Guest Fallback
    if not current_user:
        logger.warning(f"Rejecting unauthenticated WS connection from {client_id}")
        await websocket.send_json({"type": "error", "message": "Authentication required. Please login."})
        await websocket.close(code=4003)
        return

    user_id_for_ai = current_user.id
    db_user_id = current_user.id
    
    logger.info(f"Client {client_id} connected (User: {user_id_for_ai})")

    # --- Session Recovery & Priming ---
    # Rehydrate AI memory from DB before processing any new messages
    await prime_adk_session_from_db(client_id, user_id_for_ai)

    # Audio buffer: accumulates raw webm bytes from MediaRecorder chunks
    audio_buffer = bytearray()

    # State for idle follow-ups
    followup_task = None
    cold_start_task = None
    hard_timeout_task = None
    interaction_started = False  # True once user sends first message
    session_ended = False
    last_activity_time = time.time()
    last_typing_time = 0
    is_client_active = True # Default to True, hook will update it immediately

    # --- Cold Start Routine ---
    async def cold_start_routine():
        """If user opens chat but doesn't type for 15s, send exactly ONE nudge if session is empty."""
        try:
            await asyncio.sleep(15)
            # Only send if no interaction, no session end, and 0 nudges sent so far
            if not interaction_started and not session_ended and is_client_active:
                db = SessionLocal()
                session_obj = None
                db_count = 0
                
                # Only check/write DB for logged in users
                if db_user_id:
                    session_obj = db.query(ChatSession).filter(ChatSession.id == client_id).first()
                    db_count = session_obj.nudge_count if session_obj else 0
                else:
                    # For guests, we only use in-memory state
                    # We assume 0 since if they refreshed, they get a new connection anyway
                    db_count = 0
                
                if db_count == 0:
                    msg = random.choice(COLD_START_MESSAGES)
                    await websocket.send_json({"type": "response.text_new", "text": msg})
                    
                    if db_user_id:
                        if not session_obj:
                            session_obj = ChatSession(id=client_id, user_id=db_user_id)
                            db.add(session_obj)
                        
                        session_obj.nudge_count = 1
                        db.add(ChatMessage(session_id=client_id, role="assistant", content=msg))
                        session_obj.last_message = msg
                        session_obj.last_message_at = datetime.now(timezone.utc)
                        db.commit()
                    
                    logger.info(f"Persistent Cold Start nudge sent to {client_id}")
                db.close()
        except asyncio.CancelledError:
            pass

    # --- Post-Interaction Follow-Up Routine (2 nudges max, persists across refreshes) ---
    async def follow_up_routine(initial_text: str):
        """Sends max 2 nudges after interaction. Checks global count to prevent refresh-spam."""
        nonlocal session_ended
        try:
            # We track guest nudge count in memory
            guest_nudge_count = 0
            
            for _ in range(2):
                await asyncio.sleep(90)
                if session_ended: return
                
                db = SessionLocal()
                session_obj = None
                count = 0
                
                if db_user_id:
                    session_obj = db.query(ChatSession).filter(ChatSession.id == client_id).first()
                    count = session_obj.nudge_count if session_obj else 0
                else:
                    count = guest_nudge_count

                # --- Dynamic Idle Check ---
                # Only send if:
                # 1. Chat is actively open (is_client_active)
                # 2. User is not currently typing (last 10s)
                # 3. User has been idle for at least 80s since last activity
                current_time = time.time()
                is_idle = (current_time - last_activity_time) >= 80
                is_typing_now = (current_time - last_typing_time) < 10

                if not is_client_active or is_typing_now or not is_idle:
                    logger.info(f"Nudge skipped for {client_id}: active={is_client_active}, typing={is_typing_now}, idle={is_idle}")
                    # Re-queue the loop if we want to try again, but let's just skip this slot
                    continue

                if count >= 2: 
                    db.close()
                    logger.info(f"Nudge limit (2) reached for {client_id}. Stopping.")
                    return

                if count == 0:
                    # First nudge: AI contextual
                    msg = await generate_ai_followup(initial_text) or random.choice(FALLBACK_MESSAGES)
                else:
                    # Second nudge: Predefined
                    msg = random.choice(FALLBACK_MESSAGES)

                await websocket.send_json({"type": "response.text_new", "text": msg})
                
                if db_user_id:
                    if not session_obj:
                        session_obj = ChatSession(id=client_id, user_id=db_user_id)
                        db.add(session_obj)
                    session_obj.nudge_count = count + 1
                    db.add(ChatMessage(session_id=client_id, role="assistant", content=msg))
                    session_obj.last_message = msg
                    session_obj.last_message_at = datetime.now(timezone.utc)
                    db.commit()
                else:
                    guest_nudge_count += 1
                    
                db.close()
                logger.info(f"Follow-up nudge sent to {client_id}")
        except asyncio.CancelledError:
            pass

    # --- Hard Timeout (5 minutes of inactivity → close session silently) ---
    async def hard_timeout_routine():
        nonlocal session_ended
        try:
            while True:
                await asyncio.sleep(10)
                if session_ended: return
                elapsed = time.time() - last_activity_time
                if elapsed >= 300:  # 5 minutes
                    logger.info(f"Hard timeout reached for {client_id} ({elapsed:.0f}s idle)")
                    session_ended = True
                    try:
                        await websocket.send_json({"type": "session.end"})
                    except Exception:
                        pass
                    cleanup_all()
                    try:
                        await websocket.close()
                    except Exception:
                        pass
                    return
        except asyncio.CancelledError:
            pass
        except Exception:
            pass

    def cancel_followup():
        nonlocal followup_task
        if followup_task and not followup_task.done():
            followup_task.cancel()
        followup_task = None

    def cancel_cold_start():
        nonlocal cold_start_task
        if cold_start_task and not cold_start_task.done():
            cold_start_task.cancel()
        cold_start_task = None

    def cleanup_all():
        cancel_followup()
        cancel_cold_start()
        nonlocal hard_timeout_task
        if hard_timeout_task and not hard_timeout_task.done():
            hard_timeout_task.cancel()
        hard_timeout_task = None
        client_cooldowns.pop(client_id, None)
        # Note: We do NOT pop session_connection_counts, so it persists if the server stays up

    # Start cold start timer and hard timeout monitor
    # --- Initial State Sync ---
    # Check if session has ANY history to determine if we should resume nudges
    db = SessionLocal()
    session_obj = db.query(ChatSession).filter(ChatSession.id == client_id).first()
    
    # --- Check for 5-minute Timeout (Persistent) ---
    if session_obj and session_obj.last_message_at:
        elapsed = (datetime.now(timezone.utc) - session_obj.last_message_at.replace(tzinfo=timezone.utc)).total_seconds()
        if elapsed >= 300:
            logger.info(f"Session {client_id} resumed but is already timed out ({elapsed:.0f}s). Locking.")
            session_ended = True
            await websocket.send_json({"type": "session.end"})

    db_nudge_count = session_obj.nudge_count if session_obj else 0
    
    # --- Fetch DB History ---
    # Send existing messages to the frontend immediately on connect
    history = db.query(ChatMessage).filter(ChatMessage.session_id == client_id).order_by(ChatMessage.created_at.asc()).all()
    if history:
        await websocket.send_json({
            "type": "history",
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "created_at": msg.created_at.replace(tzinfo=timezone.utc).isoformat() if msg.created_at else None
                } for msg in history
            ]
        })
        logger.info(f"Sent {len(history)} messages of history to {client_id}")
    
    db.close()

    existing_session = await session_service.get_session(app_name="CryptoBackend", user_id=user_id_for_ai, session_id=client_id)
    history_found = (existing_session and hasattr(existing_session, 'history') and len(existing_session.history) > 0)

    if history_found:
        interaction_started = True
        logger.info(f"Resuming active session {client_id} (History found). Checking for pending nudges...")
        
        # Look for the last bot message to provide context for potential follow-up resume
        last_bot_msg = ""
        for m in reversed(existing_session.history):
            if m.role == "model":
                for p in m.parts:
                    if hasattr(p, 'text') and p.text:
                        last_bot_msg = p.text
                        break
                if last_bot_msg: break
        
        # If the last message was from the bot and we haven't reached the nudge limit, resume the routine
        if last_bot_msg and db_nudge_count < 2:
            followup_task = asyncio.create_task(follow_up_routine(last_bot_msg))
            logger.info(f"Resumed follow-up routine for {client_id} (DB Count: {db_nudge_count})")
    else:
        # No history found. Start cold-start if no nudge has been sent yet
        if db_nudge_count == 0:
            cold_start_task = asyncio.create_task(cold_start_routine())
            logger.info(f"Started one-shot cold-start timer for {client_id}")
        else:
            interaction_started = True
            logger.info(f"Cold-start already sent for {client_id}, waiting for user.")
    
    hard_timeout_task = asyncio.create_task(hard_timeout_routine())

    try:
        while True:
            message = await websocket.receive()

            # Update activity timestamp on any message
            last_activity_time = time.time()

            if "bytes" in message and message["bytes"]:
                cancel_followup()
                cancel_cold_start()
                interaction_started = True
                # Accumulate audio chunk from MediaRecorder
                audio_buffer.extend(message["bytes"])
                logger.info(f"Audio chunk received: {len(message['bytes'])} bytes (buffer total: {len(audio_buffer)} bytes)")

            elif "text" in message and message["text"]:
                data = json.loads(message["text"])
                msg_type = data.get("type")

                if msg_type == "transcribe_request":
                    # Frontend stopped recording — process the buffer
                    if len(audio_buffer) < 1000:
                        logger.warning("Audio buffer too small — skipping transcription.")
                        await websocket.send_json({"type": "transcript", "text": "", "is_dictation": True})
                        audio_buffer = bytearray()
                        continue

                    logger.info(f"Transcribing {len(audio_buffer)} bytes with whisper.cpp...")
                    transcript = await transcribe_with_whisper(bytes(audio_buffer))
                    audio_buffer = bytearray()  # Reset buffer

                    await websocket.send_json({
                        "type": "transcript",
                        "text": transcript,
                        "is_dictation": True
                    })

                elif msg_type == "user_typing":
                    cancel_followup()
                    cancel_cold_start()
                    interaction_started = True
                    continue

                elif msg_type == "text_input":
                    cancel_followup()
                    cancel_cold_start()
                    interaction_started = True
                    user_text = data.get("text", "").strip()
                    if not user_text:
                        continue

                    # Echo user text back
                    await websocket.send_json({"type": "transcript", "text": user_text})

                    # Agent Processing
                    response_text = ""
                    
                    # Ensure session exists in DB
                    if db_user_id:
                        db = SessionLocal()
                        db_session = db.query(ChatSession).filter(ChatSession.id == client_id).first()
                        if not db_session:
                            db_session = ChatSession(id=client_id, user_id=db_user_id, title=user_text[:50])
                            db.add(db_session)
                        
                        # Save user message to DB
                        user_msg = ChatMessage(session_id=client_id, role="user", content=user_text)
                        db.add(user_msg)
                        db_session.last_message = user_text
                        db_session.last_message_at = datetime.now(timezone.utc)
                        db_session.user_id = db_user_id # Ensure it's updated if they just logged in
                        db.commit()
                        db.close()

                    session = await session_service.get_session(
                        app_name="CryptoBackend", user_id=user_id_for_ai, session_id=client_id
                    )
                    if not session:
                        await session_service.create_session(
                            app_name="CryptoBackend", user_id=user_id_for_ai, session_id=client_id
                        )

                    # --- Agent Execution with Smart Retry Logic ---
                    max_retries = 3
                    
                    async def safe_send(data):
                        try:
                            await websocket.send_json(data)
                        except Exception:
                            pass

                    try:
                        for attempt in range(1, max_retries + 1):
                            try:
                                logger.info(f"Running agent for {client_id} (attempt {attempt})...")
                                # Inject structured [SYSTEM CONTEXT] for deterministic identity in tool calls
                                # This is internal-only and won't be visible to the user in the UI
                                context_prefix = f"[SYSTEM CONTEXT: user_id={db_user_id}, session_id={client_id}]\n"
                                
                                async for event in runner.run_async(
                                    user_id=user_id_for_ai,
                                    session_id=client_id,
                                    new_message=types.Content(role="user", parts=[types.Part(text=f"{context_prefix}{user_text}")])
                                ):
                                    chunk_text = ""
                                    if hasattr(event, 'text') and event.text:
                                        chunk_text = event.text
                                    elif hasattr(event, 'content') and event.content:
                                        if hasattr(event.content, 'parts'):
                                            for part in event.content.parts:
                                                if hasattr(part, 'text') and part.text:
                                                    chunk_text += part.text
                                        elif hasattr(event.content, 'text') and event.content.text:
                                            chunk_text = event.content.text

                                    if chunk_text:
                                        response_text += chunk_text
                                        await safe_send({"type": "response.text_partial", "text": chunk_text})

                                logger.info(f"Agent reply complete: {len(response_text)} chars.")
                                if not response_text.strip():
                                    response_text = "I'm sorry, I couldn't process that. Please try again."
                                    await safe_send({"type": "response.text_partial", "text": response_text})
                                await safe_send({"type": "response.text", "text": response_text})
                                await safe_send({"type": "response.complete"})
                                
                                # Save Bot response to DB
                                if db_user_id:
                                    db = SessionLocal()
                                    bot_msg = ChatMessage(session_id=client_id, role="bot", content=response_text)
                                    db.add(bot_msg)
                                    db_session = db.query(ChatSession).filter(ChatSession.id == client_id).first()
                                    if db_session:
                                        db_session.last_message = response_text
                                        db_session.last_message_at = datetime.now(timezone.utc)
                                    db.commit()
                                    db.close()

                                # Start follow-up timer for the 2-nudge sequence
                                if not session_ended:
                                    cancel_followup()
                                    followup_task = asyncio.create_task(follow_up_routine(response_text))

                                break  # Success — exit retry loop

                            except (ConnectionError, BrokenPipeError, OSError) as e:
                                logger.warning(f"⚠️ MCP connection lost (attempt {attempt}/{max_retries}): {e}")
                                if attempt < max_retries:
                                    logger.info("🔄 Retrying in 2 seconds...")
                                    await asyncio.sleep(2)
                                    response_text = ""
                                else:
                                    logger.error(f"❌ MCP server unreachable after {max_retries} attempts.")
                                    await safe_send({
                                        "type": "error",
                                        "message": "Our analysis engine is temporarily unavailable. Please try again in a moment."
                                    })
                                    await safe_send({"type": "response.complete"})

                            except Exception as e:
                                err_msg = str(e)
                                is_429 = "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg
                                is_401 = "401" in err_msg or "UNAUTHORIZED" in err_msg
                                is_503 = (GeminiServerError and isinstance(e, GeminiServerError) and "503" in err_msg) or "503" in err_msg

                                if is_429:
                                    logger.error(f"❌ Gemini Quota Exceeded (429): {err_msg}")
                                    await safe_send({"type": "error", "message": "I've hit my daily limit for analysis. Please try again tomorrow or upgrade your Gemini API key plan."})
                                    await safe_send({"type": "response.complete"})
                                    break
                                elif is_401:
                                    logger.error(f"❌ Gemini API Key Error (401): {err_msg}")
                                    await safe_send({"type": "error", "message": "My API key seems to be invalid. Please check the .env file and ensure your Google AI Studio key is correct."})
                                    await safe_send({"type": "response.complete"})
                                    break
                                elif is_503 and attempt < max_retries:
                                    wait_time = attempt * 5
                                    logger.warning(f"⚠️ Gemini 503 overloaded (attempt {attempt}/{max_retries}). Retrying in {wait_time}s...")
                                    await safe_send({"type": "response.text_partial", "text": f"_The AI model is busy. Retrying in {wait_time} seconds..._"})
                                    await asyncio.sleep(wait_time)
                                    response_text = ""
                                elif is_503:
                                    logger.error(f"❌ Gemini still overloaded after {max_retries} attempts.")
                                    await websocket.send_json({"type": "error", "message": "The AI model is currently under heavy load. Please try again in 30 seconds."})
                                    break
                                else:
                                    logger.error(f"Unhandled Agent error: {err_msg}", exc_info=True)
                                    await websocket.send_json({"type": "error", "message": "An unexpected error occurred. Please refresh and try again."})
                                    await safe_send({"type": "response.complete"})
                                    break
                    except WebSocketDisconnect:
                        logger.info(f"Client {client_id} disconnected during agent execution.")
                        break
                    except Exception as e:
                        if "disconnect" in str(e).lower() or "close" in str(e).lower():
                            logger.info(f"Client {client_id} connection closed during processing.")
                        else:
                            logger.error(f"Unexpected error during agent flow: {e}")
                        break

                elif msg_type == "stop":
                    logger.info(f"Stop signal from {client_id}")
                    audio_buffer = bytearray()

    except WebSocketDisconnect:
        cleanup_all()
        logger.info(f"Client {client_id} disconnected normally.")
    except RuntimeError as e:
        cleanup_all()
        if "disconnect" in str(e).lower():
            logger.info(f"Client {client_id} disconnected abruptly.")
        else:
            logger.error(f"RuntimeError for {client_id}: {e}", exc_info=True)
    except Exception as e:
        cleanup_all()
        logger.error(f"Unexpected error for {client_id}: {e}", exc_info=True)


# ==========================================
# REST API - ADMIN MONITORING
# ==========================================

@app.post("/api/admin/login")
def admin_login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Check Master Admin from .env
    master_username = os.getenv("ADMIN_USERNAME")
    master_password = os.getenv("ADMIN_PASSWORD")
    
    if form_data.username == master_username and form_data.password == master_password:
        access_token = create_access_token(data={"sub": master_username, "is_admin": True})
        return {"access_token": access_token, "token_type": "bearer"}

    # Check DB Admin
    admin = db.query(AdminUser).filter(AdminUser.username == form_data.username).first()
    if not admin or not verify_password(form_data.password, admin.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect admin username or password")
    
    access_token = create_access_token(data={"sub": admin.username, "is_admin": True})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/admin/create")
def create_admin(data: AdminCreateRequest, db: Session = Depends(get_db), current_admin: AdminUser = Depends(get_current_admin)):
    # Check if username exists
    if db.query(AdminUser).filter(AdminUser.username == data.username).first():
        raise HTTPException(status_code=400, detail="Admin username already exists")
    
    new_admin = AdminUser(
        username=data.username,
        password_hash=get_password_hash(data.password),
        display_name=data.display_name or data.username
    )
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    
    return {"message": "Admin created successfully", "username": new_admin.username}

@app.get("/api/admin/stats")
def get_admin_stats(db: Session = Depends(get_db), current_admin: AdminUser = Depends(get_current_admin)):
    total_users = db.query(User).filter(User.is_guest == False).count()
    total_sessions = db.query(ChatSession).filter(ChatSession.user_id.isnot(None)).count()
    total_messages = db.query(ChatMessage).join(ChatSession).filter(ChatSession.user_id.isnot(None)).count()
    total_documents = db.query(Document).count()
    return {
        "total_users": total_users,
        "total_sessions": total_sessions,
        "total_messages": total_messages,
        "total_documents": total_documents 
    }

@app.get("/api/admin/users")
def get_all_users(db: Session = Depends(get_db), current_admin: AdminUser = Depends(get_current_admin)):
    users = db.query(User).order_by(User.created_at.desc()).all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "username": u.username,
            "display_name": u.display_name,
            "role": "user",
            "is_guest": u.is_guest
        } for u in users
    ]

@app.get("/api/admin/sessions")
def get_all_sessions(db: Session = Depends(get_db), current_admin: AdminUser = Depends(get_current_admin)):
    # Simple list of all sessions with user info
    sessions = db.query(ChatSession).filter(ChatSession.user_id.isnot(None)).order_by(ChatSession.updated_at.desc()).all()
    return [
        {
            "id": s.id,
            "title": s.title,
            "user": {
                "id": s.user.id if s.user else "Unknown",
                "email": s.user.email if s.user else "Unknown",
                "username": s.user.username if s.user else "Guest",
                "is_guest": s.user.is_guest if s.user else True
            },
            "last_message": s.last_message,
            "updated_at": s.updated_at.replace(tzinfo=timezone.utc).isoformat() if s.updated_at else None
        } for s in sessions
    ]

@app.get("/api/admin/sessions/{session_id}/messages")
def get_session_messages(session_id: str, db: Session = Depends(get_db), current_admin: AdminUser = Depends(get_current_admin)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id.isnot(None)).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or is a guest session")
        
    messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc()).all()
    return [
        {
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at.replace(tzinfo=timezone.utc).isoformat() if m.created_at else None
        } for m in messages
    ]

# Admin Documents
@app.post("/api/admin/documents")
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db), current_admin: AdminUser = Depends(get_current_admin)):
    import shutil
    import os
    
    try:
        os.makedirs("./data", exist_ok=True)
        file_path = f"./data/{file.filename}"
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        logger.info(f"Admin: Uploading document {file.filename}...")
        
        # Trigger single-file RAG processing (Optimized)
        rag_service.ingest_file(file_path)
        
        # Save metadata to DB
        doc = Document(
            file_name=file.filename,
            source="upload",
            status="processed"
        )
        db.add(doc)
        db.commit()
        logger.info(f"Admin: Document {file.filename} indexed and tracked successfully.")
        return {"message": "Document uploaded and processed successfully"}
    except Exception as e:
        logger.error(f"Upload failed: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/api/admin/documents")
def get_admin_documents(db: Session = Depends(get_db), current_admin: AdminUser = Depends(get_current_admin)):
    # Sync filesystem with DB first
    sync_rag_documents(db)
    
    docs = db.query(Document).order_by(Document.created_at.desc()).all()
    return [
        {
            "id": d.id,
            "file_name": d.file_name,
            "source": d.source,
            "status": d.status,
            "created_at": d.created_at.replace(tzinfo=timezone.utc).isoformat() if d.created_at else None
        } for d in docs
    ]

@app.delete("/api/admin/documents/{doc_id}")
def delete_admin_document(doc_id: int, db: Session = Depends(get_db), current_admin: AdminUser = Depends(get_current_admin)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # 1. Delete from ChromaDB
    rag_service.delete_document(doc.file_name)
    
    # 2. Delete from Filesystem
    file_path = f"./data/{doc.file_name}"
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
    
    # 3. Delete from DB
    db.delete(doc)
    db.commit()
    
    return {"message": "Document deleted successfully"}

# Admin Questions Management
class QuestionCreate(BaseModel):
    question_text: str
    display_order: int = 0
    is_active: bool = True

@app.post("/api/admin/questions")
def create_question(q: QuestionCreate, db: Session = Depends(get_db), current_admin: AdminUser = Depends(get_current_admin)):
    new_q = DefaultQuestion(
        question_text=q.question_text,
        display_order=q.display_order,
        is_active=q.is_active
    )
    db.add(new_q)
    db.commit()
    db.refresh(new_q)
    return new_q

@app.put("/api/admin/questions/{q_id}")
def update_question(q_id: str, q: QuestionCreate, db: Session = Depends(get_db), current_admin: AdminUser = Depends(get_current_admin)):
    db_q = db.query(DefaultQuestion).filter(DefaultQuestion.id == q_id).first()
    if not db_q:
        raise HTTPException(status_code=404, detail="Question not found")
    
    db_q.question_text = q.question_text
    db_q.display_order = q.display_order
    db_q.is_active = q.is_active
    db.commit()
    return db_q

@app.delete("/api/admin/questions/{q_id}")
def delete_question(q_id: str, db: Session = Depends(get_db), current_admin: AdminUser = Depends(get_current_admin)):
    db_q = db.query(DefaultQuestion).filter(DefaultQuestion.id == q_id).first()
    if not db_q:
        raise HTTPException(status_code=404, detail="Question not found")
    
    db.delete(db_q)
    db.commit()
    return {"message": "Question deleted"}

@app.get("/api/admin/me")
def get_admin_me(current_admin: AdminUser = Depends(get_current_admin)):
    return {
        "id": current_admin.id,
        "username": current_admin.username,
        "display_name": current_admin.display_name,
        "role": "admin"
    }

# --- Public / Chatbot UI Endpoints ---
# (Using /api/questions for active default questions)

if __name__ == "__main__":
    from database import engine, Base
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

