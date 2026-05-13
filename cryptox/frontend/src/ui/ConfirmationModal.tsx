interface Props {
  isOpen: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
  danger?: boolean;
}

export default function ConfirmationModal({
  isOpen,
  title,
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  onConfirm,
  onCancel,
  danger = false,
}: Props) {
  if (!isOpen) return null;

  return (
    // Backdrop
    <div
      onClick={onCancel}
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0,0,0,0.6)',
        zIndex: 1000,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      {/* Modal box — stop click from closing */}
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: '#1e293b',
          border: '0.5px solid #334155',
          borderRadius: '12px',
          padding: '24px',
          width: '100%',
          maxWidth: '380px',
          margin: '0 16px',
        }}
      >
        {/* Title */}
        <h3 style={{
          fontSize: '15px',
          fontWeight: 600,
          color: '#e2e8f0',
          marginBottom: '8px',
        }}>
          {title}
        </h3>

        {/* Message */}
        <p style={{
          fontSize: '13px',
          color: '#94a3b8',
          lineHeight: 1.6,
          marginBottom: '24px',
        }}>
          {message}
        </p>

        {/* Buttons */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
          <button
            onClick={onCancel}
            style={{
              padding: '8px 18px',
              borderRadius: '7px',
              fontSize: '13px',
              fontWeight: 500,
              border: '0.5px solid #334155',
              background: 'transparent',
              color: '#94a3b8',
              cursor: 'pointer',
            }}
          >
            {cancelLabel}
          </button>
          <button
            onClick={onConfirm}
            style={{
              padding: '8px 18px',
              borderRadius: '7px',
              fontSize: '13px',
              fontWeight: 600,
              border: 'none',
              background: danger ? '#ef4444' : '#6366f1',
              color: '#fff',
              cursor: 'pointer',
            }}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}