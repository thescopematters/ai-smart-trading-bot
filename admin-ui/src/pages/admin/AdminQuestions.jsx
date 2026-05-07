import React, { useState, useEffect } from 'react';
import { Plus, Edit2, Trash2, Check, X, Loader2 } from 'lucide-react';
import { useAdminAuth } from '../../context/AdminAuthContext';
import { useToast } from '../../context/ToastContext';
import ConfirmModal from '../../ui/ConfirmModal';

const AdminQuestions = () => {
    const { token } = useAdminAuth();
    const [questions, setQuestions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [editingId, setEditingId] = useState(null);
    const [editForm, setEditForm] = useState({ text: '', order: 0, active: true });

    const toast = useToast();
    const [modalState, setModalState] = useState({ isOpen: false, questionId: null });
    
    // Add new question form
    const [newQuestionText, setNewQuestionText] = useState('');

    const fetchQuestions = async () => {
        setLoading(true);
        try {
            const res = await fetch('http://localhost:8000/api/questions');
            if (res.ok) {
                const data = await res.json();
                setQuestions(data);
            }
        } catch (error) {
            console.error("Failed to fetch questions", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchQuestions();
    }, []);

    const handleAdd = async (e) => {
        e.preventDefault();
        if (!newQuestionText.trim()) return;

        try {
            const res = await fetch('http://localhost:8000/api/admin/questions', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${token}` 
                },
                body: JSON.stringify({
                    question_text: newQuestionText.trim(),
                    display_order: questions.length,
                    is_active: true
                })
            });

            if (res.ok) {
                setNewQuestionText('');
                toast({ type: 'success', message: 'Question added successfully.' });
                fetchQuestions();
            } else {
                toast({ type: 'error', message: 'Failed to add question.' });
            }
        } catch (error) {
            console.error(error);
        }
    };

    const handleEdit = (q) => {
        setEditingId(q.id);
        setEditForm({ text: q.text, order: q.display_order || 0, active: true });
    };

    const handleUpdate = async (id) => {
        if (!editForm.text.trim()) return;
        try {
            const res = await fetch(`http://localhost:8000/api/admin/questions/${id}`, {
                method: 'PUT',
                headers: { 
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${token}` 
                },
                body: JSON.stringify({
                    question_text: editForm.text.trim(),
                    display_order: editForm.order,
                    is_active: editForm.active
                })
            });

            if (res.ok) {
                setEditingId(null);
                toast({ type: 'success', message: 'Question updated successfully.' });
                fetchQuestions();
            } else {
                toast({ type: 'error', message: 'Failed to update question.' });
            }
        } catch (error) {
            console.error(error);
        }
    };

    const handleDelete = async () => {
        const id = modalState.questionId;
        setModalState({ isOpen: false, questionId: null });

        try {
            const res = await fetch(`http://localhost:8000/api/admin/questions/${id}`, {
                method: 'DELETE',
                headers: { Authorization: `Bearer ${token}` }
            });

            if (res.ok) {
                toast({ type: 'success', message: 'Question deleted successfully.' });
                fetchQuestions();
            } else {
                toast({ type: 'error', message: 'Failed to delete question.' });
            }
        } catch (error) {
            console.error(error);
            toast({ type: 'error', message: 'Something went wrong.' });
        }
    };

    return (
        <div className="bg-card-bg border border-card-border rounded-3xl p-8 shadow-sm">
            <h2 className="text-xl font-bold text-text-primary mb-2">Default Questions</h2>
            <p className="text-text-secondary mb-8">Manage the quick-selectable questions shown to users on the chat screen.</p>
            
            <form onSubmit={handleAdd} className="flex gap-4 mb-8 bg-sidebar-active/30 p-4 rounded-xl border border-border-light">
                <input 
                    type="text"
                    value={newQuestionText}
                    onChange={(e) => setNewQuestionText(e.target.value)}
                    placeholder="Enter a new default question..."
                    className="flex-1 bg-white border border-border-light rounded-lg px-4 py-2 text-text-primary placeholder-text-muted focus:outline-none focus:border-primary-purple"
                />
                <button 
                    type="submit"
                    disabled={!newQuestionText.trim()}
                    className="bg-text-primary hover:bg-text-primary/90 disabled:opacity-50 text-white px-6 py-2 rounded-lg font-medium flex items-center gap-2 transition-colors"
                >
                    <Plus size={18} /> Add
                </button>
            </form>

            <div className="bg-card-bg rounded-xl border border-border-light overflow-hidden shadow-sm">
                {loading ? (
                    <div className="flex justify-center p-8"><Loader2 className="animate-spin text-primary-purple" /></div>
                ) : questions.length === 0 ? (
                    <div className="text-center p-8 text-text-muted">No questions found.</div>
                ) : (
                    <ul className="divide-y divide-border-light">
                        {questions.map((q) => (
                            <li key={q.id} className="p-4 flex items-center justify-between hover:bg-sidebar-active/30 transition-colors group">
                                {editingId === q.id ? (
                                    <div className="flex-1 flex gap-4 mr-4">
                                        <input 
                                            type="text"
                                            value={editForm.text}
                                            onChange={(e) => setEditForm({...editForm, text: e.target.value})}
                                            className="flex-1 bg-white border border-primary-purple rounded-lg px-3 py-1.5 text-text-primary focus:outline-none focus:ring-1 focus:ring-primary-purple"
                                            autoFocus
                                        />
                                    </div>
                                ) : (
                                    <span className="text-text-primary font-medium flex-1">{q.text}</span>
                                )}

                                <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                    {editingId === q.id ? (
                                        <>
                                            <button onClick={() => handleUpdate(q.id)} className="p-2 text-emerald-600 hover:bg-emerald-50 rounded-lg">
                                                <Check size={18} />
                                            </button>
                                            <button onClick={() => setEditingId(null)} className="p-2 text-text-muted hover:bg-sidebar-active rounded-lg">
                                                <X size={18} />
                                            </button>
                                        </>
                                    ) : (
                                        <>
                                            <button onClick={() => handleEdit(q)} className="p-2 text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors">
                                                <Edit2 size={18} />
                                            </button>
                                            <button onClick={() => setModalState({ isOpen: true, questionId: q.id })} className="p-2 text-rose-600 hover:bg-rose-50 rounded-lg transition-colors">
                                                <Trash2 size={18} />
                                            </button>
                                        </>
                                    )}
                                </div>
                            </li>
                        ))}
                    </ul>
                )}
            </div>
            <ConfirmModal
                isOpen={modalState.isOpen}
                title="Delete Question"
                message="This question will be permanently removed from the chat screen. This cannot be undone."
                onConfirm={handleDelete}
                onCancel={() => setModalState({ isOpen: false, questionId: null })}
            />
        </div>
    );
};

export default AdminQuestions;
