import axios from 'axios';

// Base URL of your backend
const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:3000";

// Create axios instance
const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: false,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ── AUTH ──────────────────────────────────────────
export const authAPI = {
  register: (email: string, username: string, password: string) =>
    api.post('/api/auth/register', { email, username, password }),

  login: (email: string, password: string) =>
    api.post('/api/auth/login', { email, password }),

  logout: () => api.post('/api/auth/logout'),
};

// ── BALANCES ──────────────────────────────────────
export const balancesAPI = {
  getAll: () => api.get('/api/balances'),

  topUp: (currency: string, amount: number) =>
    api.post('/api/balances/topup', { currency, amount }),
};

// ── PAIRS ─────────────────────────────────────────
export const pairsAPI = {
  getAll: () => api.get('/api/pairs'),
};

// ── ORDERS ────────────────────────────────────────
export const ordersAPI = {
  create: (data: {
    symbol: string;
    side: 'BUY' | 'SELL';
    type: 'LIMIT' | 'MARKET';
    price?: number;
    quantity: number;
  }) => api.post('/api/orders', data),

  getMyOrders: () => api.get('/api/orders'),

  cancel: (id: string) => api.delete(`/api/orders/${id}`),

  getOrderBook: (symbol: string) =>
    api.get(`/api/orders/orderbook/${encodeURIComponent(symbol)}`),
};

// ── TRADES ────────────────────────────────────────
export const tradesAPI = {
  getMy: () => api.get('/api/trades/my'),

  getBySymbol: (symbol: string) =>
    api.get(`/api/trades/symbol/${encodeURIComponent(symbol)}`),

  getCandles: (symbol: string) =>
    api.get(`/api/trades/candles/${encodeURIComponent(symbol)}`),
};

// ── USERS ─────────────────────────────────────────
export const usersAPI = {
  getMe: () => api.get('/api/users/me'),
};

export default api;