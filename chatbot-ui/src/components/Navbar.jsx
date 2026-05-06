import React, { useState } from 'react';
import { Menu, X, LogIn, LogOut, Shield, UserPlus } from 'lucide-react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import tsmLogo from '../assets/tsm-logo-new.webp';

const Navbar = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [isProfileOpen, setIsProfileOpen] = useState(false);
    const navigate = useNavigate();
    const { user, logout } = useAuth();

    // Close profile dropdown when clicking outside
    React.useEffect(() => {
        const handleClickOutside = () => setIsProfileOpen(false);
        if (isProfileOpen) {
            window.addEventListener('click', handleClickOutside);
        }
        return () => window.removeEventListener('click', handleClickOutside);
    }, [isProfileOpen]);

    return (
        <nav className="bg-[#072042] text-white shadow-md sticky top-0 z-50 border-b border-white/5">
            <div className="w-full px-4 sm:px-6 lg:px-12">
                <div className="flex justify-between h-16 items-center">
                    <div className="flex-shrink-0 flex items-center">
                        <Link to="/" className="cursor-pointer flex items-center gap-2">
                            <img src={tsmLogo} alt="TSM" className="h-10 w-auto" />
                        </Link>
                    </div>

                    <div className="hidden md:flex items-center space-x-6">
                        {/* Removed redundant Chat link */}

                        
                        {user && user.role === 'admin' && (
                            <Link
                                to="/admin"
                                className="flex items-center gap-2 text-indigo-400 hover:text-indigo-300 px-3 py-2 rounded-md text-sm font-bold transition-all"
                            >
                                <Shield size={16} />
                                Dashboard
                            </Link>
                        )}

                        {user && !user.is_guest ? (
                            <div className="relative">
                                <button
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        setIsProfileOpen(!isProfileOpen);
                                    }}
                                    className="flex items-center gap-3 hover:opacity-80 transition-all p-1"
                                >
                                    <span className="text-sm font-bold text-gray-200 hidden lg:block">
                                        {user.display_name || user.username}
                                    </span>
                                    <div className="w-9 h-9 rounded-full bg-indigo-500 flex items-center justify-center text-xs font-bold shadow-lg uppercase text-white">
                                        {user.username?.substring(0, 1) || 'U'}
                                    </div>
                                </button>

                                {isProfileOpen && (
                                    <div className="absolute right-0 mt-2 w-72 bg-white border border-slate-200 rounded-2xl shadow-2xl overflow-hidden z-[60] animate-in fade-in zoom-in-95 duration-200">
                                        <div className="p-4 border-b border-slate-100 bg-slate-50">
                                            <p className="text-xs font-bold text-slate-800 break-all">{user.email || user.username}</p>
                                        </div>
                                        <div className="p-2">
                                            <button
                                                onClick={() => {
                                                    logout();
                                                    navigate('/');
                                                }}
                                                className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-rose-500 hover:bg-rose-50 transition-all text-xs font-bold uppercase tracking-wider"
                                            >
                                                <LogOut size={16} />
                                                Logout
                                            </button>
                                        </div>
                                    </div>
                                )}
                            </div>
                        ) : (
                            <Link
                                to="/login"
                                className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white px-5 py-2 rounded-xl text-sm font-bold transition-all shadow-lg shadow-indigo-600/20"
                            >
                                <LogIn size={16} />
                                Login
                            </Link>
                        )}
                    </div>

                    <div className="md:hidden flex items-center">
                        <button
                            onClick={() => setIsOpen(!isOpen)}
                            className="text-gray-300 hover:text-white focus:outline-none p-2 rounded-lg hover:bg-white/5"
                        >
                            {isOpen ? <X size={24} /> : <Menu size={24} />}
                        </button>
                    </div>
                </div>
            </div>

            {/* Mobile menu */}
            {isOpen && (
                <div className="md:hidden bg-[#072042] border-t border-white/5 p-4 space-y-4">
                    {/* Mobile Chat link removed */}

                    
                    {user && user.role === 'admin' && (
                        <Link
                            to="/admin"
                            onClick={() => setIsOpen(false)}
                            className="block text-indigo-400 hover:text-indigo-300 px-3 py-2 rounded-md text-base font-bold"
                        >
                            Admin Dashboard
                        </Link>
                    )}

                    {user && !user.is_guest ? (
                        <div className="space-y-4">
                            <div className="flex items-center gap-3 p-4 bg-white/5 rounded-2xl border border-white/10">
                                <div className="w-10 h-10 rounded-full bg-indigo-500 flex items-center justify-center font-bold shadow-lg shadow-indigo-500/20">
                                    {user.username?.substring(0, 1).toUpperCase() || 'U'}
                                </div>
                                <div>
                                    <p className="text-sm font-bold text-white">{user.display_name || user.username}</p>
                                    <p className="text-xs text-gray-400 break-all">{user.email}</p>
                                </div>
                            </div>
                            <button
                                onClick={() => {
                                    logout();
                                    setIsOpen(false);
                                    navigate('/');
                                }}
                                className="w-full flex items-center justify-center gap-2 bg-rose-500/10 text-rose-400 py-3 rounded-xl font-bold"
                            >
                                <LogOut size={18} />
                                Logout
                            </button>
                        </div>
                    ) : (
                        <Link
                            to="/login"
                            onClick={() => setIsOpen(false)}
                            className="flex items-center justify-center gap-2 bg-indigo-600 text-white py-3 rounded-xl font-bold shadow-lg"
                        >
                            <LogIn size={18} />
                            Login
                        </Link>
                    )}
                </div>
            )}
        </nav>
    );
};

export default Navbar;
