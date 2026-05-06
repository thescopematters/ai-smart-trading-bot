import React from 'react';
import { NavLink, Outlet, useNavigate, Navigate } from 'react-router-dom';
import { useAdminAuth } from '../../context/AdminAuthContext';
import { 
    LayoutDashboard, 
    Users, 
    FileText, 
    MessageSquare, 
    Settings, 
    LogOut, 
    ShieldCheck
} from 'lucide-react';
import clsx from 'clsx';

const AdminLayout = () => {
    const { admin, logout, loading } = useAdminAuth();
    const navigate = useNavigate();

    if (loading) {
        return (
            <div className="h-screen bg-main-bg flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-purple"></div>
            </div>
        );
    }

    if (!admin) {
        return <Navigate to="/login" replace />;
    }

    const navItems = [
        { icon: LayoutDashboard, label: 'Overview', path: '/' },
        { icon: Users, label: 'Users', path: '/users' },
        { icon: MessageSquare, label: 'Chats', path: '/chats' },
        { icon: FileText, label: 'Documents', path: '/documents' },
        { icon: Settings, label: 'Questions', path: '/questions' },
    ];

    return (
        <div className="flex h-screen bg-main-bg text-text-secondary">
            {/* Sidebar */}
            <aside className="w-64 bg-sidebar-bg border-r border-border-light flex flex-col">
                <div className="p-6 flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-primary-purple flex items-center justify-center text-white shadow-lg shadow-primary-purple/20">
                        <ShieldCheck size={24} />
                    </div>
                    <div>
                        <h2 className="font-bold text-text-primary text-lg leading-tight">Admin</h2>
                        <span className="text-[10px] uppercase tracking-widest text-primary-purple font-bold">Control Panel</span>
                    </div>
                </div>

                <nav className="flex-1 px-4 py-6 space-y-2">
                    {navItems.map((item) => (
                        <NavLink
                            key={item.path}
                            to={item.path}
                            end={item.path === '/'}
                            className={({ isActive }) => clsx(
                                "flex items-center gap-3 px-4 py-3 rounded-xl font-medium transition-all group",
                                isActive 
                                    ? "bg-sidebar-active text-text-primary shadow-sm" 
                                    : "text-text-secondary hover:bg-sidebar-active hover:text-text-primary"
                            )}
                        >
                            <item.icon size={20} className={clsx("transition-transform group-hover:scale-110")} />
                            {item.label}
                        </NavLink>
                    ))}
                </nav>

                <div className="p-4 border-t border-border-light bg-sidebar-active/30">
                    <div className="flex items-center gap-3 px-2 py-3 mb-2">
                        <div className="w-10 h-10 rounded-xl bg-primary-purple flex items-center justify-center text-white font-bold shadow-sm">
                            {admin.username?.substring(0, 1).toUpperCase() || 'A'}
                        </div>
                        <div className="flex-1 min-w-0">
                            <p className="text-sm font-bold text-text-primary truncate">{admin.display_name || admin.username}</p>
                            <p className="text-[10px] text-text-muted font-medium uppercase tracking-wider">Admin</p>
                        </div>
                    </div>
                    <button
                        onClick={() => {
                            logout();
                            navigate('/login');
                        }}
                        className="w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-rose-500 hover:bg-rose-50 transition-all text-xs font-bold uppercase tracking-wider"
                    >
                        <LogOut size={16} />
                        Logout
                    </button>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 flex flex-col overflow-hidden">
                <header className="h-20 bg-sidebar-bg border-b border-border-light flex items-center justify-between px-8">
                    <div className="flex items-center gap-4">
                        <h1 className="text-xl font-bold text-text-primary capitalize">
                            {window.location.pathname.split('/')[1] || 'Overview'}
                        </h1>
                    </div>

                    <div className="flex items-center gap-3">
                        <div className="px-3 py-1.5 bg-sidebar-active rounded-lg border border-border-light text-[10px] font-bold text-text-secondary uppercase tracking-widest">
                            Server: Online
                        </div>
                    </div>
                </header>

                <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
                    <Outlet />
                </div>
            </main>
        </div>
    );
};

export default AdminLayout;
