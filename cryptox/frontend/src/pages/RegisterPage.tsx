/* eslint-disable @typescript-eslint/no-explicit-any */
import { useState } from 'react';
import { authAPI } from '../services/api';
import { useExchangeStore } from '../store/useExchangeStore';

interface Props {
  onSwitch: () => void;
}

export default function RegisterPage({ onSwitch }: Props) {
  const setUser = useExchangeStore((s) => s.setUser);
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleRegister = async () => {
    setError('');
    setLoading(true);
    try {
      const res = await authAPI.register(email, username, password);
      setUser(res.data.user, res.data.token);
      localStorage.setItem('token', res.data.token);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-dark flex items-center justify-center">
      <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-8 w-full max-w-md">

        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold font-display"
            style={{ background: 'linear-gradient(135deg, #6366f1, #ec4899)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            CryptoX
          </h1>
          <p className="text-[#64748b] text-sm mt-1">Create your account</p>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/30 text-red-400 text-sm rounded-lg p-3 mb-4">
            {error}
          </div>
        )}

        <div className="mb-4">
          <label className="text-[#64748b] text-xs uppercase tracking-wider mb-1 block">Email</label>
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            className="w-full bg-[#0f172a] border border-[#334155] rounded-lg px-4 py-3 text-sm text-[#e2e8f0] outline-none focus:border-primary" />
        </div>

        <div className="mb-4">
          <label className="text-[#64748b] text-xs uppercase tracking-wider mb-1 block">Username</label>
          <input type="text" value={username} onChange={(e) => setUsername(e.target.value)}
            placeholder="satoshi"
            className="w-full bg-[#0f172a] border border-[#334155] rounded-lg px-4 py-3 text-sm text-[#e2e8f0] outline-none focus:border-primary" />
        </div>

        <div className="mb-6">
          <label className="text-[#64748b] text-xs uppercase tracking-wider mb-1 block">Password</label>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
            placeholder="min 6 characters"
            onKeyDown={(e) => e.key === 'Enter' && handleRegister()}
            className="w-full bg-[#0f172a] border border-[#334155] rounded-lg px-4 py-3 text-sm text-[#e2e8f0] outline-none focus:border-primary" />
        </div>

        {/* Dummy balance info */}
        <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-3 mb-4 text-xs text-green-400">
          🎁 You'll get: $50,000 USDT + 1 BTC + 10 ETH as starting balance
        </div>

        <button onClick={handleRegister} disabled={loading}
          className="w-full py-3 rounded-lg font-semibold text-white text-sm disabled:opacity-50"
          style={{ background: 'linear-gradient(135deg, #6366f1, #4f46e5)' }}>
          {loading ? 'Creating account...' : 'Create Account'}
        </button>

        <p className="text-center text-[#64748b] text-sm mt-4">
          Have an account?{' '}
          <button onClick={onSwitch} className="text-primary hover:underline">Sign in</button>
        </p>
      </div>
    </div>
  );
}