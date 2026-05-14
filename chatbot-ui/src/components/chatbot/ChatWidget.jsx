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
                className={`fixed bottom-4 right-4 sm:right-6 z-[60] w-12 h-12 rounded-full shadow-xl transition-all duration-500 ease-out flex items-center justify-center active:scale-90
                ${isOpen ? 'hidden sm:flex bg-slate-700 hover:bg-slate-800' : 'flex bg-[#072042] hover:bg-[#0a2a52] hover:scale-110'}`}
                >
                <div className={`transition-transform duration-500 flex items-center justify-center ${isOpen ? 'rotate-180' : 'rotate-0'}`}>
                    {isOpen ? <X className="w-4 h-4 text-white" /> : <MessageSquare className="w-5 h-5 text-white" />}
                </div>
                {!isOpen && (
                    <span className="absolute -top-1 -right-1 flex h-3 w-3">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#072042] opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-3 w-3 bg-[#072042] border-2 border-white"></span>
                    </span>
                )}
            </button>

            {/* Chat Panel Container */}
            <div className={`fixed z-50 transition-all duration-300 ease-[cubic-bezier(0.4,0,0.2,1)] flex flex-col bg-white overflow-hidden shadow-2xl
                ${isOpen 
                    ? 'opacity-100 scale-100 translate-y-0 pointer-events-auto' 
                    : 'opacity-0 scale-90 translate-y-8 pointer-events-none'
                }
                ${isMaximized 
                    ? 'inset-0 sm:inset-8 sm:mt-16 sm:max-w-5xl sm:mx-auto sm:h-[82vh] sm:rounded-2xl rounded-none' 
                    : 'bottom-0 left-0 right-0 h-[92dvh] rounded-t-3xl sm:bottom-[88px] sm:left-auto sm:right-6 sm:w-[400px] sm:rounded-2xl sm:max-h-[calc(100vh-12rem)] shadow-indigo-900/20'
                }`}
                style={{ 
                    paddingBottom: isMaximized ? '0' : 'env(safe-area-inset-bottom)',
                    transformOrigin: isMaximized ? 'center' : 'bottom right'
                }}
            >
                <ChatbotPanel 
                    onClose={handleClose} 
                    onMaximize={toggleMaximize} 
                    isMaximized={isMaximized} 
                />
            </div>

            {/* Backdrop for Maximized State */}
            {isOpen && isMaximized && (
                <div 
                    className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm transition-opacity duration-300" 
                    onClick={handleClose} 
                />
            )}
        </>
    );
};

export default ChatWidget;