import React, { useState } from 'react';
import { MessageSquare, X } from 'lucide-react';
import ChatbotPanel from './ChatbotPanel';

const ChatWidget = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [isMaximized, setIsMaximized] = useState(false);

    const handleToggle = () => {
        if (isOpen) { setIsOpen(false); setIsMaximized(false); }
        else setIsOpen(true);
    };

    const handleClose = () => { setIsOpen(false); setIsMaximized(false); };
    const toggleMaximize = () => setIsMaximized(prev => !prev);

    return (
        <>
            {/* Bubble */}
            <button
                onClick={handleToggle}
                className={`fixed bottom-5 right-4 sm:right-6 z-[60] w-14 h-14 rounded-full shadow-2xl transition-all duration-300 flex items-center justify-center
                    ${isOpen ? 'bg-slate-700 hover:bg-slate-800' : 'bg-indigo-600 hover:bg-indigo-500 hover:scale-110'}`}
            >
                {isOpen ? <X className="w-5 h-5 text-white" /> : <MessageSquare className="w-6 h-6 text-white" />}
                {!isOpen && (
                    <span className="absolute -top-1 -right-1 flex h-3.5 w-3.5">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-violet-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-3.5 w-3.5 bg-violet-500 border-2 border-white"></span>
                    </span>
                )}
            </button>

            {/* Small popup - mobile full width, desktop fixed */}
            {isOpen && !isMaximized && (
                <div className="fixed z-40 overflow-hidden border border-slate-200 flex flex-col bg-white
                    bottom-0 left-0 right-0 h-[92dvh] rounded-t-3xl
                    sm:bottom-24 sm:left-auto sm:right-6 sm:w-[420px] sm:h-[600px] sm:rounded-2xl
                    shadow-2xl shadow-indigo-900/20"
     style={{ paddingBottom: 'env(safe-area-inset-bottom)' }}>
                    <ChatbotPanel onMaximize={toggleMaximize} isMaximized={false} />
                </div>
            )}

            {/* Maximized modal */}
            {isOpen && isMaximized && (
                <>
                    <div className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm" onClick={handleClose} />
                    <div className="fixed inset-0 z-50 flex items-center justify-center p-0 sm:p-8">
                        <div className="w-full max-w-5xl h-[100dvh] sm:h-[82vh] sm:rounded-2xl rounded-none shadow-2xl overflow-hidden border border-slate-200 flex flex-col bg-white sm:mt-4">
                            <ChatbotPanel onMaximize={toggleMaximize} isMaximized={true} />
                        </div>
                    </div>
                </>
            )}
        </>
    );
};

export default ChatWidget;