import React, { useState, useEffect } from 'react';
import { useAdminAuth } from '../../context/AdminAuthContext';
import { Users, Mail, User as UserIcon, Shield, Search, RefreshCcw, MoreHorizontal } from 'lucide-react';

const AdminUsers = () => {
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const { token } = useAdminAuth();

    const fetchUsers = async () => {
        setLoading(true);
        try {
            const response = await fetch('http://localhost:8000/api/admin/users', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                const data = await response.json();
                setUsers(data);
            }
        } catch (error) {
            console.error("Failed to fetch users:", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchUsers();
    }, [token]);

    const filteredUsers = users.filter(user => 
        (user.email?.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (user.username?.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (user.display_name?.toLowerCase().includes(searchQuery.toLowerCase()))
    );

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h2 className="text-2xl font-bold text-text-primary flex items-center gap-3">
                        <Users className="text-primary-purple" />
                        User Management
                    </h2>
                    <p className="text-text-secondary text-sm mt-1">Manage and monitor all registered accounts and guest sessions.</p>
                </div>
                
                <div className="flex items-center gap-3">
                    <button 
                        onClick={fetchUsers}
                        className="p-2.5 bg-card-bg border border-border-light rounded-xl text-text-secondary hover:text-text-primary hover:bg-sidebar-active transition-all"
                        title="Refresh List"
                    >
                        <RefreshCcw size={20} className={loading ? "animate-spin" : ""} />
                    </button>
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" size={18} />
                        <input 
                            type="text"
                            placeholder="Search users..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="bg-card-bg border border-border-light rounded-xl pl-10 pr-4 py-2.5 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-primary-purple/50 w-64 transition-all"
                        />
                    </div>
                </div>
            </div>

            <div className="bg-card-bg border border-card-border rounded-3xl overflow-hidden shadow-sm">
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="border-b border-border-light bg-sidebar-active/50">
                                <th className="px-6 py-4 text-xs font-bold text-text-muted uppercase tracking-widest">User Info</th>
                                <th className="px-6 py-4 text-xs font-bold text-text-muted uppercase tracking-widest">Username</th>
                                <th className="px-6 py-4 text-xs font-bold text-text-muted uppercase tracking-widest">Role</th>
                                <th className="px-6 py-4 text-xs font-bold text-text-muted uppercase tracking-widest">Status</th>
                                <th className="px-6 py-4 text-xs font-bold text-text-muted uppercase tracking-widest text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border-light">
                            {loading ? (
                                Array(5).fill(0).map((_, i) => (
                                    <tr key={i} className="animate-pulse">
                                        <td className="px-6 py-4"><div className="h-10 w-40 bg-sidebar-active/50 rounded-lg" /></td>
                                        <td className="px-6 py-4"><div className="h-5 w-24 bg-sidebar-active/50 rounded-lg" /></td>
                                        <td className="px-6 py-4"><div className="h-6 w-16 bg-sidebar-active/50 rounded-full" /></td>
                                        <td className="px-6 py-4"><div className="h-6 w-20 bg-sidebar-active/50 rounded-full" /></td>
                                        <td className="px-6 py-4"><div className="h-8 w-8 bg-sidebar-active/50 rounded-lg ml-auto" /></td>
                                    </tr>
                                ))
                            ) : filteredUsers.length === 0 ? (
                                <tr>
                                    <td colSpan="5" className="px-6 py-20 text-center text-slate-500 font-medium">
                                        No users found matching your search.
                                    </td>
                                </tr>
                            ) : (
                                filteredUsers.map((user) => (
                                    <tr key={user.id} className="hover:bg-sidebar-active/30 transition-colors group">
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-3">
                                                <div className="w-10 h-10 rounded-full bg-light-purple text-primary-purple flex items-center justify-center font-bold border border-primary-purple/10">
                                                    {(user.display_name || user.username || '?')[0].toUpperCase()}
                                                </div>
                                                <div>
                                                    <div className="text-text-primary font-bold text-sm">{user.display_name || 'N/A'}</div>
                                                    <div className="text-text-muted text-xs flex items-center gap-1">
                                                        <Mail size={12} />
                                                        {user.email || 'No email'}
                                                    </div>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-sm text-text-secondary font-medium">
                                            @{user.username}
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                                                user.role === 'admin' 
                                                ? 'bg-primary-purple text-white shadow-sm' 
                                                : 'bg-gray-400 text-white shadow-sm'
                                            }`}>
                                                {user.role === 'admin' && <Shield size={10} />}
                                                {user.role}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                                                user.is_guest 
                                                ? 'bg-amber-500 text-white shadow-sm' 
                                                : 'bg-emerald-500 text-white shadow-sm'
                                            }`}>
                                                {user.is_guest ? 'Guest' : 'Registered'}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            <button className="p-2 text-text-muted hover:text-text-primary hover:bg-sidebar-active rounded-lg transition-all">
                                                <MoreHorizontal size={18} />
                                            </button>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default AdminUsers;
