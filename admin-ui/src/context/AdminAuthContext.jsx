import React, { createContext, useContext, useState, useEffect } from 'react';

const AdminAuthContext = createContext(null);

export const AdminAuthProvider = ({ children }) => {
    const [admin, setAdmin] = useState(() => {
        const saved = localStorage.getItem('admin_user');
        return saved ? JSON.parse(saved) : null;
    });
    const [token, setToken] = useState(localStorage.getItem('admin_token') || null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchMe = async () => {
            if (token) {
                try {
                    const response = await fetch('http://localhost:8000/api/admin/me', {
                        headers: { 'Authorization': `Bearer ${token}` }
                    });
                    if (response.ok) {
                        const data = await response.json();
                        setAdmin(data);
                        localStorage.setItem('admin_user', JSON.stringify(data));
                    } else {
                        logout();
                    }
                } catch (error) {
                    console.error("Admin auth failed:", error);
                }
            }
            setLoading(false);
        };
        fetchMe();
    }, [token]);

    const login = (newToken, adminData) => {
        setToken(newToken);
        setAdmin(adminData);
        localStorage.setItem('admin_token', newToken);
        localStorage.setItem('admin_user', JSON.stringify(adminData));
    };

    const logout = () => {
        setToken(null);
        setAdmin(null);
        localStorage.removeItem('admin_token');
        localStorage.removeItem('admin_user');
    };

    return (
        <AdminAuthContext.Provider value={{ admin, token, loading, login, logout }}>
            {children}
        </AdminAuthContext.Provider>
    );
};

export const useAdminAuth = () => useContext(AdminAuthContext);
