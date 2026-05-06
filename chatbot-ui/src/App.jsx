import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import ChatbotPanel from './components/chatbot/ChatbotPanel';
import ErrorBoundary from './components/ErrorBoundary';
import Login from './pages/Login';
import { AuthProvider, useAuth } from './context/AuthContext';

const Home = () => {
  return (
    <div className="h-[100dvh] w-screen bg-slate-50 text-slate-800 selection:bg-violet-200 selection:text-violet-900 overflow-hidden flex flex-col relative">
      <Navbar />
      


      <div className="flex-1 w-full flex items-center justify-center p-0 md:p-4 overflow-hidden">
        <div className="w-full h-full md:max-w-5xl md:h-[85vh] z-10">
            <ChatbotPanel />
        </div>
      </div>
    </div>
  );
};

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="min-h-screen bg-slate-900 flex flex-col selection:bg-indigo-500/30">
          <ErrorBoundary>
            <Routes>
              {/* Public Routes */}
              <Route path="/login" element={<Login />} />
              
              <Route path="/" element={<Home />} />

              {/* Fallback */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </ErrorBoundary>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;