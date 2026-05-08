import React from "react";
import { AlertTriangle } from "lucide-react";

const ConfirmModal = ({
  isOpen,
  title,
  message,
  onConfirm,
  onCancel,
  confirmLabel = "Delete",
  confirmClassName,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-card-bg border border-card-border rounded-2xl p-6 shadow-xl w-full max-w-sm mx-4">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 rounded-full bg-red-500/10 flex items-center justify-center shrink-0">
            <AlertTriangle size={20} className="text-red-500" />
          </div>
          <h3 className="text-text-primary font-bold text-lg">{title}</h3>
        </div>
        <p className="text-text-secondary text-sm mb-6">{message}</p>
        <div className="flex gap-3 mt-2">
          <button
            onClick={onCancel}
            className="flex-1 px-4 py-2 rounded-lg text-sm font-medium text-text-primary border border-border-light hover:bg-sidebar-active/50 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className={
              confirmClassName ||
              "flex-1 px-4 py-2 rounded-lg text-sm font-medium bg-red-600 hover:bg-red-700 text-white transition-colors"
            }
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConfirmModal;
