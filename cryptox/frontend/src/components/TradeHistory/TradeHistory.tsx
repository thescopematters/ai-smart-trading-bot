/* eslint-disable @typescript-eslint/no-explicit-any */
import { useExchangeStore } from "../../store/useExchangeStore";
import { Trade } from "../../types";
import { useState } from "react";
import ConfirmationModal from "../../ui/ConfirmationModal";
import { useToast } from "../../context/Toastcontext";

export default function TradeHistory() {
  const toast = useToast();
  const { recentTrades, selectedSymbol, myOrders, setMyOrders } =
    useExchangeStore();
  const [activeTab, setActiveTab] = useState("trades");

  const [cancelOrderId, setCancelOrderId] = useState<string | null>(null);
  const [cancelling, setCancelling] = useState(false);

  const handleCancel = async () => {
    if (!cancelOrderId) return;
    setCancelling(true);
    try {
      await import("../../services/api").then((m) =>
        m.ordersAPI.cancel(cancelOrderId),
      );
      const res = await import("../../services/api").then((m) =>
        m.ordersAPI.getMyOrders(),
      );
      setMyOrders(res.data);
      toast.success('Order cancelled successfully! Funds returned to balance.');
    } catch (err: any) {
      alert(err.response?.data?.message || "Cancel failed");
    } finally {
      setCancelling(false);
      setCancelOrderId(null);
    }
  };

  const openOrders = myOrders.filter(
    (o) => o.status === "OPEN" || o.status === "PARTIAL",
  );

  return (
    <div className="bg-[#0f172a] border-t border-[#1e293b]">
      {/* Tabs */}
      <div className="flex gap-4 px-4 border-b border-[#1e293b]">
        {[
          { key: "trades", label: `Recent Trades` },
          { key: "orders", label: `Open Orders (${openOrders.length})` },
          { key: "history", label: "Order History" },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`py-2 text-xs font-medium border-b-2 transition-all ${
              activeTab === tab.key
                ? "border-primary text-primary"
                : "border-transparent text-[#64748b] hover:text-[#94a3b8]"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div
        className="overflow-x-auto"
        style={{ maxHeight: "160px", overflowY: "auto" }}
      >
        {/* Recent Trades */}
        {activeTab === "trades" && (
          <table className="w-full text-xs">
            <thead>
              <tr className="text-[#475569] uppercase tracking-wider">
                <th className="text-left px-4 py-2">Price</th>
                <th className="text-center py-2">Amount</th>
                <th className="text-right px-4 py-2">Time</th>
              </tr>
            </thead>
            <tbody>
              {recentTrades.slice(0, 20).map((trade: Trade, i) => (
                <tr key={trade.id || i} className="border-t border-[#1e293b]">
                  <td
                    className={`px-4 py-1 font-medium ${
                      i === 0 ||
                      Number(trade.price) >= Number(recentTrades[i - 1]?.price)
                        ? "text-green-400"
                        : "text-red-400"
                    }`}
                  >
                    $
                    {Number(trade.price).toLocaleString(undefined, {
                      minimumFractionDigits: 2,
                    })}
                  </td>
                  <td className="text-center text-[#94a3b8]">
                    {Number(trade.quantity).toFixed(4)}
                  </td>
                  <td className="px-4 text-right text-[#475569]">
                    {new Date(trade.createdAt).toLocaleTimeString()}
                  </td>
                </tr>
              ))}
              {recentTrades.length === 0 && (
                <tr>
                  <td colSpan={3} className="text-center text-[#475569] py-4">
                    No trades yet
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}

        {/* Open Orders */}
        {activeTab === "orders" && (
          <table className="w-full text-xs">
            <thead>
              <tr className="text-[#475569] uppercase tracking-wider">
                <th className="text-left px-4 py-2">Pair</th>
                <th className="py-2">Side</th>
                <th className="py-2">Price</th>
                <th className="py-2">Amount</th>
                <th className="py-2">Filled</th>
                <th className="py-2">Status</th>
                <th className="text-right px-4 py-2">Action</th>
              </tr>
            </thead>
            <tbody>
              {openOrders.map((order) => (
                <tr key={order.id} className="border-t border-[#1e293b]">
                  <td className="px-4 py-1 text-[#94a3b8]">
                    {order.pair?.symbol || selectedSymbol}
                  </td>
                  <td className="text-center">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                        order.side === "BUY"
                          ? "bg-green-500/10 text-green-400"
                          : "bg-red-500/10 text-red-400"
                      }`}
                    >
                      {order.side}
                    </span>
                  </td>
                  <td className="text-center text-[#94a3b8]">
                    {order.price
                      ? `$${Number(order.price).toLocaleString()}`
                      : "Market"}
                  </td>
                  <td className="text-center text-[#94a3b8]">
                    {Number(order.quantity).toFixed(4)}
                  </td>
                  <td className="text-center text-primary">
                    {(
                      (Number(order.filledQty) / Number(order.quantity)) *
                      100
                    ).toFixed(0)}
                    %
                  </td>
                  <td className="text-center">
                    <span className="px-2 py-0.5 rounded text-[10px] bg-primary/10 text-primary">
                      {order.status}
                    </span>
                  </td>
                  <td className="px-4 text-right">
                    <button
                      onClick={() => setCancelOrderId(order.id)}
                      className="px-2 py-0.5 rounded border border-[#334155] text-[#64748b] hover:border-red-400 hover:text-red-400 transition-all text-[10px]"
                    >
                      Cancel
                    </button>
                  </td>
                </tr>
              ))}
              {openOrders.length === 0 && (
                <tr>
                  <td colSpan={7} className="text-center text-[#475569] py-4">
                    No open orders
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}

        {/* Order History */}
        {activeTab === "history" && (
          <table className="w-full text-xs">
            <thead>
              <tr className="text-[#475569] uppercase tracking-wider">
                <th className="text-left px-4 py-2">Pair</th>
                <th className="py-2">Side</th>
                <th className="py-2">Price</th>
                <th className="py-2">Amount</th>
                <th className="py-2">Status</th>
                <th className="text-right px-4 py-2">Time</th>
              </tr>
            </thead>
            <tbody>
              {myOrders.map((order) => (
                <tr key={order.id} className="border-t border-[#1e293b]">
                  <td className="px-4 py-1 text-[#94a3b8]">
                    {order.pair?.symbol || selectedSymbol}
                  </td>
                  <td className="text-center">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                        order.side === "BUY"
                          ? "bg-green-500/10 text-green-400"
                          : "bg-red-500/10 text-red-400"
                      }`}
                    >
                      {order.side}
                    </span>
                  </td>
                  <td className="text-center text-[#94a3b8]">
                    {order.price
                      ? `$${Number(order.price).toLocaleString()}`
                      : "Market"}
                  </td>
                  <td className="text-center text-[#94a3b8]">
                    {Number(order.quantity).toFixed(4)}
                  </td>
                  <td className="text-center">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] ${
                        order.status === "FILLED"
                          ? "bg-green-500/10 text-green-400"
                          : order.status === "CANCELLED"
                            ? "bg-red-500/10 text-red-400"
                            : "bg-primary/10 text-primary"
                      }`}
                    >
                      {order.status}
                    </span>
                  </td>
                  <td className="px-4 text-right text-[#475569]">
                    {new Date(order.createdAt).toLocaleTimeString()}
                  </td>
                </tr>
              ))}
              {myOrders.length === 0 && (
                <tr>
                  <td colSpan={6} className="text-center text-[#475569] py-4">
                    No orders yet
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>

      <ConfirmationModal
        isOpen={cancelOrderId !== null}
        title="Cancel Order"
        message="Are you sure you want to cancel this order? Your locked funds will be returned to your available balance."
        confirmLabel={cancelling ? "Cancelling..." : "Yes, Cancel Order"}
        cancelLabel="Keep Order"
        danger={true}
        onConfirm={handleCancel}
        onCancel={() => setCancelOrderId(null)}
      />
    </div>
  );
}
