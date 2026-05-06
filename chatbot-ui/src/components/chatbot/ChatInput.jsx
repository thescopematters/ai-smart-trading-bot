import React, { useState, useRef, useEffect } from 'react';
import { Send, Mic, MicOff, Loader2 } from 'lucide-react';

const ChatInput = ({ onSendMessage, onAudioChunk, onRecordingStop, currentTranscript, isTyping, onTyping, isSessionEnd, onNewChat }) => {
    const [message, setMessage] = useState('');
    const [isListening, setIsListening] = useState(false);
    const [isProcessing, setIsProcessing] = useState(false);
    const textareaRef = useRef(null);
    const streamRef = useRef(null);
    const mediaRecorderRef = useRef(null);

    // Auto-resize textarea
    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
        }
    }, [message]);

    // Cleanup microphone on unmount
    useEffect(() => {
        return () => {
            if (streamRef.current) {
                streamRef.current.getTracks().forEach(track => track.stop());
            }
        };
    }, []);

    // ... existing transcription useEffect ...
    useEffect(() => {
        if (currentTranscript !== undefined) {
            setIsProcessing(false);
        }
        if (currentTranscript && currentTranscript.trim()) {
            setMessage(prev => (prev.trim() ? prev + ' ' : '') + currentTranscript.trim());
        }
    }, [currentTranscript]);

    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            streamRef.current = stream;

            // Use webm/opus — best quality for Whisper transcription
            const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
                ? 'audio/webm;codecs=opus'
                : 'audio/webm';

            const mediaRecorder = new MediaRecorder(stream, { mimeType });
            mediaRecorderRef.current = mediaRecorder;

            mediaRecorder.ondataavailable = (event) => {
                if (event.data && event.data.size > 0 && onAudioChunk) {
                    onAudioChunk(event.data);
                }
            };

            mediaRecorder.onstop = () => {
                stream.getTracks().forEach(track => track.stop());
                if (onRecordingStop) onRecordingStop();
            };

            mediaRecorder.start(500); // 500ms chunks for smoother streaming
            setIsListening(true);
        } catch (err) {
            console.error('Microphone access denied:', err);
            alert('Could not access microphone. Please check browser permissions.');
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
            setMessage('');
            // Reset height
            if (textareaRef.current) {
                textareaRef.current.style.height = 'auto';
            }
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit();
        }
    };

    const handleChange = (e) => {
        setMessage(e.target.value);
        if (onTyping) onTyping();
    };

    return (
        <form onSubmit={handleSubmit} className="p-4 bg-white/40 backdrop-blur-xl relative border-t border-white/40 shadow-inner">
            <div className={`flex items-end gap-3 bg-white rounded-3xl p-2 relative transition-all duration-500 ease-out ${isListening
                ? 'shadow-[0_0_40px_-5px_rgba(139,92,246,0.3)] border-violet-100 scale-[1.01]'
                : 'shadow-xl shadow-indigo-500/10 border border-indigo-50'
                }`}>

                {/* Mic Button */}
                <button
                    type="button"
                    onClick={handleVoiceClick}
                    disabled={isProcessing || isTyping || isSessionEnd}
                    title={isSessionEnd ? 'Session ended' : isListening ? 'Stop recording' : isProcessing ? 'Processing...' : isTyping ? 'AI is thinking...' : 'Start voice input'}
                    className={`relative z-10 flex items-center justify-center w-12 h-12 rounded-full transition-all duration-300 group shrink-0 mb-0.5 ${isListening
                        ? 'bg-violet-600 text-white shadow-lg shadow-violet-500/40'
                        : (isProcessing || isTyping || isSessionEnd)
                            ? 'bg-slate-50 text-slate-300 border border-slate-100 cursor-not-allowed'
                            : 'bg-slate-50 text-slate-400 hover:bg-indigo-50 border border-slate-100 hover:text-indigo-500 hover:shadow-md'
                        }`}
                >
                    {isListening ? (
                        /* ChatGPT-style Fluid Morphing Orb */
                        <div className="relative flex items-center justify-center w-full h-full">
                            {/* Base glow */}
                            <div className="absolute inset-0 bg-white/20 rounded-full animate-pulse" />
                            {/* Inner core orb */}
                            <div className="absolute w-6 h-6 bg-white rounded-full animate-ping" style={{ animationDuration: '2s' }} />
                            <div className="absolute w-4 h-4 bg-white rounded-full shadow-[0_0_15px_5px_rgba(255,255,255,0.8)]" />
                        </div>
                    ) : isProcessing ? (
                        <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                        <Mic className="w-5 h-5 group-hover:scale-110 transition-transform duration-300" />
                    )}

                    {/* Ripple rings when listening */}
                    {isListening && (
                        <>
                            <span className="absolute inset-[-4px] rounded-full border-2 border-violet-400 animate-[ping_1.5s_ease-in-out_infinite] opacity-40 shadow-[0_0_20px_rgba(139,92,246,0.6)]" />
                            <span className="absolute inset-[-12px] rounded-full border border-fuchsia-400 animate-[ping_2.5s_ease-in-out_infinite] opacity-20 shadow-[0_0_30px_rgba(217,70,239,0.3)]" />
                        </>
                    )}
                </button>

                <div className="flex-1 relative flex items-center h-full min-h-[48px]">
                    {isSessionEnd ? (
                        <div className="w-full bg-transparent border-0 px-2 py-3 text-slate-500">
                            Session ended due to inactivity. <button type="button" onClick={onNewChat} className="text-violet-500 hover:text-violet-600 hover:underline font-medium">Click here</button> to start a new conversation.
                        </div>
                    ) : (
                        <textarea
                            ref={textareaRef}
                            rows={1}
                            value={message}
                            onChange={handleChange}
                            onKeyDown={handleKeyDown}
                            placeholder="Message Crypto AI..."
                            className={`w-full bg-transparent border-0 px-2 py-3 text-slate-700 placeholder-slate-400 focus:outline-none focus:ring-0 focus:ring-offset-0 focus:border-0 outline-none transition-opacity duration-300 resize-none scrollbar-hide max-h-[200px] ${isListening || isProcessing ? 'opacity-60' : 'opacity-100'}`}
                            style={{ WebkitTapHighlightColor: 'transparent', boxShadow: 'none' }}
                            disabled={isListening || isProcessing}
                        />
                    )}
                </div>

                <button
                    type="submit"
                    disabled={!message.trim() || isProcessing || isTyping || isSessionEnd}
                    className="p-3 mr-1 mb-0.5 rounded-full bg-slate-900 text-white hover:bg-black disabled:opacity-30 disabled:cursor-not-allowed transition-all duration-300 group shadow-md shrink-0"
                >
                    <Send className="w-4 h-4 translate-x-[1px] -translate-y-[1px] group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform" />
                </button>
            </div>
        </form>
    );
};

export default ChatInput;
