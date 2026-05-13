import { useEffect, useRef, useState } from "react";
import Navbar from "../components/Layout/Navbar";
import Chart from "../components/Chart/Chart";
import OrderBook from "../components/OrderBook/OrderBook";
import OrderForm from "../components/OrderForm/OrderForm";
import TradeHistory from "../components/TradeHistory/TradeHistory";
import { useExchangeStore } from "../store/useExchangeStore";
import { pairsAPI, balancesAPI, ordersAPI, tradesAPI } from "../services/api";
import {
  connectSocket,
  subscribeToSymbol,
  getSocket,
} from "../services/socket";

export default function TradingPage() {
  const [bottomHeight, setBottomHeight] = useState(220);
  const isDragging = useRef(false);

  const handleMouseDown = () => {
    isDragging.current = true;
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging.current) return;
    const screenH = window.innerHeight;
    const newH = screenH - e.clientY;
    if (newH >= 120 && newH <= 500) setBottomHeight(newH);
  };

  const handleMouseUp = () => {
    isDragging.current = false;
  };

  const {
    selectedSymbol,
    setPairs,
    setBalances,
    setMyOrders,
    setRecentTrades,
    setOrderBook,
    setLastPrice,
    addTrade,
  } = useExchangeStore();

  // Load initial data
  useEffect(() => {
    const loadData = async () => {
      try {
        // Load trading pairs
        const pairsRes = await pairsAPI.getAll();
        setPairs(pairsRes.data);

        // Load balances
        const balRes = await balancesAPI.getAll();
        setBalances(balRes.data);

        // Load my orders
        const ordersRes = await ordersAPI.getMyOrders();
        setMyOrders(ordersRes.data);
      } catch (err) {
        console.error("Failed to load initial data", err);
      }
    };
    loadData();
  }, []);

  // Load symbol-specific data when pair changes
  useEffect(() => {
    const loadSymbolData = async () => {
      try {
        // Load order book
        const obRes = await ordersAPI.getOrderBook(selectedSymbol);
        setOrderBook(obRes.data);

        // Load recent trades
        const tradesRes = await tradesAPI.getBySymbol(selectedSymbol);
        setRecentTrades(tradesRes.data);

        // Set last price from most recent trade
        if (tradesRes.data.length > 0) {
          setLastPrice(Number(tradesRes.data[0].price));
        }
      } catch (err) {
        console.error("Failed to load symbol data", err);
      }
    };
    loadSymbolData();
  }, [selectedSymbol]);

  // WebSocket setup
  useEffect(() => {
    const socket = connectSocket();
    subscribeToSymbol(selectedSymbol);

    socket.on("trade:new", async (trade) => {
      addTrade(trade);
      const obRes = await ordersAPI.getOrderBook(selectedSymbol);
      setOrderBook(obRes.data);
      const [ordersRes, balRes] = await Promise.all([
        ordersAPI.getMyOrders(),
        balancesAPI.getAll(),
      ]);
      setMyOrders(ordersRes.data);
      setBalances(balRes.data);
    });

    socket.on("orderbook:update", async () => {
      const obRes = await ordersAPI.getOrderBook(selectedSymbol);
      setOrderBook(obRes.data);
    });

    return () => {
      const s = getSocket();
      if (s) {
        s.emit('unsubscribe', selectedSymbol);
        s.off('trade:new');
        s.off('orderbook:update');
      }
    };
  }, [selectedSymbol]);

  return (
    <div
      className="flex flex-col h-screen bg-[#0f172a] overflow-hidden"
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
    >
      {/* Top navbar */}
      <Navbar />

      {/* Main trading grid */}
      <div
        className="flex flex-1 overflow-hidden min-h-0"
        style={{ gap: "1px", background: "#1e293b" }}
      >
        {/* Chart - takes most space */}
        <div className="flex-1 flex flex-col" style={{ background: "#0f172a" }}>
          <div className="flex-1 relative" style={{ minHeight: "400px" }}>
            <Chart />
          </div>
        </div>

        {/* Order Book */}
        <div style={{ width: "200px", background: "#0f172a", flexShrink: 0 }}>
          <OrderBook />
        </div>

        {/* Buy/Sell Form */}
        <div style={{ width: "240px", background: "#0f172a", flexShrink: 0 }}>
          <OrderForm />
        </div>
      </div>

      <div
        onMouseDown={handleMouseDown}
        style={{
          height: "4px",
          background: "#1e293b",
          cursor: "row-resize",
          flexShrink: 0,
        }}
        className="hover:bg-primary transition-colors"
      />

      {/* Bottom: Trade history + Orders */}
      <div
        style={{
          height: `${bottomHeight}px`,
          borderTop: "1px solid #1e293b",
          flexShrink: 0,
        }}
      >
        <TradeHistory />
      </div>
    </div>
  );
}
