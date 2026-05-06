import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { LogIn, UserPlus, UserCircle, Shield, ArrowRight, Loader2, Eye, EyeOff } from 'lucide-react';
import clsx from 'clsx';

const Login = () => {
    // Initial mode from localStorage or default to 'login'
    const [mode, setMode] = useState(localStorage.getItem('current_auth_mode') || 'login'); 
    const [loading, setLoading] = useState(false);
    const [showPassword, setShowPassword] = useState(false);
    const [error, setError] = useState('');
    const [formData, setFormData] = useState({
        email: '',
        username: '',
        password: '',
        displayName: ''
    });

    const { login } = useAuth();
    const navigate = useNavigate();

    // Persist mode changes to localStorage
    React.useEffect(() => {
        localStorage.setItem('current_auth_mode', mode);
    }, [mode]);

    // Check for mode requested from Navbar (override refresh persistence if needed)
    React.useEffect(() => {
        const requestedMode = localStorage.getItem('login_mode');
        if (requestedMode) {
            setMode(requestedMode);
            localStorage.removeItem('login_mode');
        }
    }, []);

    const handleInputChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
        setError('');
    };

    const validateForm = () => {
        // Email validation
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(formData.email)) {
            setError('Please enter a valid email address.');
            return false;
        }

        // Password validation
        if (formData.password.length < 6) {
            setError('Password must be at least 6 characters long.');
            return false;
        }

        // Sign Up specific validations
        if (mode === 'register') {
            if (!formData.displayName.trim()) {
                setError('Please enter your full name.');
                return false;
            }
        }

        return true;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        if (!validateForm()) return;

        setLoading(true);
        // Get the current guest session ID from ephemeral storage
        const guestSessionId = sessionStorage.getItem('guest_last_session');
        const endpoint = mode === 'login' ? 'login' : 'register';
        
        const body = {
            email: formData.email,
            password: formData.password,
            client_id: guestSessionId
        };

        if (mode === 'register') {
            // Backend requires a username, so we'll derive it from the email
            body.username = formData.email.split('@')[0];
            body.display_name = formData.displayName;
        }

        try {
            const response = await fetch(`http://localhost:8000/api/auth/${endpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });

            const data = await response.json();

            if (response.ok) {
                login(data.access_token, data.user);
                // Redirect based on role
                if (data.user.role === 'admin') {
                    navigate('/admin');
                } else {
                    navigate('/');
                }
            } else {
                setError(data.detail || 'Authentication failed');
            }
        } catch (err) {
            setError('Connection failed. Is the backend running?');
        } finally {
            setLoading(false);
        }
    };

    const handleGuestLogin = async () => {
        setLoading(true);
        try {
            const response = await fetch('http://localhost:8000/api/auth/guest', { method: 'POST' });
            const data = await response.json();
            if (response.ok) {
                login(data.access_token, data.user);
                // Guests always go to home/chat
                navigate('/');
            }
        } catch (err) {
            setError('Guest login failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-[calc(100vh-64px)] flex items-center justify-center p-4 bg-[#072042] relative overflow-hidden">
            {/* Background Decorations */}
            <div className="absolute top-[-10%] right-[-5%] w-[400px] h-[400px] bg-indigo-600/20 rounded-full blur-[120px]" />
            <div className="absolute bottom-[-10%] left-[-5%] w-[400px] h-[400px] bg-cyan-600/20 rounded-full blur-[120px]" />

            <div className="w-full max-w-md relative z-10">
                <div className="bg-white/10 backdrop-blur-xl border border-white/20 rounded-3xl shadow-2xl p-8">
                    {/* Header */}
                    <div className="text-center mb-8">
                        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-indigo-600/20 text-indigo-400 mb-4 border border-indigo-500/30">
                            {mode === 'login' ? <LogIn size={32} /> : <UserPlus size={32} />}
                        </div>
                        <h1 className="text-3xl font-bold text-white mb-2">
                            {mode === 'login' ? 'Welcome Back' : 'Create Account'}
                        </h1>
                        <p className="text-slate-400">
                            Join the next generation of crypto intelligence
                        </p>
                    </div>

                    {error && (
                        <div className="bg-rose-500/10 border border-rose-500/20 text-rose-400 p-3 rounded-xl text-sm mb-6 animate-shake">
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-5">
                        {mode === 'register' && (
                            <div>
                                <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 ml-1">
                                    Full Name
                                </label>
                                <input
                                    type="text"
                                    name="displayName"
                                    value={formData.displayName}
                                    onChange={handleInputChange}
                                    placeholder="Enter your full name"
                                    className="w-full bg-slate-900/50 border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-slate-600 focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/50 transition-all"
                                    required
                                />
                            </div>
                        )}

                        <div>
                            <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 ml-1">
                                Email Address
                            </label>
                            <input
                                type="email"
                                name="email"
                                value={formData.email}
                                onChange={handleInputChange}
                                placeholder="name@example.com"
                                className="w-full bg-slate-900/50 border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-slate-600 focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/50 transition-all"
                                required
                            />
                        </div>

                        <div>
                            <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 ml-1">
                                Password
                            </label>
                            <div className="relative">
                                <input
                                    type={showPassword ? "text" : "password"}
                                    name="password"
                                    value={formData.password}
                                    onChange={handleInputChange}
                                    placeholder="••••••••"
                                    className="w-full bg-slate-900/50 border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-slate-600 focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/50 transition-all pr-12"
                                    required
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 p-2 text-slate-500 hover:text-slate-300 transition-colors"
                                >
                                    {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                                </button>
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-3 rounded-xl shadow-lg shadow-indigo-600/30 transition-all flex items-center justify-center gap-2 group disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {loading ? <Loader2 className="animate-spin" /> : mode === 'login' ? 'Sign In' : 'Create Account'}
                            {!loading && <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />}
                        </button>
                    </form>

                    <div className="mt-6 text-center">
                        {mode === 'login' ? (
                            <p className="text-slate-400 text-sm">
                                Don't have an account?{' '}
                                <button
                                    onClick={() => setMode('register')}
                                    className="text-indigo-400 hover:text-indigo-300 font-bold hover:underline"
                                >
                                    Sign Up
                                </button>
                            </p>
                        ) : (
                            <p className="text-slate-400 text-sm">
                                Already have an account?{' '}
                                <button
                                    onClick={() => setMode('login')}
                                    className="text-indigo-400 hover:text-indigo-300 font-bold hover:underline"
                                >
                                    Sign In
                                </button>
                            </p>
                        )}
                    </div>

                    <div className="mt-8 pt-8 border-t border-white/10 flex flex-col gap-4">
                        <button
                            onClick={handleGuestLogin}
                            disabled={loading}
                            className="w-full bg-white/5 hover:bg-white/10 text-white font-semibold py-3 rounded-xl transition-all flex items-center justify-center gap-2 border border-white/5"
                        >
                            <UserCircle size={20} className="text-cyan-400" />
                            Continue as Guest
                        </button>

                        <p className="text-center text-xs text-slate-500">
                            By continuing, you agree to our <span className="text-slate-300 hover:underline cursor-pointer">Terms of Service</span>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Login;
