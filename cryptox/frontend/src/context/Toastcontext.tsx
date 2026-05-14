import { createContext, useContext, useState, useCallback, ReactNode } from 'react';

// ── Types ──────────────────────────────────────────
type ToastType = 'success' | 'error' | 'info' | 'warning';

interface Toast {
  id: string;
  message: string;
  type: ToastType;
}

interface ToastContextValue {
  showToast: (message: string, type?: ToastType) => void;
  success: (message: string) => void;
  error: (message: string) => void;
  info: (message: string) => void;
  warning: (message: string) => void;
}

// ── Context ────────────────────────────────────────
const ToastContext = createContext<ToastContextValue | null>(null);

// ── Hook ───────────────────────────────────────────
export const useToast = (): ToastContextValue => {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used inside ToastProvider');
  return ctx;
};

// ── Icons ──────────────────────────────────────────
const icons: Record<ToastType, string> = {
  success: '✅',
  error:   '❌',
  info:    'ℹ️',
  warning: '⚠️',
};

const colors: Record<ToastType, { bg: string; border: string; text: string }> = {
  success: { bg: 'rgba(34,197,94,0.12)',  border: 'rgba(34,197,94,0.3)',  text: '#22c55e' },
  error:   { bg: 'rgba(239,68,68,0.12)',  border: 'rgba(239,68,68,0.3)',  text: '#ef4444' },
  info:    { bg: 'rgba(99,102,241,0.12)', border: 'rgba(99,102,241,0.3)', text: '#6366f1' },
  warning: { bg: 'rgba(234,179,8,0.12)',  border: 'rgba(234,179,8,0.3)',  text: '#eab308' },
};

// ── Provider ───────────────────────────────────────
export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const showToast = useCallback((message: string, type: ToastType = 'info') => {
    const id = Math.random().toString(36).slice(2);
    setToasts((prev) => [...prev, { id, message, type }]);

    // Auto remove after 3.5 seconds
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3500);
  }, []);

  const success = useCallback((msg: string) => showToast(msg, 'success'), [showToast]);
  const error   = useCallback((msg: string) => showToast(msg, 'error'),   [showToast]);
  const info    = useCallback((msg: string) => showToast(msg, 'info'),    [showToast]);
  const warning = useCallback((msg: string) => showToast(msg, 'warning'), [showToast]);

  return (
    <ToastContext.Provider value={{ showToast, success, error, info, warning }}>
      {children}

      {/* Toast Container — fixed top-right */}
      <div style={{
        position: 'fixed',
        top: '16px',
        right: '16px',
        zIndex: 9999,
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
        pointerEvents: 'none',
      }}>
        {toasts.map((toast) => (
          <div
            key={toast.id}
            style={{
              background: colors[toast.type].bg,
              border: `1px solid ${colors[toast.type].border}`,
              borderRadius: '10px',
              padding: '12px 16px',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              minWidth: '280px',
              maxWidth: '380px',
              backdropFilter: 'blur(8px)',
              animation: 'slideIn 0.25s ease',
              pointerEvents: 'auto',
            }}
          >
            <span style={{ fontSize: '16px' }}>{icons[toast.type]}</span>
            <span style={{
              color: colors[toast.type].text,
              fontSize: '13px',
              fontWeight: 500,
              flex: 1,
            }}>
              {toast.message}
            </span>
          </div>
        ))}
      </div>

      {/* Animation style */}
      <style>{`
        @keyframes slideIn {
          from { opacity: 0; transform: translateX(40px); }
          to   { opacity: 1; transform: translateX(0); }
        }
      `}</style>
    </ToastContext.Provider>
  );
}