import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAdminAuth } from '../context/AdminAuthContext';
import { LogIn, Shield, ArrowRight, Loader2, Eye, EyeOff } from 'lucide-react';

const AdminLogin = () => {
    const [loading, setLoading] = useState(false);
    const [showPassword, setShowPassword] = useState(false);
    const [error, setError] = useState('');
    const [formData, setFormData] = useState({
        username: '',
        password: ''
    });

    const { login } = useAdminAuth();
    const navigate = useNavigate();

    const handleInputChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
        setError('');
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        const formDataPayload = new URLSearchParams();
        formDataPayload.append('username', formData.username);
        formDataPayload.append('password', formData.password);

        try {
            const response = await fetch(`http://localhost:8000/api/admin/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: formDataPayload
            });

            const data = await response.json();

            if (response.ok) {
                // Fetch admin info after login
                const meRes = await fetch('http://localhost:8000/api/admin/me', {
                    headers: { 'Authorization': `Bearer ${data.access_token}` }
                });
                const adminData = await meRes.json();
                login(data.access_token, adminData);
                navigate('/');
            } else {
                setError(data.detail || 'Invalid admin credentials');
            }
        } catch (err) {
            setError('Connection failed. Is the backend running?');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center p-4 bg-main-bg relative overflow-hidden">
            {/* Background Decorations */}
            <div className="absolute top-[-10%] right-[-5%] w-[400px] h-[400px] bg-primary-purple/5 rounded-full blur-[120px]" />
            <div className="absolute bottom-[-10%] left-[-5%] w-[400px] h-[400px] bg-primary-purple/5 rounded-full blur-[120px]" />

            <div className="w-full max-w-md relative z-10">
                <div className="bg-card-bg border border-card-border rounded-3xl shadow-[0_10px_30px_rgba(0,0,0,0.06)] p-8">
                    {/* Header */}
                    <div className="text-center mb-8">
                        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-light-purple text-primary-purple mb-4 border border-primary-purple/10">
                            <Shield size={32} />
                        </div>
                        <h1 className="text-3xl font-bold text-text-primary mb-2">
                            Admin Control
                        </h1>
                        <p className="text-[#6B7280]">
                            Secure access to CryptoBot ecosystem
                        </p>
                    </div>

                    {error && (
                        <div className="bg-rose-500/10 border border-rose-500/20 text-rose-400 p-3 rounded-xl text-sm mb-6 animate-shake">
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-6">
                        <div>
                            <label className="block text-xs font-bold text-black uppercase tracking-wider mb-2 ml-1">
                                Admin Username
                            </label>
                            <input
                                type="text"
                                name="username"
                                value={formData.username}
                                onChange={handleInputChange}
                                placeholder="Enter admin username"
                                className="w-full bg-white border border-border-light rounded-xl px-4 py-3 text-black placeholder:text-[#9CA3AF] focus:outline-none focus:border-primary-purple focus:ring-4 focus:ring-primary-purple/15 transition-all duration-200"
                                required
                            />
                        </div>

                        <div>
                            <label className="block text-xs font-bold text-black uppercase tracking-wider mb-2 ml-1">
                                Password
                            </label>
                            <div className="relative">
                                <input
                                    type={showPassword ? "text" : "password"}
                                    name="password"
                                    value={formData.password}
                                    onChange={handleInputChange}
                                    placeholder="••••••••"
                                    className="w-full bg-white border border-border-light rounded-xl px-4 py-3 text-black placeholder:text-[#9CA3AF] focus:outline-none focus:border-primary-purple focus:ring-4 focus:ring-primary-purple/15 transition-all duration-200 pr-12"
                                    required
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 p-2 text-text-muted hover:text-text-primary transition-colors"
                                >
                                    {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                                </button>
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full bg-primary-purple hover:bg-[#5558E8] text-white font-bold py-3 rounded-xl shadow-[0_4px_12px_rgba(99,102,241,0.25)] hover:translate-y-[-1px] transition-all duration-200 flex items-center justify-center gap-2 group disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {loading ? <Loader2 className="animate-spin" /> : 'Enter Dashboard'}
                            {!loading && <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />}
                        </button>
                    </form>

                    <div className="mt-8 pt-6 border-t border-border-light text-center">
                        <p className="text-[13px] text-[#9CA3AF]">
                            Authorized personnel only. Access is monitored and logged.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AdminLogin;
