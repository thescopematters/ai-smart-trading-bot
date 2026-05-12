/* eslint-disable react-refresh/only-export-components */
/* eslint-disable react-hooks/immutability */
import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(() => {
        const savedUser = localStorage.getItem('crypto_user');
        return savedUser ? JSON.parse(savedUser) : null;
    });
    const [token, setToken] = useState(localStorage.getItem('crypto_token') || null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchMe = async () => {
            if (token) {
                try {
                    const response = await api.get('/api/auth/me', token);
                    if (response.ok) {
                        const data = await response.json();
                        setUser(data);
                        localStorage.setItem('crypto_user', JSON.stringify(data));
                    } else {
                        // Token invalid or expired
                        logout();
                    }
                } catch (error) {
                    console.error("Auth initialization failed:", error);
                    // Don't log out on network error, keep local state
                }
            }
            setLoading(false);
        };
        fetchMe();
    }, [token]);

    const login = (newToken, userData) => {
        setToken(newToken);
        setUser(userData);
        localStorage.setItem('crypto_token', newToken);
        localStorage.setItem('crypto_user', JSON.stringify(userData));
    };

    const logout = () => {
    localStorage.removeItem('crypto_token');
    localStorage.removeItem('crypto_user');
    setTimeout(() => {
        setToken(null);
        setUser(null);
    }, 0);
    };

    return (
        <AuthContext.Provider value={{ user, token, loading, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);
