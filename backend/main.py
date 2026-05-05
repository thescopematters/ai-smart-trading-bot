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
from dotenv import load_dotenv

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
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
    allow_origins=["http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
session_nudge_counts = {}  # Tracks nudges sent per session: {client_id: count}
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


@app.websocket("/ws/chat/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    logger.info(f"Client {client_id} connected")

    # Audio buffer: accumulates raw webm bytes from MediaRecorder chunks
    audio_buffer = bytearray()

    # State for idle follow-ups
    followup_task = None
    cold_start_task = None
    hard_timeout_task = None
    interaction_started = False  # True once user sends first message
    session_ended = False
    last_activity_time = time.time()

    # --- Cold Start Routine ---
    async def cold_start_routine():
        """If user opens chat but doesn't type for 45s, send exactly ONE nudge if session is empty."""
        try:
            await asyncio.sleep(45)
            # Only send if no interaction, no session end, and 0 nudges sent so far
            if not interaction_started and not session_ended:
                if session_nudge_counts.get(client_id, 0) == 0:
                    msg = random.choice(COLD_START_MESSAGES)
                    await websocket.send_json({"type": "response.text_new", "text": msg})
                    session_nudge_counts[client_id] = 1
                    logger.info(f"Persistent Cold Start nudge sent to {client_id}")
        except asyncio.CancelledError:
            pass

    # --- Post-Interaction Follow-Up Routine (2 nudges max, persists across refreshes) ---
    async def follow_up_routine(initial_text: str):
        """Sends max 2 nudges after interaction. Checks global count to prevent refresh-spam."""
        nonlocal session_ended
        try:
            for _ in range(2):
                await asyncio.sleep(90)
                if session_ended: return
                
                count = session_nudge_counts.get(client_id, 0)
                if count >= 2: 
                    logger.info(f"Nudge limit (2) reached for {client_id}. Stopping.")
                    return

                if count == 0:
                    # First nudge: AI contextual
                    msg = await generate_ai_followup(initial_text) or random.choice(FALLBACK_MESSAGES)
                else:
                    # Second nudge: Predefined
                    msg = random.choice(FALLBACK_MESSAGES)

                await websocket.send_json({"type": "response.text_new", "text": msg})
                session_nudge_counts[client_id] = count + 1
                logger.info(f"Follow-up nudge {count + 1} sent to {client_id}")

        except asyncio.CancelledError:
            pass

    # --- Hard Timeout (10 minutes of inactivity → close session silently) ---
    async def hard_timeout_routine():
        nonlocal session_ended
        try:
            while True:
                await asyncio.sleep(10)
                if session_ended: return
                elapsed = time.time() - last_activity_time
                if elapsed >= 600:  # 10 minutes
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
        # Note: We do NOT pop session_nudge_counts or session_connection_counts, so they persist if the server stays up

    # Start cold start timer and hard timeout monitor
    # --- Initial State Sync ---
    # Track connections for this specific session
    conn_count = session_connection_counts.get(client_id, 0) + 1
    session_connection_counts[client_id] = conn_count

    # Check if session has ANY history to determine if we should resume nudges
    existing_session = await session_service.get_session(app_name="CryptoBackend", user_id="user", session_id=client_id)
    history_found = existing_session and hasattr(existing_session, 'messages') and len(existing_session.messages) > 0

    if history_found:
        interaction_started = True
        logger.info(f"Resuming active session {client_id} (History found). Checking for pending nudges...")
        
        # Look for the last bot message to provide context for potential follow-up resume
        last_bot_msg = ""
        for m in reversed(existing_session.messages):
            if m.role == "model":
                for p in m.parts:
                    if hasattr(p, 'text') and p.text:
                        last_bot_msg = p.text
                        break
                if last_bot_msg: break
        
        # If the last message was from the bot and we haven't reached the nudge limit, resume the routine
        if last_bot_msg and session_nudge_counts.get(client_id, 0) < 2:
            followup_task = asyncio.create_task(follow_up_routine(last_bot_msg))
            logger.info(f"Resumed follow-up routine for {client_id}")
    else:
        # No history found. Skip cold-start if this is a refresh (conn > 1)
        if conn_count > 1:
            interaction_started = True
            logger.info(f"Skipping cold-start for fresh refresh on {client_id}")
        else:
            cold_start_task = asyncio.create_task(cold_start_routine())
            logger.info(f"Started one-shot cold-start timer for {client_id}")
    
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
                    session_nudge_counts[client_id] = 0
                    continue

                elif msg_type == "text_input":
                    cancel_followup()
                    cancel_cold_start()
                    interaction_started = True
                    session_nudge_counts[client_id] = 0
                    user_text = data.get("text", "").strip()
                    if not user_text:
                        continue

                    # Echo user text back
                    await websocket.send_json({"type": "transcript", "text": user_text})

                    # Agent Processing
                    response_text = ""
                    session = await session_service.get_session(
                        app_name="CryptoBackend", user_id="user", session_id=client_id
                    )
                    if not session:
                        await session_service.create_session(
                            app_name="CryptoBackend", user_id="user", session_id=client_id
                        )

                    # --- Agent Execution with Smart Retry Logic ---
                    max_retries = 3
                    try:
                        for attempt in range(1, max_retries + 1):
                            try:
                                logger.info(f"Running agent for {client_id} (attempt {attempt})...")
                                async for event in runner.run_async(
                                    user_id="user",
                                    session_id=client_id,
                                    new_message=types.Content(role="user", parts=[types.Part(text=user_text)])
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
                                        await websocket.send_json({"type": "response.text_partial", "text": chunk_text})

                                logger.info(f"Agent reply complete: {len(response_text)} chars.")
                                if not response_text.strip():
                                    response_text = "I'm sorry, I couldn't process that. Please try again."
                                    await websocket.send_json({"type": "response.text_partial", "text": response_text})
                                await websocket.send_json({"type": "response.text", "text": response_text})
                                
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
                                    await websocket.send_json({
                                        "type": "error",
                                        "message": "Our analysis engine is temporarily unavailable. Please try again in a moment."
                                    })

                            except Exception as e:
                                err_msg = str(e)
                                is_429 = "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg
                                is_401 = "401" in err_msg or "UNAUTHORIZED" in err_msg
                                is_503 = (GeminiServerError and isinstance(e, GeminiServerError) and "503" in err_msg) or "503" in err_msg

                                if is_429:
                                    logger.error(f"❌ Gemini Quota Exceeded (429): {err_msg}")
                                    await websocket.send_json({"type": "error", "message": "I've hit my daily limit for analysis. Please try again tomorrow or upgrade your Gemini API key plan."})
                                    break
                                elif is_401:
                                    logger.error(f"❌ Gemini API Key Error (401): {err_msg}")
                                    await websocket.send_json({"type": "error", "message": "My API key seems to be invalid. Please check the .env file and ensure your Google AI Studio key is correct."})
                                    break
                                elif is_503 and attempt < max_retries:
                                    wait_time = attempt * 5
                                    logger.warning(f"⚠️ Gemini 503 overloaded (attempt {attempt}/{max_retries}). Retrying in {wait_time}s...")
                                    await websocket.send_json({"type": "response.text_partial", "text": f"_The AI model is busy. Retrying in {wait_time} seconds..._"})
                                    await asyncio.sleep(wait_time)
                                    response_text = ""
                                elif is_503:
                                    logger.error(f"❌ Gemini still overloaded after {max_retries} attempts.")
                                    await websocket.send_json({"type": "error", "message": "The AI model is currently under heavy load. Please try again in 30 seconds."})
                                    break
                                else:
                                    logger.error(f"Unhandled Agent error: {err_msg}", exc_info=True)
                                    await websocket.send_json({"type": "error", "message": "An unexpected error occurred. Please refresh and try again."})
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


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

