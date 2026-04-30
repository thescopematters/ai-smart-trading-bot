import os
import asyncio
import logging
import json
import re
import subprocess
import tempfile
import traceback
from dotenv import load_dotenv

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

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.genai import types
from agent import root_agent # Import the root agent

# Import Gemini error types for smart retry logic
try:
    from google.genai.errors import ServerError as GeminiServerError
except ImportError:
    GeminiServerError = None


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

try:
    import rag_service
except ImportError:
    from . import rag_service

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

@app.websocket("/ws/chat/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    logger.info(f"Client {client_id} connected")

    # Audio buffer: accumulates raw webm bytes from MediaRecorder chunks
    audio_buffer = bytearray()

    try:
        while True:
            message = await websocket.receive()

            if "bytes" in message and message["bytes"]:
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

                elif msg_type == "text_input":
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
                    # Retries on: MCP crash (ConnectionError) OR Gemini overload (503)
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
                                break  # Success — exit retry loop

                            except (ConnectionError, BrokenPipeError, OSError) as e:
                                # MCP subprocess likely crashed — retry
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
                                # 429 = Quota Exceeded / Rate Limit
                                is_429 = "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg
                                # 401 = Invalid API Key / Unauthorized
                                is_401 = "401" in err_msg or "UNAUTHORIZED" in err_msg
                                # 503 = Service Unavailable (Model Overloaded)
                                is_503 = (GeminiServerError and isinstance(e, GeminiServerError) and "503" in err_msg) or "503" in err_msg

                                if is_429:
                                    logger.error(f"❌ Gemini Quota Exceeded (429): {err_msg}")
                                    await websocket.send_json({
                                        "type": "error",
                                        "message": "I've hit my daily limit for analysis. Please try again tomorrow or upgrade your Gemini API key plan."
                                    })
                                    break
                                elif is_401:
                                    logger.error(f"❌ Gemini API Key Error (401): {err_msg}")
                                    await websocket.send_json({
                                        "type": "error",
                                        "message": "My API key seems to be invalid. Please check the .env file and ensure your Google AI Studio key is correct."
                                    })
                                    break
                                elif is_503 and attempt < max_retries:
                                    wait_time = attempt * 5
                                    logger.warning(f"⚠️ Gemini 503 overloaded (attempt {attempt}/{max_retries}). Retrying in {wait_time}s...")
                                    await websocket.send_json({
                                        "type": "response.text_partial",
                                        "text": f"_The AI model is busy. Retrying in {wait_time} seconds..._"
                                    })
                                    await asyncio.sleep(wait_time)
                                    response_text = ""
                                elif is_503:
                                    logger.error(f"❌ Gemini still overloaded after {max_retries} attempts.")
                                    await websocket.send_json({
                                        "type": "error",
                                        "message": "The AI model is currently under heavy load. Please try again in 30 seconds."
                                    })
                                    break
                                else:
                                    logger.error(f"Unhandled Agent error: {err_msg}", exc_info=True)
                                    await websocket.send_json({"type": "error", "message": "An unexpected error occurred. Please refresh and try again."})
                                    break
                    except WebSocketDisconnect:
                        logger.info(f"Client {client_id} disconnected during agent execution.")
                        break # Stop processing if client is gone
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
        logger.info(f"Client {client_id} disconnected normally.")
    except RuntimeError as e:
        if "disconnect" in str(e).lower():
            logger.info(f"Client {client_id} disconnected abruptly.")
        else:
            logger.error(f"RuntimeError for {client_id}: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Unexpected error for {client_id}: {e}", exc_info=True)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
