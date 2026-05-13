// All TypeScript types used across the app

export interface User {
  id: string;
  email: string;
  username: string;
}

export interface Balance {
  id: string;
  currency: string;
  available: number;
  locked: number;
}

export interface TradingPair {
  id: string;
  symbol: string;
  baseCurrency: string;
  quoteCurrency: string;
  minOrderSize: number;
}

export interface Order {
  id: string;
  side: 'BUY' | 'SELL';
  type: 'LIMIT' | 'MARKET';
  price: number | null;
  quantity: number;
  filledQty: number;
  status: 'OPEN' | 'PARTIAL' | 'FILLED' | 'CANCELLED';
  createdAt: string;
  pair?: TradingPair;
}

export interface Trade {
  id: string;
  price: number;
  quantity: number;
  createdAt: string;
  buyerId: string;
  sellerId: string;
}

export interface Candle {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface OrderBookEntry {
  price: number;
  quantity: number;
  filledQty: number;
  id: string;
}

export interface OrderBook {
  bids: OrderBookEntry[];
  asks: OrderBookEntry[];
}