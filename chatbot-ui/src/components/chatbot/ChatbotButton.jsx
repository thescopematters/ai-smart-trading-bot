import React from 'react';
import { MessageSquare, Mic } from 'lucide-react';

const ChatbotButton = ({ onClick, isOpen }) => {
    return (
        <button
            onClick={onClick}
            className={`fixed bottom-6 right-6 z-50 flex items-center justify-center transition-all duration-300 ${isOpen
                    ? 'w-12 h-12 rounded-full bg-red-500/20 text-red-400 border border-red-500 hover:bg-red-500/30'
                    : 'w-16 h-16 rounded-full bg-neon-blue/10 text-neon-blue border border-neon-blue shadow-[0_0_20px_rgba(0,243,255,0.4)] hover:scale-105 animate-pulse-slow'
                }`}
        >
            {isOpen ? (
                <span className="text-xl font-bold">✕</span>
            ) : (
                <div className="relative">
                    <MessageSquare className="w-8 h-8" />
                    <span className="absolute -top-1 -right-1 flex h-3 w-3">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-neon-purple opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-3 w-3 bg-neon-purple"></span>
                    </span>
                </div>
            )}
        </button>
    );
};

export default ChatbotButton;