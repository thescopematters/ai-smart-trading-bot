import React, { useState, useEffect } from "react";
import {
  Users,
  MessageSquare,
  FileText,
  Zap,
  TrendingUp,
  Clock,
  UserPlus,
  Activity,
  Eye,
  EyeOff,
  RefreshCcw,
} from "lucide-react";
import { useAdminAuth } from "../../context/AdminAuthContext";
import { useToast } from "../../context/ToastContext";
import { api } from '../../services/api';

const AdminDashboard = () => {
  const toast = useToast();
  const [stats, setStats] = useState({
    total_users: 0,
    total_sessions: 0,
    total_messages: 0,
    total_documents: 0,
    performance: {
      api_latency: "---",
      api_percent: 5,
      vector_sync: "---",
      vector_percent: 0,
      llm_response: "---",
      llm_percent: 5
    }
  });
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    username: "",
    password: "",
    display_name: "",
  });
  const { token } = useAdminAuth();

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await api.get('/api/admin/stats', token);
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

  const handleCreateAdmin = async (e) => {
    e.preventDefault();
    setCreating(true);
    try {
      const response = await api.post('/api/admin/create', formData, token);
      const result = await response.json();
      if (response.ok) {
        toast({ type: "success", message: "Admin created successfully!" });
        setIsModalOpen(false);
        setFormData({ username: "", password: "", display_name: "" });
      } else {
        toast({
          type: "error",
          message: result.detail || "Failed to create admin",
        });
      }
    } catch (error) {
      toast({ type: "error", message: "Error: " + error.message });
    } finally {
      setCreating(false);
    }
  };

  const statCards = [
    {
      label: "Total Users",
      value: stats.total_users,
      icon: Users,
      color: "bg-indigo-500",
      trend: "+12%",
    },
    {
      label: "Chat Sessions",
      value: stats.total_sessions,
      icon: MessageSquare,
      color: "bg-emerald-500",
      trend: "+5%",
    },
    {
      label: "Total Messages",
      value: stats.total_messages,
      icon: Activity,
      color: "bg-amber-500",
      trend: "+28%",
    },
    {
      label: "Knowledge Docs",
      value: stats.total_documents,
      icon: FileText,
      color: "bg-rose-500",
      trend: "Stable",
    },
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
          <div
            key={idx}
            className="bg-card-bg border border-card-border rounded-3xl p-6 hover:shadow-md transition-all group shadow-sm"
          >
            <div className="flex items-start justify-between mb-4">
              <div
                className={`${stat.color} p-3 rounded-2xl text-white shadow-lg`}
              >
                <stat.icon size={24} />
              </div>
              <span className="text-xs font-bold text-emerald-400 flex items-center gap-1">
                <TrendingUp size={14} />
                {stat.trend}
              </span>
            </div>
            <h3 className="text-text-secondary text-sm font-medium mb-1">
              {stat.label}
            </h3>
            <p className="text-3xl font-bold text-text-primary">
              {stat.value.toLocaleString()}
            </p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* System Status */}
        <div className="lg:col-span-2 bg-card-bg border border-card-border rounded-3xl p-8 shadow-sm">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-xl font-bold text-text-primary">
                System Performance
              </h2>
              <p className="text-sm text-text-secondary">
                Real-time infrastructure monitoring
              </p>
            </div>
            <div className="flex items-center gap-2 px-4 py-1.5 bg-emerald-500 text-white rounded-full text-[10px] font-bold uppercase tracking-wider shadow-sm">
              All Systems Operational
            </div>
          </div>

          <div className="space-y-6">
            {[
              { label: "API Latency", value: stats.performance?.api_latency || "---", percent: stats.performance?.api_percent || 5 },
              { label: "Vector DB Sync", value: stats.performance?.vector_sync || "---", percent: stats.performance?.vector_percent || 0 },
              { label: "LLM Response Time", value: stats.performance?.llm_response || "---", percent: stats.performance?.llm_percent || 5 },
            ].map((item, idx) => (
              <div key={idx} className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-text-secondary font-medium">
                    {item.label}
                  </span>
                  <span className="text-text-primary font-bold">
                    {item.value}
                  </span>
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
          <Zap
            size={120}
            className="absolute -bottom-8 -right-8 text-primary-purple/5 group-hover:scale-110 transition-transform duration-700"
          />

          <h2 className="text-xl font-bold mb-2">Quick Actions</h2>
          <p className="text-text-secondary text-sm mb-8">
            Common administrative tasks
          </p>

          <div className="space-y-4">
            {[
              {
                label: "Create New Admin",
                icon: UserPlus,
                onClick: () => setIsModalOpen(true),
              },
              { label: "Upload Data", icon: FileText },
              { label: "View Logs", icon: Clock },
            ].map((action, idx) => (
              <button
                key={idx}
                onClick={action.onClick}
                className="w-full flex items-center gap-3 bg-sidebar-active/50 hover:bg-sidebar-active p-3 rounded-xl transition-all font-semibold text-sm border border-border-light text-text-primary"
              >
                <action.icon size={18} className="text-primary-purple" />
                {action.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Create Admin Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm animate-in fade-in duration-300">
          <div className="bg-white rounded-3xl p-8 w-full max-w-md shadow-2xl border border-border-light animate-in zoom-in-95 duration-300">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-text-primary flex items-center gap-2">
                <UserPlus className="text-primary-purple" />
                Create New Admin
              </h2>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-text-muted hover:text-text-primary"
              >
                <Activity size={20} className="rotate-45" />
              </button>
            </div>

            <form onSubmit={handleCreateAdmin} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-text-muted uppercase tracking-wider mb-1.5 ml-1">
                  Username
                </label>
                <input
                  type="text"
                  required
                  value={formData.username}
                  onChange={(e) =>
                    setFormData({ ...formData, username: e.target.value })
                  }
                  className="w-full bg-slate-50 border border-border-light rounded-xl px-4 py-3 text-sm text-text-primary focus:outline-none focus:border-primary-purple/50 transition-all"
                  placeholder="e.g. ritesh_admin"
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-text-muted uppercase tracking-wider mb-1.5 ml-1">
                  Display Name
                </label>
                <input
                  type="text"
                  value={formData.display_name}
                  onChange={(e) =>
                    setFormData({ ...formData, display_name: e.target.value })
                  }
                  className="w-full bg-slate-50 border border-border-light rounded-xl px-4 py-3 text-sm text-text-primary focus:outline-none focus:border-primary-purple/50 transition-all"
                  placeholder="e.g. Ritesh"
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-text-muted uppercase tracking-wider mb-1.5 ml-1">
                  Password
                </label>
                <div className="relative">
                  <input
                    type={showPassword ? "text" : "password"}
                    required
                    value={formData.password}
                    onChange={(e) =>
                      setFormData({ ...formData, password: e.target.value })
                    }
                    className="w-full bg-slate-50 border border-border-light rounded-xl px-4 py-3 text-sm text-text-primary focus:outline-none focus:border-primary-purple/50 transition-all pr-12"
                    placeholder="••••••••"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-primary p-1.5 transition-colors"
                  >
                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
              </div>

              <div className="pt-4 flex gap-3">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="flex-1 py-3 rounded-xl font-bold text-sm text-text-secondary hover:bg-slate-100 transition-all"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="flex-[2] bg-primary-purple text-white py-3 rounded-xl font-bold text-sm shadow-lg shadow-primary-purple/20 hover:opacity-90 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {creating ? (
                    <RefreshCcw size={16} className="animate-spin" />
                  ) : null}
                  {creating ? "Creating..." : "Create Admin"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;
