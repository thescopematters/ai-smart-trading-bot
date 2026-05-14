/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable @typescript-eslint/no-unused-vars */
import { useState } from "react";
import { useExchangeStore } from "../../store/useExchangeStore";
import { ordersAPI } from "../../services/api";
import { Balance } from "../../types";
import { useToast } from "../../context/Toastcontext";

export default function OrderForm() {
  const { selectedSymbol, balances, setMyOrders } =
    useExchangeStore();
  const toast = useToast();
  const [side, setSide] = useState<"BUY" | "SELL">("BUY");
  const [orderType, setOrderType] = useState<"LIMIT" | "MARKET">("LIMIT");
  const [price, setPrice] = useState("");
  const [quantity, setQuantity] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{
    text: string;
    type: "success" | "error";
  } | null>(null);

  const pair = selectedSymbol.split("/");
  const base = pair[0] || "BTC";
  const quote = pair[1] || "USDT";

  const getAvailable = (currency: string): number => {
    const b = balances.find((b: Balance) => b.currency === currency);
    return b ? Number(b.available) : 0;
  };

  const total =
    price && quantity ? (Number(price) * Number(quantity)).toFixed(2) : "";
  const fee = total ? (Number(total) * 0.001).toFixed(4) : "";

  const handlePct = (pct: number) => {
    if (side === "BUY") {
      const avail = getAvailable(quote);
      const p = Number(price) || 1;
      setQuantity(((avail * pct) / 100 / p).toFixed(6));
    } else {
      const avail = getAvailable(base);
      setQuantity(((avail * pct) / 100).toFixed(6));
    }
  };

  const handleSubmit = async () => {
    if (!quantity || Number(quantity) <= 0) {
      setMessage({ text: "Enter a valid quantity", type: "error" });
      return;
    }
    if (orderType === "LIMIT" && (!price || Number(price) <= 0)) {
      setMessage({ text: "Enter a valid price", type: "error" });
      return;
    }

    setLoading(true);
    setMessage(null);

    try {
      const res = await ordersAPI.create({
        symbol: selectedSymbol,
        side,
        type: orderType,
        price: orderType === "LIMIT" ? Number(price) : undefined,
        quantity: Number(quantity),
      });

      toast.success(`${side} ${base} order placed! Status: ${res.data.status}`);
      setMessage({
        text: `Order placed! Status: ${res.data.status}`,
        type: "success",
      });
      setQuantity("");

      // Refresh orders
      const ordersRes = await import("../../services/api").then((m) =>
        m.ordersAPI.getMyOrders(),
      );
      setMyOrders(ordersRes.data);
    } catch (err: any) {
      const errMsg = err.response?.data?.message || "Order failed";
      toast.error(errMsg);
      setMessage({ text: errMsg, type: "error" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-[#0f172a] flex flex-col h-full">
      {/* Buy / Sell tabs */}
      <div className="grid grid-cols-2 border-b border-[#1e293b]">
        <button
          onClick={() => setSide("BUY")}
          className={`py-3 text-sm font-semibold transition-all ${side === "BUY" ? "text-green-400 border-b-2 border-green-400" : "text-[#64748b]"}`}
        >
          Buy
        </button>
        <button
          onClick={() => setSide("SELL")}
          className={`py-3 text-sm font-semibold transition-all ${side === "SELL" ? "text-red-400 border-b-2 border-red-400" : "text-[#64748b]"}`}
        >
          Sell
        </button>
      </div>

      <div className="p-3 flex flex-col gap-3 flex-1 overflow-hidden">
        <div className="flex flex-col gap-3 overflow-y-auto flex-1 pb-2">
          {/* Order Type */}
          <div className="flex gap-2">
            {(["LIMIT", "MARKET"] as const).map((t) => (
              <button
                key={t}
                onClick={() => setOrderType(t)}
                className={`px-3 py-1 rounded text-xs border transition-all ${
                  orderType === t
                    ? "bg-[#1e293b] border-primary text-white"
                    : "border-[#334155] text-[#64748b]"
                }`}
              >
                {t}
              </button>
            ))}
          </div>
          {/* Price input */}
          {orderType === "LIMIT" && (
            <div>
              <label className="text-[#64748b] text-[10px] uppercase tracking-wider block mb-1">
                Price
              </label>
              <div className="flex items-center bg-[#1e293b] border border-[#334155] rounded-lg overflow-hidden focus-within:border-primary">
                <input
                  type="number"
                  value={price}
                  onChange={(e) => setPrice(e.target.value)}
                  placeholder="0.00"
                  className="flex-1 bg-transparent px-3 py-2 text-sm text-[#e2e8f0] outline-none"
                />
                <span className="px-3 text-xs text-[#64748b] border-l border-[#334155]">
                  {quote}
                </span>
              </div>
            </div>
          )}

          {/* Quantity input */}
          <div>
            <label className="text-[#64748b] text-[10px] uppercase tracking-wider block mb-1">
              Amount
            </label>
            <div className="flex items-center bg-[#1e293b] border border-[#334155] rounded-lg overflow-hidden focus-within:border-primary">
              <input
                type="number"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                placeholder="0.00"
                className="flex-1 bg-transparent px-3 py-2 text-sm text-[#e2e8f0] outline-none"
              />
              <span className="px-3 text-xs text-[#64748b] border-l border-[#334155]">
                {base}
              </span>
            </div>
          </div>

          {/* Percent buttons */}
          <div className="grid grid-cols-4 gap-1">
            {[25, 50, 75, 100].map((p) => (
              <button
                key={p}
                onClick={() => handlePct(p)}
                className="py-1 text-[10px] text-[#64748b] border border-[#334155] rounded hover:border-primary hover:text-primary transition-all"
              >
                {p}%
              </button>
            ))}
          </div>

          {/* Total */}
          {total && (
            <div>
              <label className="text-[#64748b] text-[10px] uppercase tracking-wider block mb-1">
                Total
              </label>
              <div className="flex items-center bg-[#1e293b] border border-[#1e293b] rounded-lg overflow-hidden">
                <input
                  readOnly
                  value={total}
                  className="flex-1 bg-transparent px-3 py-2 text-sm text-[#94a3b8] outline-none"
                />
                <span className="px-3 text-xs text-[#64748b] border-l border-[#334155]">
                  {quote}
                </span>
              </div>
            </div>
          )}

          {/* Fee + Available */}
          <div className="space-y-1">
            {fee && (
              <div className="flex justify-between text-xs">
                <span className="text-[#64748b]">Fee (0.1%)</span>
                <span className="text-[#94a3b8]">${fee}</span>
              </div>
            )}
            <div className="flex justify-between text-xs pt-1 border-t border-[#1e293b]">
              <span className="text-[#64748b]">Available</span>
              <span className="text-green-400 font-semibold">
                {side === "BUY"
                  ? `$${getAvailable(quote).toLocaleString()} ${quote}`
                  : `${getAvailable(base).toFixed(6)} ${base}`}
              </span>
            </div>
          </div>

          {/* Message */}
          {message && (
            <div
              className={`text-xs rounded-lg p-2 ${
                message.type === "success"
                  ? "bg-green-500/10 border border-green-500/20 text-green-400"
                  : "bg-red-500/10 border border-red-500/20 text-red-400"
              }`}
            >
              {message.text}
            </div>
          )}
        </div>

        {/* Submit button */}
        <button
          onClick={handleSubmit}
          disabled={loading}
          className={`w-full py-3 rounded-lg font-semibold text-white text-sm disabled:opacity-50 transition-opacity ${
            side === "BUY"
              ? "bg-green-500 hover:bg-green-600"
              : "bg-red-500 hover:bg-red-600"
          }`}
        >
          {loading ? "Placing..." : `${side} ${base}`}
        </button>
      </div>
    </div>
  );
}
