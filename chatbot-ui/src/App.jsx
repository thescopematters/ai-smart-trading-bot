import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import ChatWidget from './components/chatbot/ChatWidget';
import ErrorBoundary from './components/ErrorBoundary';
import Login from './pages/Login';
import { AuthProvider, useAuth } from './context/AuthContext';

const Home = () => {
    return (
        <div className="h-[100dvh] w-screen bg-slate-50 overflow-hidden flex flex-col">
            <Navbar />
            <div className="flex-1 flex items-center justify-center px-4">
                <div className="text-center space-y-4">
                    <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold text-slate-800 whitespace-nowrap">
                        Welcome to TSM CryptoBot
                    </h1>
                    <p className="text-slate-500 text-sm sm:text-base max-w-md mx-auto leading-relaxed">
                        Your AI-powered crypto assistant. Get real-time prices, 
                        portfolio insights, and market analysis.
                    </p>
                    <p className="text-[#072042] text-xs sm:text-sm font-medium animate-pulse">
                        💬 Click the chat bubble to get started →
                    </p>
                </div>
            </div>
        </div>
    );
};

const AppContent = () => {
    const { user } = useAuth();
    const showChat = user && !user.is_guest;

    return (
        <div className="min-h-screen bg-slate-900 flex flex-col">
            <ErrorBoundary>
                <Routes>
                    <Route path="/login" element={<Login />} />
                    <Route path="/" element={<Home />} />
                    <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
                {/* Floating chat widget - only for logged in users */}
                {showChat && <ChatWidget />}
            </ErrorBoundary>
        </div>
    );
};

function App() {
    return (
        <AuthProvider>
            <Router>
                <AppContent />
            </Router>
        </AuthProvider>
    );
}

export default App;