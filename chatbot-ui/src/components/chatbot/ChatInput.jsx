/* eslint-disable react-hooks/set-state-in-effect */
import React, { useState, useRef, useEffect } from "react";
import { Send, Mic, MicOff, Loader2, X, Check } from "lucide-react";
import { useToast } from "../../context/ToastContext";

const ChatInput = ({
  onSendMessage,
  onAudioChunk,
  onRecordingStop,
  currentTranscript,
  isTyping,
  onTyping,
  isSessionEnd,
  onNewChat,
}) => {
  const toast = useToast();
  const [message, setMessage] = useState("");
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [audioVolumes, setAudioVolumes] = useState(new Array(30).fill(4));
  const textareaRef = useRef(null);
  const streamRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const animationFrameRef = useRef(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 100)}px`;
    }
  }, [message]);

  const cleanupAudioAnalyser = () => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    if (audioContextRef.current && audioContextRef.current.state !== "closed") {
      audioContextRef.current.close().catch(console.error);
      audioContextRef.current = null;
    }
    analyserRef.current = null;
    setAudioVolumes(new Array(30).fill(4));
  };

  // Cleanup microphone on unmount
  useEffect(() => {
    return () => {
      cleanupAudioAnalyser();
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
      }
    };
  }, []);

  // Clean transcription and strip silence tokens
  useEffect(() => {
    if (currentTranscript !== undefined) {
      setIsProcessing(false);
    }
    if (currentTranscript && currentTranscript.trim()) {
      // Strip any transcription annotations wrapped in brackets or parentheses (e.g. [BLANK_AUDIO], [INAUDIBLE])
      let cleaned = currentTranscript
        .replace(/\[[^\]]*\]/g, "")
        .replace(/\([^\)]*\)/g, "")
        .trim();

      if (cleaned) {
        setMessage(
          (prev) => (prev.trim() ? prev + " " : "") + cleaned,
        );
      }
    }
  }, [currentTranscript]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      // Initialize Web Audio API Analyser for real-time responsiveness
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      if (AudioContextClass) {
        const audioCtx = new AudioContextClass();
        const analyser = audioCtx.createAnalyser();
        analyser.fftSize = 64; // 32 frequency bins
        analyser.smoothingTimeConstant = 0.6; // smooth transition
        const source = audioCtx.createMediaStreamSource(stream);
        source.connect(analyser);

        audioContextRef.current = audioCtx;
        analyserRef.current = analyser;

        const dataArray = new Uint8Array(analyser.frequencyBinCount);
        let lastUpdateTime = 0;
        const updateWaveform = (timestamp) => {
          if (!analyserRef.current) return;

          // Update every 60ms to make the wave scroll forward smoothly
          if (timestamp - lastUpdateTime >= 60) {
            lastUpdateTime = timestamp;
            analyserRef.current.getByteFrequencyData(dataArray);

            // Calculate average volume focusing on low/mid frequencies (first 16 bins)
            let sum = 0;
            const binsToAverage = Math.min(dataArray.length, 16);
            for (let i = 0; i < binsToAverage; i++) {
              sum += dataArray[i];
            }
            const average = sum / binsToAverage;

            // Push new volume to the end and shift array to make it scroll
            setAudioVolumes((prev) => [...prev.slice(1), Math.max(average, 4)]);
          }

          animationFrameRef.current = requestAnimationFrame(updateWaveform);
        };
        animationFrameRef.current = requestAnimationFrame(updateWaveform);
      }

      // Use webm/opus — best quality for Whisper transcription
      const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : "audio/webm";

      const mediaRecorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0 && onAudioChunk) {
          onAudioChunk(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        cleanupAudioAnalyser();
        stream.getTracks().forEach((track) => track.stop());
        if (onRecordingStop) onRecordingStop();
      };

      mediaRecorder.start(500); // 500ms chunks for smoother streaming
      setIsListening(true);
    } catch (err) {
      console.error("Microphone access denied:", err);
      toast({
        type: "error",
        message:
          "Could not access microphone. Please check browser permissions.",
      });
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isListening) {
      mediaRecorderRef.current.stop();
      setIsListening(false);
      setIsProcessing(true); // Show processing state while whisper.cpp runs
    }
  };

  const handleVoiceClick = () => {
    if (isListening) stopRecording();
    else startRecording();
  };

  const handleSubmit = (e) => {
    if (e) e.preventDefault();
    if (isListening) stopRecording();
    // Prevent sending if message is empty OR if AI is currently responding
    if (message.trim() && !isTyping) {
      onSendMessage(message.trim());
      setMessage("");
      // Reset height
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleChange = (e) => {
    setMessage(e.target.value);
    if (onTyping) onTyping();
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="p-2 pb-[max(1rem,env(safe-area-inset-bottom))] bg-white/40 backdrop-blur-xl relative border-t border-slate-200 shadow-inner"
    >
      <div
        className={`flex items-center gap-3 bg-white rounded-full relative transition-all duration-500 ease-out border border-slate-300`}
      >
        {/* Mic Button */}
        <button
          type="button"
          onClick={handleVoiceClick}
          disabled={isProcessing || isTyping || isSessionEnd}
          title={
            isSessionEnd
              ? "Session ended"
              : isListening
                ? "Stop recording"
                : isProcessing
                  ? "Processing..."
                  : isTyping
                    ? "AI is thinking..."
                    : "Start voice input"
          }
          className={`relative z-10 flex items-center justify-center w-8 h-8 rounded-full group shrink-0 ml-2 ${isListening
              ? "bg-red-500 text-white"
              : isProcessing || isTyping || isSessionEnd
                ? "text-slate-200 cursor-not-allowed"
                : "text-slate-400 hover:bg-slate-100 hover:text-slate-600"
            }`}
        >
          {isListening ? (
            <div className="w-3.5 h-3.5 bg-white rounded-sm" />
          ) : isProcessing ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Mic className="w-5 h-5 group-hover:scale-110 transition-transform duration-300" />
          )}
        </button>

        <div className="flex-1 relative flex items-center h-full min-h-[36px]">
          {isSessionEnd ? (
            <div className="w-full bg-transparent border-0 px-2 py-3 text-slate-500">
              Session ended due to inactivity.{" "}
              <button
                type="button"
                onClick={onNewChat}
                className="text-[#072042] hover:text-[#072042] hover:underline font-medium"
              >
                Click here
              </button>{" "}
              to start a new conversation.
            </div>
          ) : isListening ? (
            <div className="flex items-center gap-1 w-full px-1 py-1">
              {/* Waveform container with real-time responsive heights */}
              <div className="flex items-center gap-[2.5px] flex-1 h-8 overflow-hidden justify-center px-2">
                {audioVolumes.map((vol, i) => {
                  // vol is from 0 to 255 (or 4). Scale to max 28px height, min 5px
                  const height = 5 + (vol / 255) * 23;
                  return (
                    <div
                      key={i}
                      className="w-[3px] rounded-full bg-slate-400 shrink-0 transition-[height] duration-75"
                      style={{
                        height: `${height}px`,
                      }}
                    />
                  );
                })}
              </div>

              {/* X — cancel, no transcription */}
              <button
                type="button"
                onClick={() => {
                  if (mediaRecorderRef.current) {
                    mediaRecorderRef.current.onstop = null;
                    mediaRecorderRef.current.stop();
                  }
                  cleanupAudioAnalyser();
                  if (streamRef.current) {
                    streamRef.current.getTracks().forEach((t) => t.stop());
                  }
                  setIsListening(false);
                  setIsProcessing(false);
                }}
                className="w-8 h-8 flex items-center justify-center rounded-full border border-slate-200 hover:bg-red-50 text-slate-400 hover:text-red-500 transition-all shrink-0"
              >
                <X className="w-4 h-4" />
              </button>

              {/* ✓ — confirm, send to Whisper */}
              <button
                type="button"
                onClick={stopRecording}
                className="w-8 h-8 flex items-center justify-center rounded-full border border-slate-200 hover:bg-green-50 text-slate-400 hover:text-green-600 transition-all shrink-0"
              >
                <Check className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <textarea
              ref={textareaRef}
              rows={1}
              value={message}
              onChange={handleChange}
              onKeyDown={handleKeyDown}
              placeholder="Message Crypto AI..."
              className={`w-full bg-transparent border-0 px-1 py-2 text-base text-slate-700 placeholder-slate-400 focus:outline-none focus:ring-0 focus:ring-offset-0 focus:border-0 outline-none transition-opacity duration-300 resize-none max-h-[120px] overflow-y-auto ${isListening || isProcessing ? "opacity-60" : "opacity-100"}`}
              style={{
                WebkitTapHighlightColor: "transparent",
                boxShadow: "none",
              }}
              disabled={isListening || isProcessing}
            />
          )}
        </div>

        {!isListening && (
          <button
            type="submit"
            disabled={
              !message.trim() || isProcessing || isTyping || isSessionEnd
            }
            className="p-2 mr-2 rounded-full text-slate-500 hover:bg-slate-100 hover:text-slate-800 disabled:opacity-50 disabled:cursor-not-allowed shrink-0"
          >
            <Send className="w-4 h-4" />
          </button>
        )}
      </div>
    </form>
  );
};

export default ChatInput;
