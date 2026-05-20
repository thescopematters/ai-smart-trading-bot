import React, { useState, useEffect } from 'react';
import { Upload, FileText, Loader2, Trash2, RefreshCw, Database, Server, ExternalLink } from 'lucide-react';
import { useAdminAuth } from '../../context/AdminAuthContext';
import { useToast } from '../../context/ToastContext';
import ConfirmModal from '../../ui/ConfirmModal';
import { api } from '../../services/api';

const AdminDocuments = () => {
    const toast = useToast();
    const { token } = useAdminAuth();
    const [documents, setDocuments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [uploading, setUploading] = useState(false);
    const [file, setFile] = useState(null);
    const [modalState, setModalState] = useState({ isOpen: false, docId: null });

    const fetchDocuments = async () => {
        setLoading(true);
        try {
            const res = await api.get('/api/admin/documents', token);
            if (res.ok) {
                const data = await res.json();
                setDocuments(data);
            }
        } catch (error) {
            console.error("Failed to fetch documents", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchDocuments();
    }, [token]);

    const handleUpload = async (e) => {
        e.preventDefault();
        if (!file) return;

        setUploading(true);
        const formData = new FormData();
        formData.append('file', file);

        try {
            const res = await api.postForm('/api/admin/documents', formData, token);

            if (res.ok) {
                setFile(null);
                toast({ type: 'success', message: 'Document uploaded and indexed successfully.' });
                fetchDocuments();
            } else {
                const errorData = await res.json();
                toast({ type: 'error', message: `Upload failed: ${errorData.detail || 'Unknown error'}` });
            }
        } catch (error) {
            console.error("Upload error", error);
            toast({ type: 'error', message: `Upload failed: ${error.message}` });
        } finally {
            setUploading(false);
        }
    };

    const handleDelete = async () => {
        const id = modalState.docId;
        setModalState({ isOpen: false, docId: null });

        try {
            const res = await api.delete(`/api/admin/documents/${id}`, token);
            if (res.ok) {
                toast({ type: 'success', message: 'Document deleted successfully.' });
                fetchDocuments();
            } else {
                toast({ type: 'error', message: 'Failed to delete document.' });
            }
        } catch (error) {
            console.error("Delete error", error);
        }
    };

    const handleViewFile = async (docId) => {
        try {
            const res = await api.get(`/api/admin/documents/${docId}/presigned-url`, token);
            if (res.ok) {
                const data = await res.json();
                if (data.url) {
                    window.open(data.url, '_blank', 'noopener,noreferrer');
                } else {
                    toast({ type: 'error', message: 'Failed to retrieve document secure URL.' });
                }
            } else {
                const errData = await res.json().catch(() => ({}));
                toast({ type: 'error', message: errData.detail || 'Failed to generate secure view link.' });
            }
        } catch (error) {
            console.error("View file error", error);
            toast({ type: 'error', message: 'Failed to fetch secure link.' });
        }
    };

    return (
        <div className="bg-card-bg border border-card-border rounded-3xl p-8 shadow-sm">
            <div className="flex items-center justify-between mb-2">
                <h2 className="text-xl font-bold text-text-primary">RAG Knowledge Base</h2>
                <button 
                    onClick={fetchDocuments}
                    className="p-2 text-text-muted hover:text-text-primary transition-colors"
                    title="Sync with storage"
                >
                    <RefreshCw size={20} className={loading ? "animate-spin" : ""} />
                </button>
            </div>
            <p className="text-text-secondary mb-8">Manage the documents that power the chatbot's domain knowledge.</p>

            <form onSubmit={handleUpload} className="mb-8 p-6 border-2 border-dashed border-border-light rounded-2xl bg-sidebar-active/30 flex flex-col items-center justify-center gap-4">
                <input 
                    type="file" 
                    id="doc-upload" 
                    className="hidden" 
                    accept=".pdf,.txt,.docx,.md"
                    onChange={(e) => setFile(e.target.files[0])}
                />
                <label htmlFor="doc-upload" className="cursor-pointer flex flex-col items-center gap-2">
                    <div className="w-16 h-16 rounded-full bg-primary-purple/10 text-primary-purple flex items-center justify-center mb-2 hover:bg-primary-purple/20 transition-colors">
                        <Upload size={28} />
                    </div>
                    <span className="text-text-primary font-medium">
                        {file ? file.name : "Click to select a document"}
                    </span>
                    <span className="text-text-muted text-sm">
                        {file ? `${(file.size / 1024 / 1024).toFixed(2)} MB` : "Supports .pdf, .txt, .md"}
                    </span>
                </label>
                
                <button 
                    type="submit" 
                    disabled={!file || uploading}
                    className="mt-4 px-6 py-2 bg-text-primary hover:bg-text-primary/90 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-all flex items-center gap-2"
                >
                    {uploading ? <Loader2 size={18} className="animate-spin" /> : <Upload size={18} />}
                    {uploading ? "Processing & Embedding..." : "Upload Document"}
                </button>
            </form>

            <div>
                <h3 className="text-lg font-bold text-text-primary mb-4 flex items-center gap-2">
                    <Database size={20} className="text-primary-purple" />
                    Indexed Knowledge
                </h3>
                {loading && documents.length === 0 ? (
                    <div className="flex justify-center p-8"><Loader2 className="animate-spin text-primary-purple" /></div>
                ) : documents.length === 0 ? (
                    <div className="text-center p-8 text-text-muted bg-sidebar-active/30 rounded-xl">No documents indexed yet.</div>
                ) : (
                    <div className="overflow-hidden rounded-xl border border-border-light">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="bg-sidebar-active/50 border-b border-border-light">
                                    <th className="p-4 text-text-muted font-medium text-xs uppercase tracking-wider">Document Name</th>
                                    <th className="p-4 text-text-muted font-medium text-xs uppercase tracking-wider">Source</th>
                                    <th className="p-4 text-text-muted font-medium text-xs uppercase tracking-wider">Status</th>
                                    <th className="p-4 text-text-muted font-medium text-xs uppercase tracking-wider">Indexed At</th>
                                    <th className="p-4 text-text-muted font-medium text-xs uppercase tracking-wider text-right">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-border-light">
                                {documents.map(doc => (
                                    <tr key={doc.id} className="hover:bg-sidebar-active/30 transition-colors text-text-primary">
                                        <td className="p-4">
                                            <div className="flex items-center gap-3">
                                                <FileText size={18} className="text-primary-purple shrink-0" />
                                                <span className="truncate max-w-[200px]" title={doc.file_name}>{doc.file_name}</span>
                                            </div>
                                        </td>
                                        <td className="p-4">
                                            <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                                                doc.source === 'upload' ? 'bg-primary-purple text-white' : 'bg-amber-500 text-white'
                                            }`}>
                                                {doc.source === 'upload' ? <Upload size={10} /> : <Server size={10} />}
                                                {doc.source}
                                            </span>
                                        </td>
                                        <td className="p-4">
                                            <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                                                doc.status === 'processed' ? 'bg-emerald-500 text-white' : 'bg-gray-400 text-white'
                                            }`}>
                                                {doc.status}
                                            </span>
                                        </td>
                                        <td className="p-4 text-xs text-text-muted">
                                            {new Date(doc.created_at).toLocaleDateString()}
                                        </td>
                                        <td className="p-4 text-right">
                                            <div className="flex items-center justify-end gap-2">
                                                {doc.s3_key && (
                                                    <button 
                                                        onClick={() => handleViewFile(doc.id)}
                                                        className="p-2 text-text-muted hover:text-primary-purple transition-colors"
                                                        title="View / Download Document"
                                                    >
                                                        <ExternalLink size={18} />
                                                    </button>
                                                )}
                                                <button 
                                                    onClick={() => setModalState({ isOpen: true, docId: doc.id })}
                                                    className="p-2 text-text-muted hover:text-red-600 transition-colors"
                                                    title="Delete document"
                                                >
                                                    <Trash2 size={18} />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            <ConfirmModal
                isOpen={modalState.isOpen}
                title="Delete Document"
                message="This will remove its knowledge from the chatbot and delete the file. This cannot be undone."
                onConfirm={handleDelete}
                onCancel={() => setModalState({ isOpen: false, docId: null })}
            />

        </div>
    );
};

export default AdminDocuments;
