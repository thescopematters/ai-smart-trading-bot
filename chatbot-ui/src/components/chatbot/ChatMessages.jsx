/* eslint-disable react-hooks/set-state-in-effect */
/* eslint-disable no-unused-vars */
import React, { useEffect, useRef, useState, useCallback } from 'react';
import clsx from 'clsx';
import ReactMarkdown from 'react-markdown';
import cryptobotAvatar from '../../assets/cryptobot_avatar_cute.png';
import { ArrowDown } from 'lucide-react';

import remarkGfm from 'remark-gfm';

const ChatMessages = ({ messages, isTyping }) => {
    const messagesEndRef = useRef(null);
    const scrollContainerRef = useRef(null);
    const [isNearBottom, setIsNearBottom] = useState(true);

    const scrollToBottom = useCallback((behavior = "smooth") => {
        messagesEndRef.current?.scrollIntoView({ behavior });
        setIsNearBottom(true);
    }, []);

    // Detect if user is near bottom
    const handleScroll = useCallback(() => {
        if (!scrollContainerRef.current) return;
        
        const { scrollTop, scrollHeight, clientHeight } = scrollContainerRef.current;
        // If user is within 100px of the bottom, we consider them "at bottom"
        const isAtBottom = scrollHeight - scrollTop - clientHeight < 100;
        setIsNearBottom(isAtBottom);
    }, []);

    // Only auto-scroll if user is already looking at the bottom
    useEffect(() => {
        if (isNearBottom) {
            scrollToBottom();
        }
    }, [messages, isTyping, isNearBottom, scrollToBottom]);

    // Initial scroll
    useEffect(() => {
        scrollToBottom("auto");
    }, []);

    return (
        <div className="flex-1 relative overflow-hidden flex flex-col min-h-0">
            <div 
                ref={scrollContainerRef}
                onScroll={handleScroll}
                className="flex-1 overflow-y-auto p-4 space-y-6 custom-scrollbar overscroll-contain"
            >
                {messages.map((msg) => (
                    <div
                        key={msg.id}
                        className={clsx(
                            "flex w-full",
                            msg.isUser ? "justify-end" : "justify-start"
                        )}
                    >
                        {!msg.isUser && (
                            <div className="w-8 h-8 rounded-full overflow-hidden shrink-0 shadow-md border border-slate-200 bg-white mr-3">
                                <img src={cryptobotAvatar} alt="CryptoBot" className="w-full h-full object-cover" />
                            </div>
                        )}

                        <div className={clsx("flex flex-col max-w-[80%] min-w-0", msg.isUser ? "items-end" : "items-start")}>
                            <div
                                className={clsx(
                                    "rounded-2xl px-5 py-3 text-sm shadow-sm min-w-0 overflow-x-auto",
                                    msg.isUser
                                        ? "bg-violet-600 text-white rounded-br-none shadow-indigo-500/20"
                                        : msg.isError
                                            ? "bg-red-50 text-red-900 border border-red-200 shadow-sm rounded-bl-none"
                                            : "bg-white text-gray-900 shadow-sm rounded-bl-none border border-slate-100"
                                )}
                            >
                                {msg.isUser ? (
                                    msg.text
                                ) : (
                                    <div className="prose prose-slate prose-sm max-w-none text-gray-900">
                                        <ReactMarkdown
                                            remarkPlugins={[remarkGfm]}
                                            components={{
                                                p: ({ node, ...props }) => <p className="mb-2 last:mb-0" {...props} />,
                                                ul: ({ node, ...props }) => <ul className="list-disc pl-4 mb-2" {...props} />,
                                                ol: ({ node, ...props }) => <ol className="list-decimal pl-4 mb-2" {...props} />,
                                                li: ({ node, ...props }) => <li className="mb-1" {...props} />,
                                                a: ({ node, ...props }) => <a className="text-neon-blue hover:underline" target="_blank" rel="noopener noreferrer" {...props} />,
                                                code: ({ node, inline, className, children, ...props }) => {
                                                    return inline ? (
                                                        <code className="bg-indigo-50 px-1.5 py-0.5 rounded text-indigo-900 font-mono text-xs border border-indigo-100 font-semibold" {...props}>
                                                            {children}
                                                        </code>
                                                    ) : (
                                                        <code className="block bg-slate-800 text-slate-200 p-3 rounded-xl text-xs font-mono my-2 whitespace-pre-wrap shadow-inner" {...props}>
                                                            {children}
                                                        </code>
                                                    )
                                                },
                                                table: ({ node, ...props }) => (
                                                    <div className="overflow-x-auto max-w-full my-4 rounded-xl border border-slate-200">
                                                        <table className="min-w-full divide-y divide-slate-200" {...props} />
                                                    </div>
                                                ),
                                                thead: ({ node, ...props }) => <thead className="bg-slate-50" {...props} />,
                                                th: ({ node, ...props }) => <th className="px-4 py-2 text-left text-xs font-bold text-slate-600 uppercase tracking-wider" {...props} />,
                                                td: ({ node, ...props }) => <td className="px-4 py-2 text-xs text-slate-700 whitespace-normal break-words border-t border-slate-100" {...props} />,
                                                tr: ({ node, ...props }) => <tr className="hover:bg-slate-50/50 transition-colors" {...props} />
                                            }}
                                        >
                                            {msg.text || ''}
                                        </ReactMarkdown>
                                    </div>
                                )}
                            </div>
                            {msg.timestamp && msg.id !== 'greeting' && (
                                <span className={clsx("text-[10px] text-slate-500/80 font-semibold mt-1 px-1", msg.isUser ? "text-right" : "text-left")}>
                                    {msg.timestamp}
                                </span>
                            )}
                        </div>
                    </div>
                ))}

                {isTyping && (
                    <div className="flex justify-start">
                        <div className="w-8 h-8 mr-3 shrink-0 rounded-full overflow-hidden shadow-sm border border-slate-200 bg-white">
                            <img src={cryptobotAvatar} alt="CryptoBot" className="w-full h-full object-cover opacity-60" />
                        </div>
                        <div className="bg-white rounded-2xl rounded-bl-none px-4 py-3 flex gap-1 items-center shadow-sm border border-slate-100">
                            <span className="w-2 h-2 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: '0s' }}></span>
                            <span className="w-2 h-2 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></span>
                            <span className="w-2 h-2 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></span>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Floating Jump to Bottom Button / Typing Indicator */}
            {isTyping && !isNearBottom && (
                <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-20">
                    <button 
                        onClick={() => scrollToBottom()}
                        className="bg-violet-600/90 text-white p-3 rounded-full shadow-lg backdrop-blur-sm flex items-center justify-center hover:bg-violet-700 transition-all active:scale-95 animate-in fade-in slide-in-from-bottom-4 duration-300 group"
                    >
                        <div className="flex gap-1">
                            <span className="w-1.5 h-1.5 bg-white rounded-full animate-bounce" style={{ animationDelay: '0s' }}></span>
                            <span className="w-1.5 h-1.5 bg-white rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></span>
                            <span className="w-1.5 h-1.5 bg-white rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></span>
                        </div>
                    </button>
                </div>
            )}
        </div>
    );
};

export default ChatMessages;
