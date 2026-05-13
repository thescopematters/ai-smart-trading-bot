/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useRef, useState } from "react";
import {
  createChart,
  IChartApi,
  ISeriesApi,
  UTCTimestamp,
} from "lightweight-charts";
import { useExchangeStore } from "../../store/useExchangeStore";
import { tradesAPI } from "../../services/api";

type Interval = '1m' | '15m' | '1H' | '4H' | '1D';
const intervalSeconds: Record<Interval, number> = {
  '1m':  60,
  '15m': 900,
  '1H':  3600,
  '4H':  14400,
  '1D':  86400,
};

export default function Chart() {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInst = useRef<IChartApi | null>(null);
  const candleSeries = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const lineSeries = useRef<ISeriesApi<"Area"> | null>(null);
  const prevPrice = useRef<number>(0);
  const bucketOpen = useRef<Record<number, number>>({});
  const [priceDir, setPriceDir] = useState<"up" | "down">("up");
  const [interval, setIntervalVal] = useState<Interval>("1m");
  const [chartType, setChartType] = useState<"candle" | "line">("candle");
  const { selectedSymbol, lastPrice } = useExchangeStore();

  useEffect(() => {
    if (!chartRef.current) return;
    chartInst.current = createChart(chartRef.current, {
      layout: { background: { color: "#0f172a" }, textColor: "#64748b" },
      grid: {
        vertLines: { color: "#1e293b" },
        horzLines: { color: "#1e293b" },
      },
      rightPriceScale: {
        borderColor: "#1e293b",
        minimumWidth: 80,
        autoScale: true,
      },
      timeScale: {
        borderColor: "#1e293b",
        timeVisible: true,
        secondsVisible: false,
      },
      crosshair: {
        vertLine: { color: "#6366f1", labelBackgroundColor: "#6366f1" },
        horzLine: { color: "#6366f1", labelBackgroundColor: "#6366f1" },
      },
      width: chartRef.current.clientWidth,
      height: chartRef.current.clientHeight,
    });

    candleSeries.current = chartInst.current.addCandlestickSeries({
      upColor: "#22c55e",
      downColor: "#ef4444",
      borderUpColor: "#22c55e",
      borderDownColor: "#ef4444",
      wickUpColor: "#22c55e",
      wickDownColor: "#ef4444",
    });

    lineSeries.current = chartInst.current.addAreaSeries({
      lineColor: "#6366f1",
      topColor: "rgba(99,102,241,0.2)",
      bottomColor: "rgba(99,102,241,0.0)",
      lineWidth: 2,
      visible: false,
    });

    const onResize = () => {
      if (chartRef.current && chartInst.current) {
        chartInst.current.applyOptions({
          width: chartRef.current.clientWidth,
          height: chartRef.current.clientHeight,
        });
      }
    };
    window.addEventListener("resize", onResize);
    return () => {
      window.removeEventListener("resize", onResize);
      chartInst.current?.remove();
      chartInst.current = null;
      candleSeries.current = null;
      lineSeries.current = null;
    };
  }, []);

  // Toggle chart type visibility
  useEffect(() => {
    candleSeries.current?.applyOptions({ visible: chartType === "candle" });
    lineSeries.current?.applyOptions({ visible: chartType === "line" });
  }, [chartType]);

  // Load data on symbol or interval change
  useEffect(() => {
    bucketOpen.current = {}; // reset on symbol/interval change
    prevPrice.current = 0;

    candleSeries.current?.setData([]);
    lineSeries.current?.setData([]);
    const load = async () => {
      try {
        const res = await tradesAPI.getCandles(selectedSymbol);
        const raw: any[] = res.data;
        console.log("RAW CANDLE DATA:", raw[0]);
        if (!raw.length) return;
        const bucketSec = intervalSeconds[interval];
        const buckets: Record<
          number,
          { o: number; h: number; l: number; c: number }
        > = {};
        for (const c of raw) {
          const key = Math.floor(c.time / bucketSec) * bucketSec;
          if (!buckets[key])
            buckets[key] = { o: c.open, h: c.high, l: c.low, c: c.close };
          else {
            buckets[key].h = Math.max(buckets[key].h, c.high);
            buckets[key].l = Math.min(buckets[key].l, c.low);
            buckets[key].c = c.close;
          }
        }
        const candleData = Object.entries(buckets)
          .sort(([a], [b]) => Number(a) - Number(b))
          .map(([time, v]) => ({
            time: Number(time) as UTCTimestamp,
            open: v.o,
            high: v.h,
            low: v.l,
            close: v.c,
          }));
        const lineData = candleData.map((c) => ({
          time: c.time as UTCTimestamp,
          value: c.close,
        }));
        candleSeries.current?.setData(candleData);
        lineSeries.current?.setData(lineData);
        const now = Math.floor(Date.now() / 1000);
        chartInst.current?.timeScale().setVisibleRange({
          from: (now - 600) as UTCTimestamp,  // 10 mins ago
          to: (now + 60) as UTCTimestamp,     // 1 min ahead
        });
      } catch {
        console.log("No candle data yet");
      }
    };
    load();
  }, [selectedSymbol, interval]);

  // Live update on new trade
  useEffect(() => {
    if (lastPrice <= 0) return;
    const dir = lastPrice >= prevPrice.current ? "up" : "down";
    setPriceDir(dir);
    prevPrice.current = lastPrice;
    const bucketSec = intervalSeconds[interval];
    const bucketTime = Math.floor(Date.now() / 1000 / bucketSec) * bucketSec;
    if (!bucketOpen.current[bucketTime])
      bucketOpen.current[bucketTime] = lastPrice;
    const open = bucketOpen.current[bucketTime];

    try {
      // Only update if we have existing data loaded
      if (prevPrice.current > 0) {
        candleSeries.current?.update({
          time: bucketTime as UTCTimestamp,
          open,
          high: Math.max(open, lastPrice) + 0.01, 
          low: Math.min(open, lastPrice) - 0.01,
          close: lastPrice,
        });
        lineSeries.current?.update({
          time: Math.floor(Date.now() / 1000) as UTCTimestamp,
          value: lastPrice,
        });
      }
    } catch (e) {
      console.warn("Chart update error:", e);
    }
  }, [lastPrice, interval]);

  useEffect(() => {
    const color = priceDir === "up" ? "#22c55e" : "#ef4444";
    const topColor =
      priceDir === "up" ? "rgba(34,197,94,0.2)" : "rgba(239,68,68,0.2)";
    lineSeries.current?.applyOptions({
      lineColor: color,
      topColor: topColor,
      bottomColor: "rgba(0,0,0,0)",
    });
  }, [priceDir]);

  return (
    <div className="bg-[#0f172a] flex flex-col h-full min-h-0">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-[#1e293b] flex-wrap gap-2">
        <div className="flex items-baseline gap-2">
          <span className="text-green-400 font-bold text-xl font-display">
            $
            {lastPrice > 0
              ? lastPrice.toLocaleString(undefined, {
                  minimumFractionDigits: 2,
                })
              : "---"}
          </span>
          <span className="text-xs text-[#64748b]">{selectedSymbol}</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex border border-[#334155] rounded overflow-hidden">
            {(["candle", "line"] as const).map((t) => (
              <button
                key={t}
                onClick={() => setChartType(t)}
                className={`px-2 py-1 text-xs transition-all capitalize ${chartType === t ? "bg-primary text-white" : "text-[#64748b] hover:text-white"}`}
              >
                {t === "candle" ? "🕯 Candles" : "📈 Line"}
              </button>
            ))}
          </div>
          <div className="flex gap-1">
            {(['1m', '15m', '1H', '4H', '1D'] as Interval[]).map((t) => (
              <button
                key={t}
                onClick={() => setIntervalVal(t)}
                className={`px-2 py-1 text-xs rounded transition-all ${interval === t ? "bg-[#1e293b] text-primary font-semibold" : "text-[#64748b] hover:text-white hover:bg-[#1e293b]"}`}
              >
                {t}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="relative flex-1 min-h-0">
        <div ref={chartRef} className="absolute inset-0" />
        {lastPrice === 0 && (
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
            <div className="text-5xl mb-3 opacity-20">📊</div>
            <p className="text-[#475569] text-sm font-medium">
              No chart data yet
            </p>
            <p className="text-[#334155] text-xs mt-1">
              Place matching buy & sell orders to see candlesticks
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
