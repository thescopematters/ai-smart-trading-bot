import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import ErrorBoundary from './components/ErrorBoundary';
import AdminLogin from './pages/AdminLogin';
import AdminLayout from './pages/admin/AdminLayout';
import AdminDashboard from './pages/admin/AdminDashboard';
import AdminUsers from './pages/admin/AdminUsers';
import AdminUserChats from './pages/admin/AdminUserChats';
import AdminDocuments from './pages/admin/AdminDocuments';
import AdminQuestions from './pages/admin/AdminQuestions';
import { AdminAuthProvider } from './context/AdminAuthContext';

function App() {
  return (
    <AdminAuthProvider>
      <Router>
        <div className="min-h-screen bg-main-bg flex flex-col selection:bg-primary-purple/20">
          <ErrorBoundary>
            <Routes>
              <Route path="/login" element={<AdminLogin />} />
              
              <Route path="/" element={<AdminLayout />}>
                <Route index element={<AdminDashboard />} />
                <Route path="users" element={<AdminUsers />} />
                <Route path="chats" element={<AdminUserChats />} />
                <Route path="documents" element={<AdminDocuments />} />
                <Route path="questions" element={<AdminQuestions />} />
              </Route>

              {/* Fallback */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </ErrorBoundary>
        </div>
      </Router>
    </AdminAuthProvider>
  );
}

export default App;