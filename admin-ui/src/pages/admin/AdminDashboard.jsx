import React, { useState, useEffect } from 'react';
import { 
    Users, 
    MessageSquare, 
    FileText, 
    Zap, 
    TrendingUp, 
    Clock,
    UserPlus,
    Activity
} from 'lucide-react';
import { useAdminAuth } from '../../context/AdminAuthContext';

const AdminDashboard = () => {
    const [stats, setStats] = useState({
        total_users: 0,
        total_sessions: 0,
        total_messages: 0,
        total_documents: 0
    });
    const [loading, setLoading] = useState(true);
    const { token } = useAdminAuth();

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const response = await fetch('http://localhost:8000/api/admin/stats', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (response.ok) {
                    const data = await response.json();
                    setStats(data);
                }
            } catch (error) {
                console.error("Failed to fetch stats:", error);
            } finally {
                setLoading(false);
            }
        };
        fetchStats();
    }, [token]);

    const statCards = [
        { label: 'Total Users', value: stats.total_users, icon: Users, color: 'bg-indigo-500', trend: '+12%' },
        { label: 'Chat Sessions', value: stats.total_sessions, icon: MessageSquare, color: 'bg-emerald-500', trend: '+5%' },
        { label: 'Total Messages', value: stats.total_messages, icon: Activity, color: 'bg-amber-500', trend: '+28%' },
        { label: 'Knowledge Docs', value: stats.total_documents, icon: FileText, color: 'bg-rose-500', trend: 'Stable' },
    ];

    if (loading) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="w-12 h-12 border-4 border-primary-purple border-t-transparent rounded-full animate-spin"></div>
            </div>
        );
    }

    return (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {statCards.map((stat, idx) => (
                    <div key={idx} className="bg-card-bg border border-card-border rounded-3xl p-6 hover:shadow-md transition-all group shadow-sm">
                        <div className="flex items-start justify-between mb-4">
                            <div className={`${stat.color} p-3 rounded-2xl text-white shadow-lg`}>
                                <stat.icon size={24} />
                            </div>
                            <span className="text-xs font-bold text-emerald-400 flex items-center gap-1">
                                <TrendingUp size={14} />
                                {stat.trend}
                            </span>
                        </div>
                        <h3 className="text-text-secondary text-sm font-medium mb-1">{stat.label}</h3>
                        <p className="text-3xl font-bold text-text-primary">{stat.value.toLocaleString()}</p>
                    </div>
                ))}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* System Status */}
                <div className="lg:col-span-2 bg-card-bg border border-card-border rounded-3xl p-8 shadow-sm">
                    <div className="flex items-center justify-between mb-8">
                        <div>
                            <h2 className="text-xl font-bold text-text-primary">System Performance</h2>
                            <p className="text-sm text-text-secondary">Real-time infrastructure monitoring</p>
                        </div>
                        <div className="flex items-center gap-2 px-4 py-1.5 bg-emerald-500 text-white rounded-full text-[10px] font-bold uppercase tracking-wider shadow-sm">
                            All Systems Operational
                        </div>
                    </div>

                    <div className="space-y-6">
                        {[
                            { label: 'API Latency', value: '124ms', percent: 12 },
                            { label: 'Vector DB Sync', value: '99.9%', percent: 99 },
                            { label: 'LLM Response Time', value: '1.2s', percent: 85 },
                        ].map((item, idx) => (
                            <div key={idx} className="space-y-2">
                                <div className="flex justify-between text-sm">
                                    <span className="text-text-secondary font-medium">{item.label}</span>
                                    <span className="text-text-primary font-bold">{item.value}</span>
                                </div>
                                <div className="h-2 bg-border-light rounded-full overflow-hidden">
                                    <div 
                                        className="h-full bg-primary-purple rounded-full" 
                                        style={{ width: `${item.percent}%` }}
                                    ></div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Quick Actions */}
                <div className="bg-card-bg border border-card-border rounded-3xl p-8 text-text-primary shadow-sm relative overflow-hidden group">
                    <Zap size={120} className="absolute -bottom-8 -right-8 text-primary-purple/5 group-hover:scale-110 transition-transform duration-700" />
                    
                    <h2 className="text-xl font-bold mb-2">Quick Actions</h2>
                    <p className="text-text-secondary text-sm mb-8">Common administrative tasks</p>
                    
                    <div className="space-y-4">
                        {[
                            { label: 'Create New Admin', icon: UserPlus },
                            { label: 'Upload Data', icon: FileText },
                            { label: 'View Logs', icon: Clock },
                        ].map((action, idx) => (
                            <button key={idx} className="w-full flex items-center gap-3 bg-sidebar-active/50 hover:bg-sidebar-active p-3 rounded-xl transition-all font-semibold text-sm border border-border-light text-text-primary">
                                <action.icon size={18} className="text-primary-purple" />
                                {action.label}
                            </button>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AdminDashboard;
