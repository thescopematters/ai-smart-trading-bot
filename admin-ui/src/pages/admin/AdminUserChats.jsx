import React, { useState, useEffect } from 'react';
import { useAdminAuth } from '../../context/AdminAuthContext';
import { 
    MessageSquare, 
    User as UserIcon, 
    Calendar, 
    ArrowRight, 
    Clock, 
    Bot,
    Search,
    RefreshCcw,
    Circle
} from 'lucide-react';
import clsx from 'clsx';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { api } from '../../services/api';

const AdminUserChats = () => {
    const [sessions, setSessions] = useState([]);
    const [selectedSession, setSelectedSession] = useState(null);
    const [messages, setMessages] = useState([]);
    const [loading, setLoading] = useState(true);
    const [msgLoading, setMsgLoading] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const { token } = useAdminAuth();

    const fetchSessions = async () => {
        setLoading(true);
        try {
            const response = await api.get('/api/admin/sessions', token);
            if (response.ok) {
                const data = await response.json();
                setSessions(data);
            }
        } catch (err) {
            console.error("Failed to fetch sessions:", err);
        } finally {
            setLoading(false);
        }
    };

    const fetchMessages = async (sessionId) => {
        try {
            const response = await api.get(`/api/admin/sessions/${sessionId}/messages`, token);
            if (response.ok) {
                const data = await response.json();
                setMessages(data);
            }
        } catch (err) {
            console.error("Failed to fetch messages:", err);
        }
    };

    useEffect(() => {
        fetchSessions();
    }, [token]);

    const handleSelectSession = (session) => {
        setSelectedSession(session);
        fetchMessages(session.id);
    };

    const filteredSessions = sessions.filter(s => 
        (s.user?.email?.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (s.user?.username?.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (s.last_message?.toLowerCase().includes(searchQuery.toLowerCase()))
    );

    return (
        <div className="flex flex-col lg:flex-row gap-6 h-[calc(100vh-160px)] animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Sessions List */}
            <div className="w-full lg:w-80 xl:w-96 bg-card-bg border border-card-border rounded-3xl overflow-hidden flex flex-col shadow-sm shrink-0">
                <div className="p-6 border-b border-border-light">
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-xl font-bold text-text-primary flex items-center gap-2">
                            <MessageSquare className="text-primary-purple" size={20} />
                            Sessions
                        </h2>
                        <button onClick={fetchSessions} className="text-text-muted hover:text-text-primary transition-colors">
                            <RefreshCcw size={16} className={loading ? "animate-spin" : ""} />
                        </button>
                    </div>
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" size={14} />
                        <input 
                            type="text"
                            placeholder="Filter sessions..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="w-full bg-main-bg border border-border-light rounded-xl pl-9 pr-4 py-2 text-xs text-text-primary placeholder:text-text-muted focus:outline-none focus:border-primary-purple/50"
                        />
                    </div>
                </div>
                
                <div className="flex-1 overflow-y-auto custom-scrollbar p-3 space-y-2">
                    {loading ? (
                        <div className="flex flex-col items-center justify-center h-40 gap-3">
                            <div className="w-8 h-8 border-2 border-primary-purple border-t-transparent rounded-full animate-spin"></div>
                            <span className="text-xs text-text-muted font-medium tracking-wide">Retrieving chats...</span>
                        </div>
                    ) : filteredSessions.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-40 text-slate-500 px-6 text-center">
                            <MessageSquare size={32} className="mb-2 opacity-20" />
                            <p className="text-xs italic">No matching sessions found</p>
                        </div>
                    ) : (
                        filteredSessions.map((s) => (
                            <button
                                key={s.id}
                                onClick={() => handleSelectSession(s)}
                                className={clsx(
                                    "w-full text-left p-4 rounded-2xl transition-all border group relative overflow-hidden",
                                    selectedSession?.id === s.id 
                                        ? "bg-light-purple border-primary-purple/30 shadow-sm" 
                                        : "bg-card-bg border-transparent hover:bg-sidebar-active/50"
                                )}
                            >
                                <div className="flex justify-between items-start mb-2">
                                    <span className={clsx(
                                        "text-[9px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full shadow-sm text-white",
                                        s.user.is_guest ? "bg-amber-500" : "bg-primary-purple"
                                    )}>
                                        {s.user.is_guest ? "Guest" : "Member"}
                                    </span>
                                    <span className="text-[9px] text-text-muted font-mono">
                                        {new Date(s.updated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                    </span>
                                </div>
                                <h3 className="text-sm font-bold text-text-primary truncate mb-1">
                                    {s.user.email || s.user.username || "Anonymous User"}
                                </h3>
                                <p className="text-xs text-text-secondary truncate line-clamp-1 opacity-70">
                                    {s.last_message || "No messages yet"}
                                </p>
                            </button>
                        ))
                    )}
                </div>
            </div>

            {/* Message Viewer */}
            <div className="flex-1 bg-card-bg border border-card-border rounded-3xl overflow-hidden flex flex-col shadow-sm">
                {selectedSession ? (
                    <>
                        <div className="p-6 border-b border-border-light bg-sidebar-active/30 flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                <div className="w-12 h-12 rounded-2xl bg-light-purple flex items-center justify-center text-primary-purple border border-primary-purple/10 shadow-sm">
                                    <UserIcon size={24} />
                                </div>
                                <div>
                                    <h2 className="text-base font-bold text-text-primary leading-tight">
                                        {selectedSession.user.email || selectedSession.user.username}
                                    </h2>
                                    <div className="flex items-center gap-3 mt-1">
                                        <p className="text-[10px] text-text-muted uppercase tracking-widest font-mono">
                                            ID: {selectedSession.id.substring(0, 12)}...
                                        </p>
                                        <span className="w-1 h-1 rounded-full bg-border-light" />
                                        <p className="text-[10px] text-primary-purple font-bold uppercase tracking-widest">
                                            {selectedSession.user.role}
                                        </p>
                                    </div>
                                </div>
                            </div>
                            <div className="flex items-center gap-4">
                                <div className="flex flex-col items-end">
                                    <div className="flex items-center gap-2 text-xs text-text-secondary font-bold">
                                        <Calendar size={14} className="text-primary-purple" />
                                        {new Date(selectedSession.updated_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
                                    </div>
                                    <div className="flex items-center gap-2 text-[10px] text-text-muted mt-1 uppercase tracking-tighter">
                                        <Clock size={12} />
                                        Last Active: {new Date(selectedSession.updated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="flex-1 overflow-y-auto p-8 space-y-8 custom-scrollbar bg-main-bg relative">
                            {messages.length === 0 ? (
                                <div className="flex flex-col items-center justify-center h-full text-slate-500 gap-2">
                                    <MessageSquare size={48} className="opacity-10" />
                                    <p className="italic text-sm">No messages recorded in this session</p>
                                </div>
                            ) : (
                                messages.map((m, idx) => (
                                    <div 
                                        key={idx} 
                                        className={clsx(
                                            "flex gap-4 max-w-[85%]",
                                            m.role === 'user' ? "ml-auto flex-row-reverse" : "mr-auto"
                                        )}
                                    >
                                        <div className={clsx(
                                            "w-8 h-8 rounded-full shrink-0 flex items-center justify-center border",
                                            m.role === 'user' 
                                                ? "bg-sidebar-active border-border-light text-text-muted" 
                                                : "bg-light-purple border-primary-purple/20 text-primary-purple"
                                        )}>
                                            {m.role === 'user' ? <UserIcon size={14} /> : <Bot size={14} />}
                                        </div>
                                        <div className="flex flex-col space-y-2">
                                            <div className={clsx(
                                                "px-5 py-3.5 rounded-3xl text-sm leading-relaxed shadow-sm",
                                                m.role === 'user' 
                                                    ? "bg-text-primary text-white rounded-tr-none shadow-text-primary/10" 
                                                    : "bg-white text-text-primary border border-card-border rounded-tl-none prose prose-sm max-w-none prose-p:my-1 prose-a:text-primary-purple"
                                            )}>
                                                {m.role === 'user' ? (
                                                    m.content
                                                ) : (
                                                    <ReactMarkdown
                                                        remarkPlugins={[remarkGfm]}
                                                        components={{
                                                            p: ({ node, ...props }) => <p className="mb-2 last:mb-0" {...props} />,
                                                            ul: ({ node, ...props }) => <ul className="list-disc pl-4 mb-2" {...props} />,
                                                            ol: ({ node, ...props }) => <ol className="list-decimal pl-4 mb-2" {...props} />,
                                                            li: ({ node, ...props }) => <li className="mb-1" {...props} />,
                                                            a: ({ node, ...props }) => <a className="text-indigo-400 hover:underline" target="_blank" rel="noopener noreferrer" {...props} />,
                                                            code: ({ node, inline, className, children, ...props }) => {
                                                                return inline ? (
                                                                    <code className="bg-indigo-500/20 px-1.5 py-0.5 rounded text-indigo-200 font-mono text-xs border border-indigo-500/30" {...props}>
                                                                        {children}
                                                                    </code>
                                                                ) : (
                                                                    <code className="block bg-slate-900 text-slate-200 p-3 rounded-xl text-xs font-mono my-2 whitespace-pre-wrap shadow-inner" {...props}>
                                                                        {children}
                                                                    </code>
                                                                )
                                                            }
                                                        }}
                                                    >
                                                        {m.content}
                                                    </ReactMarkdown>
                                                )}
                                            </div>
                                            <span className={clsx(
                                                "text-[9px] text-text-muted font-bold uppercase tracking-widest",
                                                m.role === 'user' ? "text-right mr-1" : "ml-1"
                                            )}>
                                                {new Date(m.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                                            </span>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </>
                ) : (
                    <div className="flex-1 flex flex-col items-center justify-center text-text-muted gap-6">
                        <div className="relative">
                            <div className="absolute inset-0 bg-primary-purple/10 blur-3xl rounded-full"></div>
                            <div className="relative w-24 h-24 rounded-3xl bg-sidebar-active/30 flex items-center justify-center text-text-muted border border-border-light shadow-sm">
                                <MessageSquare size={48} className="animate-bounce" />
                            </div>
                        </div>
                        <div className="text-center space-y-2">
                            <h3 className="text-text-primary font-bold text-lg">Conversation Viewer</h3>
                            <p className="text-sm max-w-xs mx-auto text-text-secondary leading-relaxed font-medium">
                                Select a session from the left to view the full conversation history between the User and CryptoBot.
                            </p>
                        </div>
                        <div className="flex items-center gap-2 text-[10px] text-primary-purple font-black uppercase tracking-[0.2em] animate-pulse">
                            <Circle size={8} fill="currentColor" />
                            Awaiting Selection
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default AdminUserChats;
