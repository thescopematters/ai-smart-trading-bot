/* eslint-disable @typescript-eslint/no-explicit-any */
import { useState } from 'react';
import { authAPI } from '../services/api';
import { useExchangeStore } from '../store/useExchangeStore';

interface Props {
  onSwitch: () => void; // switch to register
}

export default function LoginPage({ onSwitch }: Props) {
  const setUser = useExchangeStore((s) => s.setUser);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    setError('');
    setLoading(true);
    try {
      const res = await authAPI.login(email, password);
      setUser(res.data.user, res.data.token);
      localStorage.setItem('token', res.data.token);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-dark flex items-center justify-center">
      <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-8 w-full max-w-md">

        {/* Logo */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold font-display"
            style={{ background: 'linear-gradient(135deg, #6366f1, #ec4899)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            CryptoX
          </h1>
          <p className="text-[#64748b] text-sm mt-1">Sign in to your account</p>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/30 text-red-400 text-sm rounded-lg p-3 mb-4">
            {error}
          </div>
        )}

        {/* Email */}
        <div className="mb-4">
          <label className="text-[#64748b] text-xs uppercase tracking-wider mb-1 block">Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            className="w-full bg-[#0f172a] border border-[#334155] rounded-lg px-4 py-3 text-sm text-[#e2e8f0] outline-none focus:border-primary"
          />
        </div>

        {/* Password */}
        <div className="mb-6">
          <label className="text-[#64748b] text-xs uppercase tracking-wider mb-1 block">Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••"
            onKeyDown={(e) => e.key === 'Enter' && handleLogin()}
            className="w-full bg-[#0f172a] border border-[#334155] rounded-lg px-4 py-3 text-sm text-[#e2e8f0] outline-none focus:border-primary"
          />
        </div>

        {/* Button */}
        <button
          onClick={handleLogin}
          disabled={loading}
          className="w-full py-3 rounded-lg font-semibold text-white text-sm disabled:opacity-50"
          style={{ background: 'linear-gradient(135deg, #6366f1, #4f46e5)' }}
        >
          {loading ? 'Signing in...' : 'Sign In'}
        </button>

        {/* Switch */}
        <p className="text-center text-[#64748b] text-sm mt-4">
          No account?{' '}
          <button onClick={onSwitch} className="text-primary hover:underline">
            Register here
          </button>
        </p>
      </div>
    </div>
  );
}