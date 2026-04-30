import React, { useState, useEffect } from 'react';
import ChatHeader from './ChatHeader';
import ChatMessages from './ChatMessages';
import ChatInput from './ChatInput';
import { useChatWebSocket } from '../../hooks/useChatWebSocket';
import { MessagesSquare, MessageCircle } from 'lucide-react';
import cryptobotAvatar from '../../assets/cryptobot_avatar_cute.png';

// Helper to convert timestamp to "2 min ago", "1 hr ago", etc.
const getRelativeTime = (timestamp) => {
    if (!timestamp) return '';
    const now = Date.now();
    const diff = now - timestamp;

    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    const weeks = Math.floor(diff / 604800000);

    if (minutes < 1) return 'just now';
    if (minutes < 60) return `${minutes} min ago`;
    if (hours < 24) return `${hours} hr ago`;
    if (days < 7) return `${days} day ago`;
    return `${weeks} week ago`;
};

// Helper to strip markdown symbols like **, * from previews
const stripMarkdown = (text) => {
    if (!text) return '';
    return text
        .replace(/\*\*(.*?)\*\*/g, '$1') // Strip bold
        .replace(/__(.*?)__/g, '$1')     // Strip underline
        .replace(/\*(.*?)\*/g, '$1')     // Strip italic
        .replace(/^\s*[\*\-]\s+/gm, '')  // Strip bullet markers (* or -)
        .replace(/\n\* /g, ' ')          // Strip bullet markers in same line
        .replace(/`(.*?)`/g, '$1')       // Strip code
        .replace(/#+\s/g, '');           // Strip headers
};

const ChatbotPanel = () => {
    const [sessions, setSessions] = useState([]);
    const [showHistory, setShowHistory] = useState(false);

    // Auto-initialize to the last used session, or create a new one immediately
    const [activeSessionId, setActiveSessionId] = useState(() => {
        const lastSession = localStorage.getItem('last_crypto_session');
        if (lastSession) {
            return lastSession;
        }
        const newSession = `session-${Date.now()}`;
        localStorage.setItem('last_crypto_session', newSession);
        return newSession;
    });

    // Centralize the WebSocket connection here so it stays alive during history view
    const chatControls = useChatWebSocket(import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/chat', activeSessionId);

    // Sync session ID to localStorage across refreshes
    useEffect(() => {
        if (activeSessionId) {
            localStorage.setItem('last_crypto_session', activeSessionId);
        }
    }, [activeSessionId]);

    const loadSessions = () => {
        const loadedSessions = [];
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key.startsWith('crypto_chat_')) {
                const id = key.replace('crypto_chat_', '');
                try {
                    const data = JSON.parse(localStorage.getItem(key));
                    if (data && data.length > 1) {
                        let preview = "New Conversation";
                        const lastMsg = data[data.length - 1];
                        const lastTimeId = lastMsg && lastMsg.id ? lastMsg.id : 0;

                        if (lastMsg && lastMsg.text) {
                            preview = stripMarkdown(lastMsg.text);
                        }

                        loadedSessions.push({
                            id,
                            preview,
                            time: getRelativeTime(lastTimeId),
                            timestampRaw: lastTimeId
                        });
                    }
                } catch (e) {
                    // Ignore broken keys
                }
            }
        }
        loadedSessions.sort((a, b) => b.timestampRaw - a.timestampRaw);
        setSessions(loadedSessions);
    };

    useEffect(() => {
        loadSessions();
        window.addEventListener('chat_history_updated', loadSessions);
        return () => window.removeEventListener('chat_history_updated', loadSessions);
    }, []);

    const startNewChat = () => {
        const newId = `session-${Date.now()}`;
        setActiveSessionId(newId);
        setShowHistory(false);
    };

    const handleSelectSession = (id) => {
        setActiveSessionId(id);
        setShowHistory(false);
    };

    return (
        <div className="flex flex-col w-full h-full bg-gray-100/60 backdrop-blur-2xl md:rounded-3xl shadow-2xl shadow-indigo-500/10 border border-indigo-200 overflow-hidden relative">
            {showHistory ? (
                /* HISTORY LIST VIEW */
                <div className="flex flex-col w-full h-full bg-white/40 backdrop-blur-md">
                    <div className="flex items-center justify-between p-6 border-b border-indigo-50/50 bg-white/40">
                        <div className="flex items-center gap-3">
                            <h2 className="text-xl font-bold text-slate-800 tracking-wide">Your Chats</h2>
                        </div>
                        <button
                            onClick={startNewChat}
                            className="p-3 bg-gradient-to-r from-violet-600 to-indigo-600 text-white rounded-xl hover:shadow-lg hover:-translate-y-0.5 transition-all flex items-center justify-center shadow-md active:scale-95"
                            title="New Chat"
                        >
                            <MessagesSquare className="w-5 h-5" />
                        </button>
                    </div>

                    <div className="flex-1 overflow-y-auto w-full custom-scrollbar p-2">
                        {sessions.length === 0 ? (
                            <div className="flex flex-col items-center justify-center h-full text-slate-400 gap-4 p-8">
                                <MessageCircle className="w-16 h-16 text-slate-300" />
                                <p className="text-center font-medium">No past conversations found.<br />Start a new chat to begin!</p>
                            </div>
                        ) : (
                            <div className="flex flex-col gap-2 p-2">
                                {sessions.map((session) => (
                                    <div
                                        key={session.id}
                                        onClick={() => handleSelectSession(session.id)}
                                        className="flex items-center gap-4 p-4 cursor-pointer bg-white/60 hover:bg-white border border-white/40 rounded-2xl shadow-sm hover:shadow-md transition-all"
                                    >
                                        <div className="w-12 h-12 rounded-full overflow-hidden shrink-0 shadow-inner bg-white">
                                            <img src={cryptobotAvatar} alt="CryptoBot" className="w-full h-full object-cover" />
                                        </div>
                                        <div className="flex-1 overflow-hidden">
                                            <div className="flex justify-between items-baseline mb-1">
                                                <h3 className="font-bold text-slate-800">CryptoBot</h3>
                                                <span className="text-xs font-semibold text-slate-500">{session.time}</span>
                                            </div>
                                            <p className="text-sm text-slate-600 truncate">{session.preview}</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            ) : (
                /* ACTIVE CHAT VIEW */
                <ActiveChat
                    chatControls={chatControls}
                    onOpenHistory={() => setShowHistory(true)}
                />
            )}
        </div>
    );
};

const ActiveChat = ({ chatControls, onOpenHistory }) => {
    const {
        isConnected,
        messages,
        setMessages,
        isTyping,
        sendMessage,
        sendAudioChunk,
        sendTranscribeRequest,
        currentTranscript
    } = chatControls;

    // Add initial greeting if empty
    useEffect(() => {
        if (messages.length === 0) {
            setMessages([{ id: 1, text: "Hello! I'm your crypto AI assistant. How can I help you today?", isUser: false }]);
        }
    }, [messages.length, setMessages]);

    const handleSendMessage = (text) => {
        sendMessage(text);
    };

    return (
        <>
            <ChatHeader
                onClose={() => { }}
                status={!isConnected ? "Connecting..." : isTyping ? "Processing..." : "Online"}
                onOpenHistory={onOpenHistory}
            />

            <ChatMessages messages={messages} isTyping={isTyping} />

            {messages.length <= 1 && (
                <div className="px-4 pb-2 grid grid-cols-2 gap-2">
                    {[
                        "What is the price of Bitcoin?",
                        "What is the latest crypto news?",
                        "Show me the network stats for Dogecoin",
                        "Tell me the history of Bitcoin"
                    ].map((prompt, index) => (
                        <button
                            key={index}
                            onClick={() => handleSendMessage(prompt)}
                            className="text-left text-xs bg-white hover:bg-white/80 border border-white/60 hover:border-violet-200 text-slate-600 hover:text-violet-600 p-4 rounded-xl transition-all duration-300 shadow-sm hover:shadow-md hover:-translate-y-0.5"
                        >
                            {prompt}
                        </button>
                    ))}
                </div>
            )}

            <ChatInput
                onSendMessage={handleSendMessage}
                onAudioChunk={sendAudioChunk}
                onRecordingStop={() => {
                    sendTranscribeRequest();
                }}
                currentTranscript={currentTranscript}
                isTyping={isTyping}
            />
        </>
    );
};

export default ChatbotPanel;