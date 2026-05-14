/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from "react";
import { useExchangeStore } from "../../store/useExchangeStore";
import { Balance, TradingPair } from "../../types";
import { authAPI, tradesAPI } from "../../services/api";
import AddFundsModal from "../../ui/AddFundsModal";

export default function Navbar() {
  const {
    user,
    logout,
    balances,
    pairs,
    selectedSymbol,
    setSelectedSymbol,
    lastPrice,
  } = useExchangeStore();
  const [priceChange, setPriceChange] = useState<{
    pct: number;
    direction: "up" | "down" | "flat";
  }>({ pct: 0, direction: "flat" });
  const [high24h, setHigh24h] = useState(0);
  const [low24h, setLow24h] = useState(0);
  const [vol24h, setVol24h] = useState(0);
  const [showAddFunds, setShowAddFunds] = useState(false);

  const getBalance = (currency: string): number => {
    const b = balances.find((b: Balance) => b.currency === currency);
    return b ? Number(b.available) : 0;
  };

  // Calculate 24h stats from candle data
  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await tradesAPI.getCandles(selectedSymbol);
        const candles: any[] = res.data;
        if (!candles.length) return;

        const now = Math.floor(Date.now() / 1000);
        const oneDayAgo = now - 86400;
        const recent = candles.filter((c) => c.time >= oneDayAgo);

        if (recent.length === 0) return;

        const openPrice = recent[0].open;
        const closePrice = recent[recent.length - 1].close;
        const high = Math.max(...recent.map((c) => c.high));
        const low = Math.min(...recent.map((c) => c.low));
        const vol = recent.reduce((sum, c) => sum + c.volume, 0);
        const pct = ((closePrice - openPrice) / openPrice) * 100;

        setPriceChange({
          pct,
          direction: pct > 0 ? "up" : pct < 0 ? "down" : "flat",
        });
        setHigh24h(high);
        setLow24h(low);
        setVol24h(vol);
      } catch {
        /* no data yet */
      }
    };
    fetchStats();
  }, [selectedSymbol, lastPrice]);

  const pctColor =
    priceChange.direction === "up"
      ? "#22c55e"
      : priceChange.direction === "down"
        ? "#ef4444"
        : "#64748b";
  const pctSign = priceChange.direction === "up" ? "+" : "";

  return (
    <div className="border-b border-[#1e293b] bg-[#0f172a]">
      {/* Main row */}
      <div className="flex items-center justify-between px-4 py-2 flex-wrap gap-2">
        {/* Logo */}
        <div
          className="text-lg font-bold font-display flex-shrink-0"
          style={{
            background: "linear-gradient(135deg, #6366f1, #ec4899)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
          }}
        >
          CryptoX
        </div>

        {/* Pair Tabs */}
        <div className="flex gap-2">
          {pairs.map((pair: TradingPair) => (
            <button
              key={pair.symbol}
              onClick={() => setSelectedSymbol(pair.symbol)}
              className={`px-3 py-1 rounded text-xs font-medium border transition-all ${
                selectedSymbol === pair.symbol
                  ? "bg-primary border-primary text-white"
                  : "border-[#334155] text-[#94a3b8] hover:border-primary"
              }`}
            >
              {pair.symbol}
            </button>
          ))}
        </div>

        {/* Balances + User */}
        <div className="flex items-center gap-3 flex-shrink-0">
          <div className="bg-[#1e293b] border border-[#334155] rounded-full px-3 py-1 text-xs text-[#94a3b8]">
            USDT:{" "}
            <span className="text-green-400 font-semibold">
              ${getBalance("USDT").toLocaleString()}
            </span>
          </div>
          <div className="bg-[#1e293b] border border-[#334155] rounded-full px-3 py-1 text-xs text-[#94a3b8]">
            BTC:{" "}
            <span className="text-green-400 font-semibold">
              {getBalance("BTC").toFixed(4)}
            </span>
          </div>

          <button
            onClick={() => setShowAddFunds(true)}
            style={{
              background: "linear-gradient(135deg, #6366f1, #4f46e5)",
              border: "none",
              borderRadius: "20px",
              padding: "4px 12px",
              fontSize: "11px",
              fontWeight: 600,
              color: "#fff",
              cursor: "pointer",
            }}
          >
            + Add Funds
          </button>

          <div className="flex items-center gap-2">
            <div
              className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold text-white"
              style={{
                background: "linear-gradient(135deg, #6366f1, #ec4899)",
              }}
            >
              {user?.username?.[0]?.toUpperCase() || "U"}
            </div>
            <span className="text-xs text-[#94a3b8] hidden sm:block">
              {user?.username}
            </span>
            <button
              onClick={async () => {
                await authAPI.logout();
                localStorage.removeItem('token');
                logout();
              }}
              className="text-xs text-[#64748b] hover:text-red-400 transition-colors"
            >
              Logout
            </button>
          </div>
        </div>
      </div>

      {/* 24h Stats row */}
      <div className="flex items-center gap-6 px-4 py-1 border-t border-[#1e293b] overflow-x-auto">
        {/* Last price */}
        <div className="flex items-center gap-2 flex-shrink-0">
          <span className="text-[10px] text-[#475569] uppercase tracking-wider">
            Last
          </span>
          <span className="text-sm font-bold" style={{ color: pctColor }}>
            $
            {lastPrice > 0
              ? lastPrice.toLocaleString(undefined, {
                  minimumFractionDigits: 2,
                })
              : "---"}
          </span>
        </div>

        {/* 24h Change */}
        <div className="flex items-center gap-1 flex-shrink-0">
          <span className="text-[10px] text-[#475569] uppercase tracking-wider">
            24h
          </span>
          <span
            className="text-xs font-semibold px-1.5 py-0.5 rounded"
            style={{ color: pctColor, background: `${pctColor}18` }}
          >
            {priceChange.pct !== 0
              ? `${pctSign}${priceChange.pct.toFixed(2)}%`
              : "--"}
          </span>
        </div>

        {/* 24h High */}
        {high24h > 0 && (
          <div className="flex items-center gap-1 flex-shrink-0">
            <span className="text-[10px] text-[#475569] uppercase tracking-wider">
              High
            </span>
            <span className="text-xs text-[#22c55e] font-medium">
              ${high24h.toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </span>
          </div>
        )}

        {/* 24h Low */}
        {low24h > 0 && (
          <div className="flex items-center gap-1 flex-shrink-0">
            <span className="text-[10px] text-[#475569] uppercase tracking-wider">
              Low
            </span>
            <span className="text-xs text-red-400 font-medium">
              ${low24h.toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </span>
          </div>
        )}

        {/* 24h Volume */}
        {vol24h > 0 && (
          <div className="flex items-center gap-1 flex-shrink-0">
            <span className="text-[10px] text-[#475569] uppercase tracking-wider">
              Vol
            </span>
            <span className="text-xs text-[#94a3b8] font-medium">
              {vol24h.toFixed(4)} {selectedSymbol.split("/")[0]}
            </span>
          </div>
        )}
      </div>
      <AddFundsModal
        isOpen={showAddFunds}
        onClose={() => setShowAddFunds(false)}
      />
    </div>
  );
}
