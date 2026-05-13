import { useEffect, useState } from 'react';
import { useExchangeStore } from './store/useExchangeStore';
import { usersAPI } from './services/api';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import TradingPage from './pages/TradingPage';

export default function App() {
  const { token, setUser, logout } = useExchangeStore();
  const [checking, setChecking] = useState(true);
  const [showRegister, setShowRegister] = useState(false);

  // On every page load → ask backend if cookie is valid
  useEffect(() => {
    const verify = async () => {
      try {
        const res = await usersAPI.getMe();
        // Cookie is valid → restore user in memory store
        setUser(res.data, 'cookie-managed');
      } catch {
        // Cookie missing or expired → force logout
        logout();
      } finally {
        setChecking(false);
      }
    };
    verify();
  }, []);

  // Show loading spinner while checking
  if (checking) {
    return (
      <div className="min-h-screen bg-dark flex items-center justify-center">
        <div style={{ color: '#6366f1', fontSize: '14px' }}>
          Verifying session...
        </div>
      </div>
    );
  }

  if (token) return <TradingPage />;
  if (showRegister) return <RegisterPage onSwitch={() => setShowRegister(false)} />;
  return <LoginPage onSwitch={() => setShowRegister(true)} />;
}