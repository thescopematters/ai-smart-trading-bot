import { create } from 'zustand';
import { User, Balance, Order, Trade, OrderBook, TradingPair } from '../types';

interface ExchangeStore {
  // ── Auth ──────────────────────────────
  user: User | null;
  token: string | null;
  setUser: (user: User, token: string) => void;
  logout: () => void;

  // ── Trading Pair ───────────────────────
  selectedSymbol: string;
  pairs: TradingPair[];
  setSelectedSymbol: (symbol: string) => void;
  setPairs: (pairs: TradingPair[]) => void;

  // ── Balances ──────────────────────────
  balances: Balance[];
  setBalances: (balances: Balance[]) => void;

  // ── Order Book ────────────────────────
  orderBook: OrderBook;
  setOrderBook: (ob: OrderBook) => void;

  // ── Orders ────────────────────────────
  myOrders: Order[];
  setMyOrders: (orders: Order[]) => void;

  // ── Recent Trades ─────────────────────
  recentTrades: Trade[];
  setRecentTrades: (trades: Trade[]) => void;
  addTrade: (trade: Trade) => void;

  // ── Last Price ────────────────────────
  lastPrice: number;
  setLastPrice: (price: number) => void;
}

export const useExchangeStore = create<ExchangeStore>((set) => ({
  // Auth
  user: null,
  token: null,
  setUser: (user, token) => {
    set({ user, token });
  },
  logout: () => {
    set({ user: null, token: null });
  },

  // Trading Pair
  selectedSymbol: 'BTC/USDT',
  pairs: [],
  setSelectedSymbol: (symbol) => set({ selectedSymbol: symbol }),
  setPairs: (pairs) => set({ pairs }),

  // Balances
  balances: [],
  setBalances: (balances) => set({ balances }),

  // Order Book
  orderBook: { bids: [], asks: [] },
  setOrderBook: (orderBook) => set({ orderBook }),

  // Orders
  myOrders: [],
  setMyOrders: (myOrders) => set({ myOrders }),

  // Recent Trades
  recentTrades: [],
  setRecentTrades: (recentTrades) => set({ recentTrades }),
  addTrade: (trade) =>
    set((state) => ({
      recentTrades: [trade, ...state.recentTrades].slice(0, 50),
      lastPrice: Number(trade.price),
    })),

  // Last Price
  lastPrice: 0,
  setLastPrice: (lastPrice) => set({ lastPrice }),
}));