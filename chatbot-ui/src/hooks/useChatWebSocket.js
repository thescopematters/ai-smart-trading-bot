import { useState, useEffect, useRef, useCallback } from 'react';
import { playNotificationSound, showBrowserNotification, requestNotificationPermission } from '../utils/notifications';

// Returns formatted time like "03:38 PM"
export const formatMessageTime = () => {
    return new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true });
};

const DEFAULT_GREETING = { id: 'greeting', text: "Hello! I'm your crypto AI assistant. How can I help you today?", isUser: false, timestamp: formatMessageTime() };

/**
 * useChatWebSocket
 * 
 * Architecture:
 *  - GUEST (userPrefix === 'guest'):
 *      Messages are stored IN MEMORY only. Nothing is read from or written to any storage.
 *      Chat disappears on page refresh. Nothing is saved to the DB for guests.
 *
 *  - USER (userPrefix === 'user_XXX'):
 *      On WebSocket connect, the backend immediately sends a 'history' event with all DB messages.
 *      New messages are saved to the DB by the backend as they are sent.
 *      The frontend only reads/writes the session ID (not messages) to localStorage.
 *
 * @param {string} url - Base WebSocket URL (may include ?token=...)
 * @param {string} sessionId - The unique session/conversation ID
 * @param {string} userPrefix - 'guest' or 'user_<id>'
 * @param {boolean} isActive - Whether the user is actively viewing this chat (suppresses notifications if true)
 */
export const useChatWebSocket = (url, sessionId, userPrefix = 'guest', isActive = true) => {
    const isGuest = userPrefix === 'guest';

    const [isConnected, setIsConnected] = useState(false);
    const [messages, setMessages] = useState([DEFAULT_GREETING]);
    const [isTyping, setIsTyping] = useState(false);
    const [isSessionEnd, setIsSessionEnd] = useState(false);
    const [currentTranscript, setCurrentTranscript] = useState(undefined);

    const socketRef = useRef(null);
    const reconnectTimeoutRef = useRef(null);

    // When session or user changes, reset the UI to a clean state.
    // For users, the 'history' event from the server will populate messages.
    useEffect(() => {
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
            reconnectTimeoutRef.current = null;
        }
        setMessages([DEFAULT_GREETING]);
        setIsTyping(false);
        setIsSessionEnd(false);
    }, [sessionId, userPrefix]);

    const connect = useCallback(() => {
        if (!sessionId) return;
        if (socketRef.current?.readyState === WebSocket.OPEN || socketRef.current?.readyState === WebSocket.CONNECTING) return;

        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
            reconnectTimeoutRef.current = null;
        }

        // Build the WS URL: ws://localhost:8000/ws/chat?token=XXX → ws://localhost:8000/ws/chat/SESSION_ID?token=XXX
        const [baseWithPath, queryString] = url.split('?');
        const cleanBase = baseWithPath.replace(/\/user-session-1$/, '').replace(/\/$/, '');
        const wsUrl = queryString ? `${cleanBase}/${sessionId}?${queryString}` : `${cleanBase}/${sessionId}`;

        console.log('[WS] Connecting to:', wsUrl);
        const socket = new WebSocket(wsUrl);
        socketRef.current = socket;

        socket.onopen = () => {
            if (socketRef.current !== socket) { socket.close(); return; }
            console.log('[WS] Connected for session:', sessionId);
            setIsConnected(true);
        };

        socket.onclose = () => {
            setIsConnected(false);
            // Auto-reconnect only if this socket is still the current one
            if (socketRef.current === socket && sessionId) {
                reconnectTimeoutRef.current = setTimeout(() => connect(), 3000);
            }
        };

        socket.onerror = (err) => console.error('[WS] Error:', err);

        socket.onmessage = (event) => {
            if (socketRef.current !== socket) return;
            let data;
            try { data = JSON.parse(event.data); } catch { return; }

            switch (data.type) {

                // USER ONLY: Backend sends full chat history immediately on connect
                case 'history': {
                    if (!isGuest && data.messages?.length > 0) {
                        const mapped = data.messages.map(msg => ({
                            id: msg.id,
                            text: msg.content,
                            isUser: msg.role === 'user',
                            timestamp: new Date(msg.created_at).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true })
                        }));
                        setMessages(mapped);
                    }
                    break;
                }

                // Echo of user's text (voice or typed)
                case 'transcript': {
                    if (data.is_dictation) {
                        setCurrentTranscript(data.text);
                        setTimeout(() => setCurrentTranscript(undefined), 100);
                    } else {
                        setIsTyping(true);
                    }
                    break;
                }

                // Streaming bot response (partial chunks)
                case 'response.text_partial': {
                    setIsTyping(false);
                    setMessages(prev => {
                        const last = prev[prev.length - 1];
                        if (last && !last.isUser) {
                            return [...prev.slice(0, -1), { ...last, text: last.text + data.text }];
                        }
                        return [...prev, { id: Date.now(), text: data.text, isUser: false, timestamp: formatMessageTime() }];
                    });
                    break;
                }

                // Final bot response (replaces the last partial)
                case 'response.text': {
                    setMessages(prev => {
                        const last = prev[prev.length - 1];
                        if (last && !last.isUser) {
                            return [...prev.slice(0, -1), { ...last, text: data.text }];
                        }
                        return prev;
                    });
                    setIsTyping(false);
                    // Notify only when user is NOT actively looking at the chat
                    if (document.hidden || !isActive) {
                        playNotificationSound();
                        localStorage.setItem(`crypto_unread_${userPrefix}_${sessionId}`, 'true');
                        if (document.hidden) showBrowserNotification('New Message from CryptoBot', data.text);
                    }
                    window.dispatchEvent(new Event('chat_history_updated'));
                    break;
                }

                // A new, separate bot message (e.g. nudge/follow-up)
                case 'response.text_new': {
                    setMessages(prev => [...prev, { id: Date.now(), text: data.text, isUser: false, timestamp: formatMessageTime() }]);
                    setIsTyping(false);
                    if (document.hidden || !isActive) {
                        playNotificationSound();
                        localStorage.setItem(`crypto_unread_${userPrefix}_${sessionId}`, 'true');
                        if (document.hidden) showBrowserNotification('New Message from CryptoBot', data.text);
                    }
                    window.dispatchEvent(new Event('chat_history_updated'));
                    break;
                }

                case 'session.end': {
                    setIsSessionEnd(true);
                    setIsTyping(false);
                    break;
                }

                case 'error': {
                    setIsTyping(false);
                    setMessages(prev => [...prev, {
                        id: Date.now(), text: `⚠️ **Error:** ${data.message}`,
                        isUser: false, timestamp: formatMessageTime(), isError: true
                    }]);
                    break;
                }

                default: break;
            }
        };
    }, [url, sessionId, userPrefix, isGuest, isActive]);

    // Notify server of active state
    useEffect(() => {
        if (socketRef.current?.readyState === WebSocket.OPEN) {
            socketRef.current.send(JSON.stringify({ 
                type: 'visibility', 
                is_active: isActive && !document.hidden 
            }));
        }
    }, [isActive, isConnected]);

    // Connect (with a small debounce to handle React Strict Mode double-mount)
    useEffect(() => {
        const timeout = setTimeout(() => {
            connect();
            requestNotificationPermission();
        }, 100);

        return () => {
            clearTimeout(timeout);
            if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
            if (socketRef.current) {
                const s = socketRef.current;
                socketRef.current = null;
                s.close();
            }
        };
    }, [connect]);

    const sendMessage = (text) => {
        if (socketRef.current?.readyState === WebSocket.OPEN) {
            setMessages(prev => [...prev, { id: Date.now(), text, isUser: true, timestamp: formatMessageTime() }]);
            socketRef.current.send(JSON.stringify({ type: 'text_input', text }));
            setIsTyping(true);
            // Notify list that a new message was sent (for the "Back" button to appear)
            window.dispatchEvent(new Event('chat_history_updated'));
        } else {
            console.warn('[WS] Not connected, cannot send message.');
            connect();
        }
    };

    const sendAudioChunk = (blob) => {
        if (socketRef.current?.readyState === WebSocket.OPEN) socketRef.current.send(blob);
    };

    const sendTranscribeRequest = () => {
        if (socketRef.current?.readyState === WebSocket.OPEN)
            socketRef.current.send(JSON.stringify({ type: 'transcribe_request' }));
    };

    const sendTypingIndicator = () => {
        if (socketRef.current?.readyState === WebSocket.OPEN)
            socketRef.current.send(JSON.stringify({ type: 'user_typing' }));
    };

    return {
        isConnected,
        messages,
        setMessages,
        isTyping,
        isSessionEnd,
        currentTranscript,
        setCurrentTranscript,
        sendMessage,
        sendAudioChunk,
        sendTranscribeRequest,
        sendTypingIndicator,
    };
};