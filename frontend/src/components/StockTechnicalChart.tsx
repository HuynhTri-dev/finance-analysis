/**
 * @file StockTechnicalChart.tsx
 * @description Advanced financial technical analysis chart utilizing Recharts.
 * Features cursor-anchored zoom & trackpad horizontal pan, granular price step axes (0.5k / 1.0k),
 * high-performance Japanese Candlesticks, volume overlays, MA20/MA50 overlays, and a synced RSI pane.
 */

"use client";

import React, { useState, useEffect, useRef, useMemo } from "react";
import { format } from "date-fns";
import { BarChart3, RefreshCw, ZoomIn, ZoomOut, RotateCcw, TrendingUp } from "lucide-react";
import {
  ComposedChart,
  Line,
  Bar,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  ReferenceLine,
} from "recharts";

export interface StockTechnicalChartProps {
  chartRecords: any[];
  loadingDetail: boolean;
  selectedTimeframe: string;
  onTimeframeChange: (timeframe: string) => void;
  showMAs: boolean;
  onToggleMAs: () => void;
}

/**
 * Custom Candlestick shape renderer for Recharts Bar.
 * Draws the wick (high to low) and body (open to close) for each trading record.
 */
const CandlestickShape = (props: any) => {
  const { x, y, width, height, payload } = props;
  if (!payload) return null;

  const { open, close, high, low } = payload;
  if (open === undefined || close === undefined || high === undefined || low === undefined) {
    return null;
  }

  const isUp = close >= open;
  const color = isUp ? "#22c55e" : "#ef4444"; // Green for gain, Red for loss

  const priceDiff = Math.abs(close - open);
  // Scale factor (pixels per unit of price)
  // If priceDiff is 0 (Doji), use a fallback or default scale
  const scaleFactor = priceDiff > 0 ? height / priceDiff : 1.0;

  // Body top and bottom coordinates
  const yOpen = isUp ? y + height : y;
  const yClose = isUp ? y : y + height;

  // Wick coordinates (higher price has smaller Y coordinate in SVG)
  const yHigh = yOpen - (high - open) * scaleFactor;
  const yLow = yOpen - (low - open) * scaleFactor;

  const centerX = x + width / 2;

  return (
    <g>
      {/* Wick / Shadow (High to Low) */}
      <line
        x1={centerX}
        y1={yHigh}
        x2={centerX}
        y2={yLow}
        stroke={color}
        strokeWidth={1.5}
      />
      {/* Real Body (Open to Close) */}
      <rect
        x={x}
        y={y}
        width={width}
        height={Math.max(height, 1)}
        fill={color}
        stroke={color}
        strokeWidth={1}
      />
    </g>
  );
};

export const StockTechnicalChart: React.FC<StockTechnicalChartProps> = ({
  chartRecords,
  loadingDetail,
  selectedTimeframe,
  onTimeframeChange,
  showMAs,
  onToggleMAs,
}) => {
  const [showBB, setShowBB] = useState<boolean>(false);
  const [viewRange, setViewRange] = useState<{ start: number; end: number } | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const isDraggingRef = useRef(false);
  const dragStartXRef = useRef(0);
  const dragRangeStartRef = useRef<{ start: number; end: number }>({ start: 0, end: 0 });

  // Reset zoom view range whenever timeframe or symbol data changes
  useEffect(() => {
    setViewRange(null);
  }, [selectedTimeframe, chartRecords]);

  const totalLen = chartRecords?.length || 0;
  const currentStart = viewRange ? viewRange.start : 0;
  const currentEnd = viewRange ? viewRange.end : totalLen;
  const currentLen = Math.max(1, currentEnd - currentStart);

  // Sliced data currently in viewport
  const visibleRecords = useMemo(() => {
    if (!chartRecords || chartRecords.length === 0) return [];
    return chartRecords.slice(currentStart, currentEnd);
  }, [chartRecords, currentStart, currentEnd]);

  const isZoomed = viewRange !== null && (viewRange.start > 0 || viewRange.end < totalLen);

  /**
   * Smart Price Ticks generator for Y-Axis with clean 0.5k / 1.0k / 2.0k intervals
   */
  const { priceTicks, priceDomain } = useMemo(() => {
    if (!visibleRecords || visibleRecords.length === 0) {
      return { priceTicks: undefined, priceDomain: ["auto", "auto"] as [any, any] };
    }

    const prices: number[] = [];
    visibleRecords.forEach((r) => {
      if (typeof r.low === "number" && !isNaN(r.low)) prices.push(r.low);
      if (typeof r.high === "number" && !isNaN(r.high)) prices.push(r.high);
      if (typeof r.open === "number" && !isNaN(r.open)) prices.push(r.open);
      if (typeof r.close === "number" && !isNaN(r.close)) prices.push(r.close);
      if (showMAs) {
        if (typeof r.ma20 === "number" && !isNaN(r.ma20)) prices.push(r.ma20);
        if (typeof r.ma50 === "number" && !isNaN(r.ma50)) prices.push(r.ma50);
      }
      if (showBB) {
        if (typeof r.bb_lower === "number" && !isNaN(r.bb_lower)) prices.push(r.bb_lower);
        if (typeof r.bb_upper === "number" && !isNaN(r.bb_upper)) prices.push(r.bb_upper);
      }
    });

    if (prices.length === 0) {
      return { priceTicks: undefined, priceDomain: ["auto", "auto"] as [any, any] };
    }

    const minP = Math.min(...prices);
    const maxP = Math.max(...prices);
    const diff = maxP - minP;

    // Pick granular step based on price level & range (in VND or thousands)
    let step = 1000;
    if (minP > 500) {
      // Prices in raw VND (e.g. 72,000)
      if (diff <= 1500) step = 200;
      else if (diff <= 3500) step = 500;
      else if (diff <= 8000) step = 1000;
      else if (diff <= 20000) step = 2000;
      else if (diff <= 50000) step = 5000;
      else step = 10000;
    } else {
      // Prices in thousands (e.g. 72.0)
      if (diff <= 1.5) step = 0.2;
      else if (diff <= 3.5) step = 0.5;
      else if (diff <= 8.0) step = 1.0;
      else if (diff <= 20.0) step = 2.0;
      else step = 5.0;
    }

    const startTick = Math.floor(minP / step) * step;
    const endTick = Math.ceil(maxP / step) * step;
    const ticks: number[] = [];
    for (let t = startTick; t <= endTick + step * 0.01; t += step) {
      ticks.push(Number(t.toFixed(2)));
    }

    return {
      priceTicks: ticks,
      priceDomain: [startTick, endTick] as [number, number],
    };
  }, [visibleRecords, showMAs, showBB]);

  /**
   * Zooms in anchored to center
   */
  const handleZoomIn = () => {
    if (totalLen <= 6) return;
    const newLen = Math.max(8, Math.round(currentLen * 0.8));
    const pivot = currentStart + currentLen / 2;
    let newStart = Math.max(0, Math.round(pivot - newLen / 2));
    let newEnd = newStart + newLen;
    if (newEnd > totalLen) {
      newStart = Math.max(0, totalLen - newLen);
      newEnd = totalLen;
    }
    setViewRange({ start: newStart, end: newEnd });
  };

  /**
   * Zooms out anchored to center
   */
  const handleZoomOut = () => {
    if (totalLen <= 6) return;
    const newLen = Math.round(currentLen * 1.25);
    if (newLen >= totalLen) {
      setViewRange(null);
      return;
    }
    const pivot = currentStart + currentLen / 2;
    let newStart = Math.max(0, Math.round(pivot - newLen / 2));
    let newEnd = newStart + newLen;
    if (newEnd > totalLen) {
      newStart = Math.max(0, totalLen - newLen);
      newEnd = totalLen;
    }
    setViewRange({ start: newStart, end: newEnd });
  };

  /**
   * Resets zoom to full view
   */
  const handleResetZoom = () => {
    setViewRange(null);
  };

  /**
   * Cursor-anchored Wheel zoom & 2-finger Trackpad swipe pan
   */
  const handleWheel = (e: React.WheelEvent) => {
    if (!containerRef.current || totalLen <= 6) return;

    const rect = containerRef.current.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const ratio = Math.max(0.02, Math.min(0.98, mouseX / rect.width));

    // Horizontal 2-finger swipe on trackpad -> Pan
    if (Math.abs(e.deltaX) > Math.abs(e.deltaY) && Math.abs(e.deltaX) > 2) {
      const panDelta = Math.round((e.deltaX / rect.width) * currentLen * 0.8);
      if (panDelta !== 0) {
        let newStart = currentStart + panDelta;
        let newEnd = currentEnd + panDelta;
        if (newStart < 0) {
          newEnd -= newStart;
          newStart = 0;
        }
        if (newEnd > totalLen) {
          newStart -= newEnd - totalLen;
          newEnd = totalLen;
          newStart = Math.max(0, newStart);
        }
        setViewRange({ start: newStart, end: newEnd });
      }
      return;
    }

    // Vertical wheel / Pinch -> Zoom anchored at cursor position
    if (Math.abs(e.deltaY) > 2) {
      const zoomFactor = e.deltaY < 0 ? 0.82 : 1.22;
      const newLen = Math.round(currentLen * zoomFactor);
      const minLen = 8;
      const clampedLen = Math.max(minLen, Math.min(totalLen, newLen));

      if (clampedLen >= totalLen) {
        setViewRange(null);
        return;
      }

      const pivotIndex = currentStart + ratio * currentLen;
      let newStart = Math.round(pivotIndex - ratio * clampedLen);
      let newEnd = newStart + clampedLen;

      if (newStart < 0) {
        newEnd -= newStart;
        newStart = 0;
      }
      if (newEnd > totalLen) {
        newStart -= newEnd - totalLen;
        newEnd = totalLen;
        newStart = Math.max(0, newStart);
      }

      setViewRange({ start: newStart, end: newEnd });
    }
  };

  /**
   * Drag to pan handlers
   */
  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button !== 0 || totalLen <= 6) return;
    isDraggingRef.current = true;
    dragStartXRef.current = e.clientX;
    dragRangeStartRef.current = { start: currentStart, end: currentEnd };
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDraggingRef.current || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const deltaX = e.clientX - dragStartXRef.current;
    const shift = Math.round((deltaX / rect.width) * currentLen);

    if (shift !== 0) {
      const orig = dragRangeStartRef.current;
      let newStart = orig.start - shift;
      let newEnd = orig.end - shift;
      if (newStart < 0) {
        newEnd -= newStart;
        newStart = 0;
      }
      if (newEnd > totalLen) {
        newStart -= newEnd - totalLen;
        newEnd = totalLen;
        newStart = Math.max(0, newStart);
      }
      setViewRange({ start: newStart, end: newEnd });
    }
  };

  const handleMouseUp = () => {
    isDraggingRef.current = false;
  };

  return (
    <div className="bg-[#161B22] border border-[#30363D] rounded-xl p-4 sm:p-5 shadow-sm space-y-4 select-none">
      {/* Header controls bar */}
      <div className="flex flex-wrap items-center justify-between pb-3 border-b border-[#30363D]/80 gap-3">
        <div className="flex items-center space-x-2 sm:space-x-3">
          <div className="flex items-center space-x-1.5 text-xs font-semibold text-gray-200">
            <BarChart3 size={16} className="text-blue-400" />
          </div>

          <button
            onClick={onToggleMAs}
            className={`text-[11px] px-2 py-0.5 rounded border transition-colors ${showMAs
              ? "bg-blue-500/20 text-blue-400 border-blue-500/40"
              : "bg-[#21262D] text-gray-400 border-[#30363D]"
              }`}
          >
            MA20 / MA50
          </button>

          <button
            onClick={() => setShowBB(!showBB)}
            className={`text-[11px] px-2 py-0.5 rounded border transition-colors ${showBB
              ? "bg-blue-500/20 text-blue-400 border-blue-500/40"
              : "bg-[#21262D] text-gray-400 border-[#30363D]"
              }`}
          >
            Dải Bollinger
          </button>
        </div>

        <div className="flex items-center space-x-2">
          {/* Zoom Controls & Status */}
          <div className="flex items-center space-x-1 bg-[#0D1117] p-1 rounded-lg border border-[#30363D]">
            <button
              onClick={handleZoomIn}
              title="Phóng to (Cuộn chuột lên tại vị trí trỏ chuột)"
              className="p-1 text-gray-400 hover:text-blue-400 hover:bg-[#21262D] rounded transition-colors"
            >
              <ZoomIn size={14} />
            </button>
            <button
              onClick={handleZoomOut}
              title="Thu nhỏ (Cuộn chuột xuống)"
              className="p-1 text-gray-400 hover:text-blue-400 hover:bg-[#21262D] rounded transition-colors"
            >
              <ZoomOut size={14} />
            </button>
            <button
              onClick={handleResetZoom}
              title={isZoomed ? "Đặt lại khung nhìn mặc định" : "Khung nhìn 100%"}
              disabled={!isZoomed}
              className={`p-1 rounded transition-colors ${isZoomed
                ? "text-amber-400 hover:bg-[#21262D]"
                : "text-gray-600 cursor-not-allowed"
                }`}
            >
              <RotateCcw size={14} />
            </button>
          </div>

          {/* Timeframe Buttons */}
          <div className="flex items-center space-x-1 bg-[#0D1117] p-1 rounded-lg border border-[#30363D]">
            {["1M", "3M", "6M", "1Y", "3Y"].map((tf) => (
              <button
                key={tf}
                onClick={() => onTimeframeChange(tf)}
                className={`px-2.5 sm:px-3 py-1 text-xs font-semibold rounded-md transition-all ${selectedTimeframe === tf
                  ? "bg-blue-600 text-white shadow"
                  : "text-gray-400 hover:text-gray-200 hover:bg-[#21262D]"
                  }`}
              >
                {tf}
              </button>
            ))}
          </div>
        </div>
      </div>

      {loadingDetail ? (
        <div className="flex items-center justify-center h-[380px] text-xs text-gray-400">
          <RefreshCw className="animate-spin mr-2" size={16} />
          Đang cập nhật biểu đồ...
        </div>
      ) : chartRecords && chartRecords.length > 0 ? (
        <div
          ref={containerRef}
          className="space-y-3 cursor-crosshair"
          onWheel={handleWheel}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
        >
          {/* Pane 1: Candlestick Price + MA + Volume Chart */}
          <div className="h-[330px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart
                data={visibleRecords}
                syncId="stockChart"
                margin={{ top: 10, right: 0, left: 0, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#21262D" vertical={false} />
                <XAxis
                  dataKey="time"
                  hide
                  padding={{ left: 10, right: 10 }}
                />
                <YAxis
                  yAxisId="price"
                  orientation="right"
                  domain={priceDomain}
                  ticks={priceTicks}
                  stroke="#6E7681"
                  tick={{ fontSize: 11, fill: "#9CA3AF" }}
                  axisLine={{ stroke: "#30363D" }}
                  tickLine={{ stroke: "#30363D" }}
                  width={52}
                  tickFormatter={(val) => {
                    if (val >= 1000) {
                      const inK = val / 1000;
                      return inK % 1 === 0 ? `${inK}` : `${inK.toFixed(1)}`;
                    }
                    return val % 1 === 0 ? `${val}` : `${val.toFixed(1)}`;
                  }}
                />
                <YAxis yAxisId="vol" orientation="right" domain={[0, "dataMax * 3.5"]} hide width={0} />

                <Tooltip
                  content={({ active, payload, label }) => {
                    if (active && payload && payload.length) {
                      const d = payload[0].payload;
                      return (
                        <div className="bg-[#161B22] border border-[#30363D] p-3 rounded-lg shadow-xl text-xs space-y-1 z-50">
                          <div className="font-bold text-gray-200 border-b border-[#30363D] pb-1">
                            {d.time ? format(new Date(d.time), "dd/MM/yyyy") : label}
                          </div>
                          <div className="grid grid-cols-2 gap-x-4 gap-y-0.5 text-[11px] pt-1">
                            <span className="text-gray-400">Đóng cửa:</span>
                            <span className="font-bold text-emerald-400 text-right">
                              {d.close?.toLocaleString()}
                            </span>
                            <span className="text-gray-400">Mở cửa:</span>
                            <span className="text-gray-200 text-right">{d.open?.toLocaleString()}</span>
                            <span className="text-gray-400">Cao nhất:</span>
                            <span className="text-emerald-300 text-right">{d.high?.toLocaleString()}</span>
                            <span className="text-gray-400">Thấp nhất:</span>
                            <span className="text-rose-300 text-right">{d.low?.toLocaleString()}</span>
                            <span className="text-gray-400">Khối lượng:</span>
                            <span className="text-blue-400 text-right">{d.volume?.toLocaleString()}</span>
                            {d.ma20 && (
                              <>
                                <span className="text-amber-400">MA20:</span>
                                <span className="text-amber-300 text-right">
                                  {d.ma20?.toLocaleString()}
                                </span>
                              </>
                            )}
                            {d.ma50 && (
                              <>
                                <span className="text-purple-400">MA50:</span>
                                <span className="text-purple-300 text-right">
                                  {d.ma50?.toLocaleString()}
                                </span>
                              </>
                            )}
                            {d.rsi && (
                              <>
                                <span className="text-pink-400">RSI (14):</span>
                                <span className="text-pink-300 text-right">{d.rsi}</span>
                              </>
                            )}
                            {d.bb_upper && d.bb_lower && (
                              <>
                                <span className="text-blue-400">BB Upper:</span>
                                <span className="text-blue-300 text-right">{d.bb_upper?.toLocaleString()}</span>
                                <span className="text-blue-400">BB Lower:</span>
                                <span className="text-blue-300 text-right">{d.bb_lower?.toLocaleString()}</span>
                              </>
                            )}
                          </div>
                        </div>
                      );
                    }
                    return null;
                  }}
                />

                {/* Current Price Dashed Reference Line */}
                {visibleRecords[visibleRecords.length - 1]?.close !== undefined && (
                  <ReferenceLine
                    yAxisId="price"
                    y={visibleRecords[visibleRecords.length - 1].close}
                    stroke={
                      (visibleRecords[visibleRecords.length - 1].close >=
                        (visibleRecords[visibleRecords.length - 1].open || 0))
                        ? "#22c55e"
                        : "#ef4444"
                    }
                    strokeDasharray="2 2"
                    strokeWidth={1}
                    opacity={0.8}
                  />
                )}

                {/* Volume Bar */}
                <Bar
                  yAxisId="vol"
                  dataKey="volume"
                  fill="#238636"
                  opacity={0.25}
                  radius={[2, 2, 0, 0]}
                  maxBarSize={18}
                />

                {/* Moving Average Overlays */}
                {showMAs && (
                  <>
                    <Line
                      yAxisId="price"
                      type="monotone"
                      dataKey="ma20"
                      stroke="#F59E0B"
                      dot={false}
                      strokeWidth={1.5}
                      name="MA20"
                    />
                    <Line
                      yAxisId="price"
                      type="monotone"
                      dataKey="ma50"
                      stroke="#8B5CF6"
                      dot={false}
                      strokeWidth={1.5}
                      name="MA50"
                    />
                  </>
                )}

                {/* Bollinger Bands Overlay */}
                {showBB && (
                  <>
                    <Area
                      yAxisId="price"
                      type="monotone"
                      dataKey={(d: any) => [d.bb_lower, d.bb_upper]}
                      stroke="none"
                      fill="#2196F3"
                      fillOpacity={0.06}
                      name="Dải Bollinger"
                    />
                    <Line
                      yAxisId="price"
                      type="monotone"
                      dataKey="bb_upper"
                      stroke="#2196F3"
                      strokeWidth={1}
                      strokeDasharray="3 3"
                      dot={false}
                      name="BB Upper"
                    />
                    <Line
                      yAxisId="price"
                      type="monotone"
                      dataKey="bb_lower"
                      stroke="#2196F3"
                      strokeWidth={1}
                      strokeDasharray="3 3"
                      dot={false}
                      name="BB Lower"
                    />
                  </>
                )}

                {/* Candlestick Body & Wicks */}
                <Bar
                  yAxisId="price"
                  dataKey={(d: any) => [d.open, d.close]}
                  shape={<CandlestickShape />}
                  name="Candlestick"
                  maxBarSize={16}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>

          {/* Pane 2: Synced RSI Line Chart with Clean Date X-Axis */}
          <div className="h-[110px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart
                data={visibleRecords}
                syncId="stockChart"
                margin={{ top: 5, right: 0, left: 0, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#21262D" vertical={false} />
                <XAxis
                  dataKey="time"
                  tickFormatter={(timeStr) => {
                    try {
                      const d = new Date(timeStr);
                      if (selectedTimeframe === "3Y" || selectedTimeframe === "1Y") {
                        return format(d, "MM/yy");
                      }
                      return format(d, "dd/MM");
                    } catch {
                      return timeStr;
                    }
                  }}
                  stroke="#6E7681"
                  tick={{ fontSize: 10, fill: "#9CA3AF" }}
                  axisLine={{ stroke: "#30363D" }}
                  tickLine={{ stroke: "#30363D" }}
                  minTickGap={35}
                  padding={{ left: 10, right: 10 }}
                />
                <YAxis
                  yAxisId="rsiAxis"
                  orientation="right"
                  domain={[0, 100]}
                  ticks={[30, 50, 70]}
                  stroke="#6E7681"
                  tick={{ fontSize: 9, fill: "#9CA3AF" }}
                  axisLine={{ stroke: "#30363D" }}
                  tickLine={{ stroke: "#30363D" }}
                  width={52}
                />

                {/* Boundaries Reference Lines for Overbought (70) and Oversold (30) */}
                <ReferenceLine yAxisId="rsiAxis" y={70} stroke="#ef4444" strokeDasharray="3 3" opacity={0.5} />
                <ReferenceLine yAxisId="rsiAxis" y={30} stroke="#22c55e" strokeDasharray="3 3" opacity={0.5} />
                <ReferenceLine yAxisId="rsiAxis" y={50} stroke="#6E7681" strokeDasharray="3 3" opacity={0.3} />

                {/* RSI Line */}
                <Line
                  yAxisId="rsiAxis"
                  type="monotone"
                  dataKey="rsi"
                  stroke="#ec4899"
                  dot={false}
                  strokeWidth={1.5}
                  name="RSI"
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center h-[380px] text-gray-500">
          <TrendingUp size={32} className="mb-2 text-gray-600 opacity-50" />
          <p className="text-xs">Không có dữ liệu biểu đồ cho mã này</p>
        </div>
      )}
    </div>
  );
};
