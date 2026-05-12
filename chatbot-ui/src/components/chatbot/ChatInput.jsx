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
  const [waveOffset, setWaveOffset] = useState(0);
  const textareaRef = useRef(null);
  const streamRef = useRef(null);
  const mediaRecorderRef = useRef(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 100)}px`;
    }
  }, [message]);

  // Cleanup microphone on unmount
  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
      }
    };
  }, []);

  // ... existing transcription useEffect ...
  useEffect(() => {
    if (currentTranscript !== undefined) {
      setIsProcessing(false);
    }
    if (currentTranscript && currentTranscript.trim()) {
      setMessage(
        (prev) => (prev.trim() ? prev + " " : "") + currentTranscript.trim(),
      );
    }
  }, [currentTranscript]);

  useEffect(() => {
    if (!isListening) return;
    const interval = setInterval(() => {
      setWaveOffset((prev) => prev + 1);
    }, 200); // speed — lower = faster scroll
    return () => clearInterval(interval);
  }, [isListening]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

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
        className={`flex items-center gap-3 bg-white rounded-full relative transition-all duration-500 ease-out ${
          isListening ? "border border-slate-300" : "border border-slate-300"
        }`}
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
          className={`relative z-10 flex items-center justify-center w-8 h-8 rounded-full group shrink-0 ml-2 ${
            isListening
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
              <div className="flex items-center gap-[2px] flex-1 h-8 overflow-hidden">
                {[...Array(48)].map((_, i) => (
                  <div
                    key={i}
                    className="w-[3px] rounded-full shrink-0"
                    style={{
                      height: `${5 + Math.abs(Math.sin((i - waveOffset) * 0.8)) * 24}px`,
                      backgroundColor: `rgba(15, 23, 42, ${0.2 + Math.abs(Math.sin((i - waveOffset) * 0.8)) * 0.8})`,
                      transition: "height 50ms ease",
                    }}
                  />
                ))}
              </div>

              {/* X — cancel, no transcription */}
              <button
                type="button"
                onClick={() => {
                  if (mediaRecorderRef.current) {
                    mediaRecorderRef.current.onstop = null;
                    mediaRecorderRef.current.stop();
                  }
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
