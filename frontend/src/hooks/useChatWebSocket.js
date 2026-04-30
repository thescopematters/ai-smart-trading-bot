import { useState, useEffect, useRef, useCallback } from 'react';

// Returns formatted time like "03:38 PM"
export const formatMessageTime = () => {
    return new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true });
};

export const useChatWebSocket = (url, sessionId) => {
    const [isConnected, setIsConnected] = useState(false);
    
    // Load initial messages from localStorage if they exist for this session
    const [messages, setMessages] = useState(() => {
        if (!sessionId) return [];
        const saved = localStorage.getItem(`crypto_chat_${sessionId}`);
        if (saved) {
            try {
                return JSON.parse(saved);
            } catch (e) {
                console.error("Failed to parse cached messages", e);
                return [];
            }
        }
        return [];
    });

    const [isTyping, setIsTyping] = useState(false);
    const [currentTranscript, setCurrentTranscript] = useState(undefined);

    const socketRef = useRef(null);
    const reconnectTimeoutRef = useRef(null);

    // Sync state when sessionId changes (for New Chat / Switching)
    useEffect(() => {
        // Clear any pending reconnects when session changes
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
            reconnectTimeoutRef.current = null;
        }
        
        if (!sessionId) {
            setMessages([]);
            return;
        }
        
        const saved = localStorage.getItem(`crypto_chat_${sessionId}`);
        if (saved) {
            try {
                setMessages(JSON.parse(saved));
            } catch (e) {
                setMessages([]);
            }
        } else {
            setMessages([]);
        }
        setIsTyping(false);
    }, [sessionId]);

    // Save messages to localStorage whenever they change
    useEffect(() => {
        if (sessionId && messages.length > 0) {
            localStorage.setItem(`crypto_chat_${sessionId}`, JSON.stringify(messages));
            // Trigger an event so the Conversation List can update instantly
            window.dispatchEvent(new Event('chat_history_updated'));
        }
    }, [messages, sessionId]);

    const connect = useCallback(() => {
        if (!sessionId) return; 
        if (socketRef.current?.readyState === WebSocket.OPEN || socketRef.current?.readyState === WebSocket.CONNECTING) return;

        // Clear existing timeout if manually connecting
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
            reconnectTimeoutRef.current = null;
        }

        const baseUrl = url.replace(/\/user-session-1$/, '').replace(/\/$/, '');
        const wsUrl = `${baseUrl}/${sessionId}`; 
        
        console.log('Connecting to WebSocket:', wsUrl);
        const socket = new WebSocket(wsUrl);
        socketRef.current = socket;

        socket.onopen = () => {
            if (socketRef.current !== socket) {
                socket.close();
                return;
            }
            console.log('WebSocket connected for', sessionId);
            setIsConnected(true);
        };

        socket.onclose = () => {
            setIsConnected(false);
            // Only reconnect if this is still the active socket and we have a session
            if (socketRef.current === socket && sessionId) {
                console.log('WebSocket closed, reconnecting in 3s...');
                reconnectTimeoutRef.current = setTimeout(() => connect(), 3000);
            }
        };

        socket.onmessage = async (event) => {
            if (socketRef.current !== socket) return;
            const data = JSON.parse(event.data);
            
            if (data.type === 'transcript') {
                if (data.is_dictation) {
                    setCurrentTranscript(data.text);
                    setTimeout(() => setCurrentTranscript(undefined), 100);
                } else {
                    setIsTyping(true);
                }
            } else if (data.type === 'response.text_partial') {
                setIsTyping(false);
                setMessages(prev => {
                    const last = prev[prev.length - 1];
                    if (last && !last.isUser) {
                        return [...prev.slice(0, -1), { ...last, text: last.text + data.text }];
                    }
                    return [...prev, { id: Date.now(), text: data.text, isUser: false, timestamp: formatMessageTime() }];
                });
            } else if (data.type === 'response.text') {
                setMessages(prev => {
                    const last = prev[prev.length - 1];
                    if (last && !last.isUser) {
                        return [...prev.slice(0, -1), { ...last, text: data.text }];
                    }
                    return prev;
                });
                setIsTyping(false);
            } else if (data.type === 'error') {
                console.error('Server error:', data.message);
                setIsTyping(false);
                setMessages(prev => [
                    ...prev, 
                    { 
                        id: Date.now(), 
                        text: `⚠️ **System Error:** ${data.message}`, 
                        isUser: false, 
                        timestamp: formatMessageTime(),
                        isError: true 
                    }
                ]);
            }
        };

        socket.onerror = (err) => {
            console.error('WebSocket error:', err);
        };
    }, [url, sessionId]);

    const sendMessage = (text) => {
        if (socketRef.current?.readyState === WebSocket.OPEN) {
            setMessages(prev => [...prev, { id: Date.now(), text, isUser: true, timestamp: formatMessageTime() }]);
            socketRef.current.send(JSON.stringify({ type: 'text_input', text }));
            setIsTyping(true);
        } else {
            alert('Not connected. Please wait a moment and try again.');
            if (!isConnected) connect();
        }
    };

    const sendAudioChunk = (blob) => {
        if (socketRef.current?.readyState === WebSocket.OPEN) {
            socketRef.current.send(blob);
        }
    };

    const sendTranscribeRequest = () => {
        if (socketRef.current?.readyState === WebSocket.OPEN) {
            socketRef.current.send(JSON.stringify({ type: 'transcribe_request' }));
        }
    };

    useEffect(() => {
        // Debounce the connection to handle React Strict Mode's double-mount 
        // and rapid session switching.
        const timeout = setTimeout(() => {
            connect();
        }, 100);

        return () => {
            clearTimeout(timeout);
            // Cleanup: stop reconnects and close socket
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current);
            }
            if (socketRef.current) {
                const socket = socketRef.current;
                socketRef.current = null; // Prevent onclose from triggering reconnect
                socket.close();
            }
        };
    }, [connect, sessionId]);

    return {
        isConnected,
        messages,
        setMessages,
        isTyping,
        sendMessage,
        sendAudioChunk,
        sendTranscribeRequest,
        currentTranscript,
        setCurrentTranscript
    };
};