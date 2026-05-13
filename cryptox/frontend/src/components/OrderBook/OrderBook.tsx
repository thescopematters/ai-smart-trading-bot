import { useEffect, useRef } from 'react';
import { useExchangeStore } from '../../store/useExchangeStore';
import { ordersAPI } from '../../services/api';

export default function OrderBook() {
  const { orderBook, setOrderBook, lastPrice, selectedSymbol } = useExchangeStore();
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // ── Auto-refresh every 3 seconds ─────────────────
  useEffect(() => {
    const refresh = async () => {
      try {
        const res = await ordersAPI.getOrderBook(selectedSymbol);
        setOrderBook(res.data);
      } catch { /* silent fail */ }
    };

    refresh(); // immediate load
    intervalRef.current = setInterval(refresh, 3000);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [selectedSymbol]);

  const symbol = selectedSymbol.split('/');
  const base   = symbol[0] || 'BTC';

  // Calculate max total for depth bar width
  const askTotals = orderBook.asks.map((a) => Number(a.quantity) * Number(a.price));
  const bidTotals = orderBook.bids.map((b) => Number(b.quantity) * Number(b.price));
  const maxTotal  = Math.max(...askTotals, ...bidTotals, 1);

  // Calculate spread
  const lowestAsk  = orderBook.asks.length > 0 ? Number(orderBook.asks[0].price)  : 0;
  const highestBid = orderBook.bids.length > 0 ? Number(orderBook.bids[0].price) : 0;
  const spread     = lowestAsk > 0 && highestBid > 0 ? (lowestAsk - highestBid) : 0;
  const spreadPct  = highestBid > 0 ? ((spread / highestBid) * 100).toFixed(3) : '0';

  return (
    <div className="bg-[#0f172a] flex flex-col h-full overflow-hidden text-xs">

      {/* Header */}
      <div className="px-3 py-2 border-b border-[#1e293b] flex justify-between items-center">
        <span className="text-[#94a3b8] text-[11px] font-semibold uppercase tracking-wider">Order Book</span>
        <span className="text-[#6366f1] text-[10px]">{selectedSymbol}</span>
      </div>

      {/* Column headers */}
      <div className="grid grid-cols-3 px-3 py-1 text-[10px] text-[#475569] uppercase tracking-wider">
        <span>Price</span>
        <span className="text-center">Qty ({base})</span>
        <span className="text-right">Total</span>
      </div>

      {/* ── ASKS (sells) — reversed: lowest at bottom ── */}
      <div className="flex-1 overflow-hidden flex flex-col justify-end">
        {orderBook.asks.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-[#334155] pb-4">
            <div className="text-2xl mb-1 opacity-40">📭</div>
            <span className="text-[10px]">No sell orders</span>
          </div>
        ) : (
          <div className="flex flex-col-reverse">
            {orderBook.asks.slice(0, 10).map((ask) => {
              const rowTotal = Number(ask.quantity) * Number(ask.price);
              const barW     = Math.round((rowTotal / maxTotal) * 100);
              return (
                <div key={ask.id} className="relative grid grid-cols-3 px-3 py-[3px] hover:bg-[#1e293b] cursor-pointer group">
                  {/* Depth bar */}
                  <div className="absolute top-0 right-0 bottom-0 rounded-sm transition-all duration-500"
                    style={{ width: `${barW}%`, background: 'rgba(239,68,68,0.08)' }} />
                  <span className="text-red-400 font-medium z-10 group-hover:text-red-300">
                    ${Number(ask.price).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </span>
                  <span className="text-center text-[#94a3b8] z-10">{Number(ask.quantity).toFixed(4)}</span>
                  <span className="text-right text-[#64748b] z-10">${rowTotal.toFixed(0)}</span>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* ── Spread ── */}
      <div className="flex items-center justify-center gap-2 px-3 py-2 border-y border-[#1e293b] bg-[#0a0f1a]">
        <span className="text-green-400 font-bold text-sm font-display">
          ${lastPrice > 0 ? lastPrice.toLocaleString(undefined, { minimumFractionDigits: 2 }) : '---'}
        </span>
        {spread > 0 && (
          <>
            <span className="text-[#334155] text-[10px]">|</span>
            <span className="text-[10px] text-[#475569]">
              Spread: <span className="text-[#6366f1]">{spreadPct}%</span>
            </span>
          </>
        )}
      </div>

      {/* ── BIDS (buys) ── */}
      <div className="flex-1 overflow-hidden">
        {orderBook.bids.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-[#334155] pt-4">
            <div className="text-2xl mb-1 opacity-40">📭</div>
            <span className="text-[10px]">No buy orders</span>
          </div>
        ) : (
          orderBook.bids.slice(0, 10).map((bid) => {
            const rowTotal = Number(bid.quantity) * Number(bid.price);
            const barW     = Math.round((rowTotal / maxTotal) * 100);
            return (
              <div key={bid.id} className="relative grid grid-cols-3 px-3 py-[3px] hover:bg-[#1e293b] cursor-pointer group">
                <div className="absolute top-0 right-0 bottom-0 rounded-sm transition-all duration-500"
                  style={{ width: `${barW}%`, background: 'rgba(34,197,94,0.08)' }} />
                <span className="text-green-400 font-medium z-10 group-hover:text-green-300">
                  ${Number(bid.price).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </span>
                <span className="text-center text-[#94a3b8] z-10">{Number(bid.quantity).toFixed(4)}</span>
                <span className="text-right text-[#64748b] z-10">${rowTotal.toFixed(0)}</span>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}