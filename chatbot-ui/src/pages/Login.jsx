/* eslint-disable no-unused-vars */
import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { LogIn, UserPlus, UserCircle, Shield, ArrowRight, Loader2, Eye, EyeOff } from 'lucide-react';
import clsx from 'clsx';
import { api } from '../services/api';

const Login = () => {
    const [loading, setLoading] = useState(false);
    const [showPassword, setShowPassword] = useState(false);
    const [error, setError] = useState('');
    const [formData, setFormData] = useState({
        email: '',
        password: ''
    });

    const { login } = useAuth();
    const navigate = useNavigate();

    const handleInputChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
        setError('');
    };

    const validateForm = () => {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(formData.email)) {
            setError('Please enter a valid email address.');
            return false;
        }

        if (formData.password.length < 6) {
            setError('Password must be at least 6 characters long.');
            return false;
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
        
        const body = {
            email: formData.email,
            password: formData.password,
            client_id: guestSessionId
        };

        try {
            const response = await api.post('/api/auth/login', body);
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

    return (
        <div className="min-h-screen flex items-center justify-center p-4 bg-[#F5F6F8] relative overflow-hidden">
            {/* Background Decorations */}
            <div className="absolute top-[-10%] right-[-5%] w-[400px] h-[400px] bg-indigo-600/5 rounded-full blur-[120px]" />
            <div className="absolute bottom-[-10%] left-[-5%] w-[400px] h-[400px] bg-indigo-600/5 rounded-full blur-[120px]" />

            <div className="w-full max-w-md relative z-10">
                <div className="bg-white border border-[#ECEFF3] rounded-3xl shadow-[0_10px_30px_rgba(0,0,0,0.06)] p-8">
                    {/* Header */}
                    <div className="text-center mb-8">
                        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-indigo-50 text-indigo-600 mb-4 border border-indigo-100">
                            <LogIn size={32} />
                        </div>
                        <h1 className="text-3xl font-bold text-[#111827] mb-2">
                            Welcome Back
                        </h1>
                        <p className="text-[#6B7280]">
                            Join the next generation of crypto intelligence
                        </p>
                    </div>

                    {error && (
                        <div className="bg-rose-500/10 border border-rose-500/20 text-rose-600 p-3 rounded-xl text-sm mb-6 animate-shake text-center">
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-5">
                        <div>
                            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2 ml-1">
                                Email Address
                            </label>
                            <input
                                type="email"
                                name="email"
                                value={formData.email}
                                onChange={handleInputChange}
                                placeholder="name@example.com"
                                className="w-full bg-white border border-[#E5E7EB] rounded-xl px-4 py-3 text-black placeholder:text-[#9CA3AF] focus:outline-none focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/15 transition-all duration-200"
                                required
                            />
                        </div>

                        <div>
                            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2 ml-1">
                                Password
                            </label>
                            <div className="relative">
                                <input
                                    type={showPassword ? "text" : "password"}
                                    name="password"
                                    value={formData.password}
                                    onChange={handleInputChange}
                                    placeholder="••••••••"
                                    className="w-full bg-white border border-[#E5E7EB] rounded-xl px-4 py-3 text-black placeholder:text-[#9CA3AF] focus:outline-none focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/15 transition-all duration-200 pr-12"
                                    required
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 p-2 text-slate-400 hover:text-slate-600 transition-colors"
                                >
                                    {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                                </button>
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-3 rounded-xl shadow-[0_4px_12px_rgba(99,102,241,0.25)] hover:translate-y-[-1px] transition-all duration-200 flex items-center justify-center gap-2 group disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {loading ? <Loader2 className="animate-spin" /> : 'Sign In'}
                            {!loading && <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />}
                        </button>
                    </form>

                    <div className="mt-8 pt-6 border-t border-[#E5E7EB]">
                        <p className="text-center text-xs text-[#9CA3AF]">
                            By continuing, you agree to our <span className="text-indigo-600 hover:underline cursor-pointer">Terms of Service</span>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Login;
