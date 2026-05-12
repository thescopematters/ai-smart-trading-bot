import React, { useState, useEffect, useRef, useCallback } from "react";
import ChatHeader from "./ChatHeader";
import ChatMessages from "./ChatMessages";
import ChatInput from "./ChatInput";
import { useChatWebSocket } from "../../hooks/useChatWebSocket";
import { useAuth } from "../../context/AuthContext";
import {
  MessagesSquare,
  MessageCircle,
  RefreshCcw,
  History,
  Plus,
  ChevronLeft,
  X,
  MoreVertical,
  Trash2,
  Minimize2,
  Maximize2,
} from "lucide-react";
import cryptobotAvatar from "../../assets/cryptobot_avatar_cute_1.png";
import { useToast } from "../../context/ToastContext";
import ConfirmModal from "../../ui/ConfirmModal";
import { api } from "../../services/api";
import { useLoader } from '../../context/LoaderContext';

// ─── Helpers ────────────────────────────────────────────────────────────────

const getRelativeTime = (ts) => {
  if (!ts) return "";
  const diff = Date.now() - ts;
  const m = Math.floor(diff / 60000);
  const h = Math.floor(diff / 3600000);
  const d = Math.floor(diff / 86400000);
  if (m < 1) return "just now";
  if (m < 60) return `${m} min ago`;
  if (h < 24) return `${h} hr ago`;
  return `${d} day${d > 1 ? "s" : ""} ago`;
};

const stripMarkdown = (text = "") => {
  if (!text) return "";
  return text
    .replace(/[#*`_~]/g, "")
    .replace(/\[(.*?)\]\(.*?\)/g, "$1")
    .trim();
};

// ─── Unique session ID generator ────────────────────────────────────────────

const newSessionId = () =>
  `session-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;

// ─── Minimalist Ghost UI Skeletons ──────────────────────────────────────────

const HistorySkeleton = () => (
  <div className="flex flex-col gap-3 p-4">
    {[1, 2, 3, 4, 5].map((i) => (
      <div key={i} className="flex items-center gap-4 p-4 bg-white/60 border border-white/40 rounded-2xl animate-pulse">
        <div className="w-12 h-12 rounded-full bg-slate-100 shadow-inner" />
        <div className="flex-1 space-y-2">
          <div className="h-4 bg-indigo-500/10 rounded w-1/3" />
          <div className="h-3 bg-indigo-500/5 rounded w-2/3" />
        </div>
      </div>
    ))}
  </div>
);

const ChatSkeleton = () => (
  <div className="flex-1 flex flex-col p-6 space-y-8 animate-pulse overflow-hidden bg-slate-50/20">
    <div className="flex justify-start gap-3">
      <div className="w-8 h-8 rounded-full bg-slate-100 shrink-0" />
      <div className="h-20 bg-white rounded-2xl rounded-bl-none w-3/4 shadow-sm border border-slate-100" />
    </div>
    <div className="flex justify-end gap-3">
      <div className="h-12 bg-[#072042]/10 rounded-2xl rounded-br-none w-2/3 shadow-sm border border-[#072042]/10" />
    </div>
    <div className="flex justify-start gap-3">
      <div className="w-8 h-8 rounded-full bg-slate-100 shrink-0" />
      <div className="h-24 bg-white rounded-2xl rounded-bl-none w-4/5 shadow-sm border border-slate-100" />
    </div>
    <div className="flex justify-end gap-3">
      <div className="h-16 bg-[#072042]/10 rounded-2xl rounded-br-none w-1/2 shadow-sm border border-[#072042]/10" />
    </div>
  </div>
);

// ─── Main Component ──────────────────────────────────────────────────────────

const ChatbotPanel = ({ onClose, onMaximize, isMaximized }) => {
  const toast = useToast();
  const { setIsLoading } = useLoader();
  const [confirmModal, setConfirmModal] = useState({
    open: false,
    sessionId: null,
  });

  const { user, token, loading: authLoading } = useAuth();

  /**
   * userPrefix uniquely namespaces all storage keys per account.
   * 'guest' for unauthenticated users.
   * 'user_<id>' for logged-in users.
   */
  const userPrefix = user ? `user_${user.id}` : "guest";
  const isGuest = !user;

  // ── Session ID ──────────────────────────────────────────────────────────
  /**
   * GUEST:  No session ID (cannot chat).
   * USER:   Resumed from localStorage, or a new one created and saved.
   */
  const [activeSessionId, setActiveSessionId] = useState(() => {
    if (isGuest) return null;
    const saved = localStorage.getItem(`${userPrefix}_last_session`);
    if (saved) return saved;
    const id = newSessionId();
    localStorage.setItem(`${userPrefix}_last_session`, id);
    return id;
  });

  // ── View State ──────────────────────────────────────────────────────────
  const [showHistory, setShowHistory] = useState(
    () => localStorage.getItem("crypto_show_history") === "true",
  );
  const [sessions, setSessions] = useState([]);
  const [loadingSessions, setLoadingSessions] = useState(authLoading);
  const [defaultQuestions, setDefaultQuestions] = useState([]);
  const [menuOpenId, setMenuOpenId] = useState(null);

  // ── Click outside to close menu ─────────────────────────────────────────
  useEffect(() => {
    const handleClickOutside = () => {
      if (menuOpenId) setMenuOpenId(null);
    };
    document.addEventListener("click", handleClickOutside);
    return () => document.removeEventListener("click", handleClickOutside);
  }, [menuOpenId]);

  const prevUserIdRef = useRef(user?.id);

  // ── Handle login / logout → reset to correct session ───────────────────
  useEffect(() => {
    // Only trigger if both are present and different (actual account switch)
    const isActualAccountSwitch =
      user?.id && prevUserIdRef.current && prevUserIdRef.current !== user.id;

    if (isActualAccountSwitch) {
      setShowHistory(false);
      if (isGuest) {
        setActiveSessionId(newSessionId());
      } else {
        const saved = localStorage.getItem(`${userPrefix}_last_session`);
        if (saved) {
          setActiveSessionId(saved);
        } else {
          const id = newSessionId();
          localStorage.setItem(`${userPrefix}_last_session`, id);
          setActiveSessionId(id);
        }
      }
    }
    prevUserIdRef.current = user?.id;
  }, [user?.id, isGuest, userPrefix]);

  // ── Persist View State ──────────────────────────────────────────────────
  useEffect(() => {
    localStorage.setItem("crypto_show_history", showHistory ? "true" : "false");

    // Clear unread and update last viewed timestamp for active session if we are looking at it
    const clearUnread = () => {
      if (!showHistory && activeSessionId && !document.hidden) {
        localStorage.removeItem(
          `crypto_unread_${userPrefix}_${activeSessionId}`,
        );
        localStorage.setItem(
          `crypto_viewed_${userPrefix}_${activeSessionId}`,
          Date.now().toString(),
        );
        window.dispatchEvent(new Event("chat_history_updated"));
      }
    };

    clearUnread();
    window.addEventListener("visibilitychange", clearUnread);

    // Also continually update the viewed timestamp while active
    const interval = setInterval(clearUnread, 2000);

    return () => {
      window.removeEventListener("visibilitychange", clearUnread);
      clearInterval(interval);
    };
  }, [showHistory, activeSessionId, userPrefix]);

  // ── Persist active session ID for users (so refresh resumes correctly) ──
  useEffect(() => {
    if (!isGuest && activeSessionId) {
      localStorage.setItem(`${userPrefix}_last_session`, activeSessionId);
    }
  }, [activeSessionId, isGuest, userPrefix]);

  // ── WebSocket ───────────────────────────────────────────────────────────
  const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";
  const WS_BASE = API_BASE.replace(/^http/, "ws");
  const wsUrl = `${WS_BASE}/ws/chat`;

  const chatControls = useChatWebSocket(
    `${wsUrl}?token=${token || ""}`,
    activeSessionId,
    userPrefix,
    !showHistory,
  );
  const { messages } = chatControls;

  // ── Default questions ───────────────────────────────────────────────────
  const fetchDefaultQuestions = useCallback(async () => {
    try {
      const res = await api.get('/api/questions');
      if (res.ok) {
        const data = await res.json();
        setDefaultQuestions(data);
      }
    } catch {
      // silent fail
    }
  }, []);

  useEffect(() => {
    fetchDefaultQuestions();
    window.addEventListener("focus", fetchDefaultQuestions);
    const interval = setInterval(fetchDefaultQuestions, 30000); // 30s
    return () => {
      window.removeEventListener("focus", fetchDefaultQuestions);
      clearInterval(interval);
    };
  }, [fetchDefaultQuestions]);

  // ── Load session list ───────────────────────────────────────────────────
  /**
   * GUEST:  No sessions to show (they have no history).
   * USER:   Fetch from the secure /api/sessions endpoint.
   */
  const loadSessions = useCallback(async () => {
    if (isGuest) {
      setSessions([]);
      return;
    }

    setLoadingSessions(true);
    try {
      const res = await api.get("/api/sessions", token);
      if (!res.ok) return;
      const data = await res.json();
      setSessions(
        data.map((s) => {
          const viewedAt =
            parseInt(
              localStorage.getItem(`crypto_viewed_${userPrefix}_${s.id}`),
            ) || 0;
          // It is unread if the server's last message time is strictly newer than our last viewed time
          // OR if the websocket explicitly flagged it as unread.
          const isUnread =
            s.last_message_at > viewedAt ||
            localStorage.getItem(`crypto_unread_${userPrefix}_${s.id}`) ===
            "true";

          return {
            id: s.id,
            preview: stripMarkdown(s.preview) || "New Conversation",
            time: getRelativeTime(s.last_message_at),
            timestampRaw: s.last_message_at,
            isUnread: isUnread,
            isEnded: s.is_ended === true,
          };
        }),
      );
    } catch (err) {
      console.error("[Sessions] Failed to load:", err);
    } finally {
      setLoadingSessions(false);
    }
  }, [isGuest, token, userPrefix]);

  const handleDeleteSession = (e, sessionId) => {
    e.stopPropagation();
    setMenuOpenId(null);
    setConfirmModal({ open: true, sessionId });
  };

  const confirmDelete = async () => {
    const sessionId = confirmModal.sessionId;
    setConfirmModal({ open: false, sessionId: null });
    setIsLoading(true);
    try {
      const res = await api.delete(`/api/sessions/${sessionId}`, token);
      if (res.ok) {
        setSessions((prev) => prev.filter((s) => s.id !== sessionId));
        if (activeSessionId === sessionId) {
          setActiveSessionId(null);
          if (!isGuest) localStorage.removeItem(`${userPrefix}_last_session`);
        }
        toast({ type: "success", message: "Session deleted successfully." });
      } else {
        toast({ type: "error", message: "Failed to delete session." });
      }
    } catch {
      toast({ type: "error", message: "Something went wrong." });
    } finally {
        setIsLoading(false);
    }
  };

  useEffect(() => {
    loadSessions();
    window.addEventListener("chat_history_updated", loadSessions);
    return () =>
      window.removeEventListener("chat_history_updated", loadSessions);
  }, [loadSessions]);

  // ── Clear unread when actively viewing a session ────────────────────────
  useEffect(() => {
    if (!showHistory && activeSessionId && !isGuest) {
      localStorage.removeItem(`crypto_unread_${userPrefix}_${activeSessionId}`);
    }
  }, [showHistory, activeSessionId, isGuest, userPrefix]);

  // ── Actions ─────────────────────────────────────────────────────────────
  const startNewChat = () => {
    const id = newSessionId();
    setActiveSessionId(id);
    if (!isGuest) localStorage.setItem(`${userPrefix}_last_session`, id);
    setShowHistory(false);
  };

  const handleSelectSession = (id) => {
    setActiveSessionId(id);
    setShowHistory(false);
    if (!isGuest) localStorage.removeItem(`crypto_unread_${userPrefix}_${id}`);
  };

  // The "Back" button should appear once there is something to go back to:
  // either saved sessions OR the current chat already has messages beyond the greeting.
  const showHistoryBtn = sessions.length > 0 || messages.length > 1;

  // ── Render ───────────────────────────────────────────────────────────────
  return (
    <>
      <div className="flex flex-col w-full h-full backdrop-blur-md overflow-hidden relative">
        {isGuest ? (
          /* ── GUEST / LOGIN PROMPT ── */
          <div className="flex-1 flex flex-col items-center justify-center p-12 text-center bg-slate-50/40">
            <div className="w-20 h-20 bg-indigo-500/10 rounded-3xl flex items-center justify-center text-indigo-500 mb-6">
              <MessageCircle size={40} />
            </div>
            <h2 className="text-2xl font-bold text-slate-800 mb-3">
              Welcome to CryptoBot
            </h2>
            <p className="text-slate-500 mb-8 max-w-sm mx-auto leading-relaxed">
              Join our community to start chatting with the AI, track your
              portfolio, and explore real-time crypto analytics.
            </p>
            <div className="flex flex-col w-full max-w-xs gap-3">
              <button
                onClick={() => (window.location.href = "/login")}
                className="w-full bg-indigo-600 text-white py-4 rounded-2xl font-bold shadow-lg shadow-indigo-600/20 hover:bg-indigo-500 transition-all active:scale-95"
              >
                Log In to Chat
              </button>
              <button
                onClick={() => (window.location.href = "/register")}
                className="w-full bg-white border border-indigo-100 text-indigo-600 py-4 rounded-2xl font-bold hover:bg-indigo-50 transition-all active:scale-95"
              >
                Create Account
              </button>
            </div>
          </div>
        ) : showHistory ? (
          /* ── HISTORY LIST VIEW ── */
          <div className="flex flex-col w-full h-full bg-slate-50/40 backdrop-blur-md">
            {/* History List View header - find this section and update */}
            <div className="flex items-center justify-between p-4 sm:p-4 border-b border-slate-700 bg-[#072042]">
              <h2 className="text-xl font-bold text-white tracking-wide">
                Your Chats
              </h2>
              <div className="flex items-center gap-2">
                <button
                  onClick={startNewChat}
                  className="p-2 rounded-full hover:bg-white/10 transition text-white flex items-center justify-center"
                  title="New Chat"
                >
                  <MessagesSquare className="w-5 h-5" />
                </button>

                {/* Maximize button */}
                {onMaximize && (
                  <button
                    onClick={onMaximize}
                    className="p-2 rounded-full hover:bg-white/10 transition text-white flex items-center justify-center"
                    title={isMaximized ? "Minimize" : "Maximize"}
                  >
                    {isMaximized ? (
                      <Minimize2 className="w-4 h-4" />
                    ) : (
                      <Maximize2 className="w-4 h-4" />
                    )}
                  </button>
                )}
              </div>
            </div>

            <div className="flex-1 overflow-y-auto w-full custom-scrollbar p-2">
              {loadingSessions || authLoading ? (
                <HistorySkeleton />
              ) : sessions.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-slate-400 gap-4 p-8">
                  <MessageCircle className="w-16 h-16 text-slate-300" />
                  <p className="text-center font-medium">
                    No past conversations found.
                    <br />
                    Start a new chat to begin!
                  </p>
                </div>
              ) : (
                <div
                  className="flex flex-col gap-2 p-2"
                  onClick={() => setMenuOpenId(null)}
                >
                  {sessions.map((session) => (
                    <div
                      key={session.id}
                      onClick={() => handleSelectSession(session.id)}
                      className={`group flex items-center gap-3 sm:gap-4 p-3 sm:p-4 cursor-pointer bg-white/60 hover:bg-white border border-white/40 rounded-2xl shadow-sm hover:shadow-md transition-all relative ${session.isUnread ? "ring-1 ring-[#072042]/20 bg-[#072042]/5" : ""}`}
                    >
                      <div className="relative shrink-0">
                        <div className="w-12 h-12 rounded-full overflow-hidden shadow-inner bg-white border border-slate-100">
                          <img
                            src={cryptobotAvatar}
                            alt="CryptoBot"
                            className="w-full h-full object-cover"
                          />
                        </div>
                        {session.isUnread && (
                          <span className="absolute -top-0.5 -right-0.5 w-3.5 h-3.5 bg-[#072042] border-2 border-white rounded-full animate-pulse shadow-sm z-10" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex justify-between items-baseline mb-1">
                          <h3
                            className={`font-bold ${session.isUnread ? "text-[#072042]" : "text-slate-800"}`}
                          >
                            CryptoBot
                          </h3>
                          <div className="flex items-center gap-2">
                            <span
                              className={`text-[12px] ${session.isUnread ? "font-bold text-[#072042]" : "font-medium text-slate-600"}`}
                            >
                              {session.time}
                            </span>
                            {!isGuest && (
                              <div className="relative">
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setMenuOpenId(
                                      menuOpenId === session.id
                                        ? null
                                        : session.id,
                                    );
                                  }}
                                  className={`p-1 rounded-full transition-all ${menuOpenId === session.id
                                      ? "opacity-100 bg-slate-200 text-slate-600"
                                      : "hover:bg-slate-200 text-slate-400 opacity-100 sm:opacity-0 sm:group-hover:opacity-100"
                                  }`}
                                >
                                  <MoreVertical size={14} />
                                </button>
                                {menuOpenId === session.id && (
                                  <div className="absolute right-0 top-full mt-1 w-36 bg-white border border-slate-100 shadow-xl rounded-xl overflow-hidden z-20">
                                    <button
                                      onClick={(e) =>
                                        handleDeleteSession(e, session.id)
                                      }
                                      className="w-full text-left px-4 py-2 text-xs font-medium text-slate-700 hover:bg-slate-100 hover:text-[#072042] flex items-center gap-2 transition-colors"
                                    >
                                      <Trash2 size={12} /> Delete Session
                                    </button>
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                        <p
                          className={`text-sm truncate ${session.isUnread ? "text-slate-900 font-semibold" : "text-slate-600"}`}
                        >
                          {session.isEnded ? (
                            <span className="text-slate-900 font-semibold text-xs uppercase tracking-tight">
                              Chat has ended
                            </span>
                          ) : (
                            session.preview
                          )}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ) : (
          /* ── ACTIVE CHAT VIEW ── */
          <ActiveChat
            chatControls={chatControls}
            defaultQuestions={defaultQuestions}
            onOpenHistory={() => setShowHistory(true)}
            showHistoryBtn={showHistoryBtn}
            onNewChat={startNewChat}
            onClose={onClose}
            onMaximize={onMaximize}
            isMaximized={isMaximized}
          />
        )}
      </div>
      <ConfirmModal
        isOpen={confirmModal.open}
        title="Delete Session"
        message="Delete this session and all its messages? This cannot be undone."
        onConfirm={confirmDelete}
        onCancel={() => setConfirmModal({ open: false, sessionId: null })}
      />
    </>
  );
};

// ─── Active Chat Sub-Component ───────────────────────────────────────────────

const ActiveChat = ({
  chatControls,
  defaultQuestions,
  onOpenHistory,
  showHistoryBtn,
  onNewChat,
  onClose,
  onMaximize,
  isMaximized,
}) => {
  const {
    isConnected,
    messages,
    isTyping,
    isSessionEnd,
    currentTranscript,
    sendMessage,
    sendAudioChunk,
    sendTranscribeRequest,
    sendTypingIndicator,
  } = chatControls;

  return (
    <>
      <ChatHeader
        onClose={onClose}
        status={
          !isConnected ? "Connecting..." : isTyping ? "Processing..." : "Online"
        }
        onOpenHistory={onOpenHistory}
        showHistoryBtn={showHistoryBtn}
        onMaximize={onMaximize}
        isMaximized={isMaximized}
      />

      {!isConnected ? (
            <div className="flex-1 flex items-center justify-center bg-white">
                <div className="flex flex-col items-center gap-3">
                    <div className="w-10 h-10 rounded-full border-4 border-[#072042]/20 border-t-[#072042] animate-spin" />
                    <p className="text-sm text-slate-400 font-medium">Connecting...</p>
                </div>
            </div>
        ) : (
        <div className="flex-1 flex flex-col overflow-hidden">
          <ChatMessages messages={messages} isTyping={isTyping} />

          {isSessionEnd ? (
            <div className="p-3 text-center border-t border-slate-200 bg-white/80 backdrop-blur-sm animate-in fade-in slide-in-from-bottom-4 duration-500">
              <p className="text-slate-500 text-sm font-medium leading-relaxed">
                Session ended due to inactivity.
                <br />
                <button
                  onClick={onNewChat}
                  className="text-[#072042] hover:text-[#072042] font-bold hover:underline transition-all mt-1"
                >
                  Click here
                </button>
                <span className="text-slate-400">
                  {" "}
                  to start a new conversation.
                </span>
              </p>
            </div>
          ) : (
            <>
              {messages.length <= 1 && defaultQuestions.length > 0 && (
                <div className="px-3 sm:px-4 pb-2 grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {defaultQuestions.map((q, i) => (
                    <button
                      key={q.id || i}
                      onClick={() => sendMessage(q.text)}
                      className="text-left text-xs bg-white hover:bg-white/80 border border-white/60 hover:border-[#072042]/30 text-slate-600 hover:text-[#072042] p-4 rounded-xl transition-all duration-300 shadow-sm hover:shadow-md hover:-translate-y-0.5 animate-in fade-in zoom-in-95"
                      style={{ animationDelay: `${i * 100}ms` }}
                    >
                      {q.text}
                    </button>
                  ))}
                </div>
              )}

              <ChatInput
                onSendMessage={sendMessage}
                onAudioChunk={sendAudioChunk}
                onRecordingStop={sendTranscribeRequest}
                currentTranscript={currentTranscript}
                isTyping={isTyping}
                onTyping={sendTypingIndicator}
                isSessionEnd={isSessionEnd}
                onNewChat={onNewChat}
              />
            </>
          )}
        </div>
      )}
    </>
  );
};

export default ChatbotPanel;
