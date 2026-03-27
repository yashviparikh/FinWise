import React, { useEffect, useMemo, useState } from "react";
import axios from "axios";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceDot,
  ReferenceLine,
} from "recharts";
import "./TradeSimulator.css";

const RANGE_OPTIONS = ["3M", "6M", "1Y"];

function formatInr(value) {
  const n = Number(value || 0);
  return n.toLocaleString("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  });
}

export default function TradeSimulator() {
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [selectedStock, setSelectedStock] = useState(null);
  const [rangeKey, setRangeKey] = useState("6M");
  const [history, setHistory] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [historyError, setHistoryError] = useState("");

  const [activeAction, setActiveAction] = useState("BUY");
  const [quantity, setQuantity] = useState("1");
  const [buyPoint, setBuyPoint] = useState(null);
  const [sellPoint, setSellPoint] = useState(null);
  const [hoverPoint, setHoverPoint] = useState(null);
  const [chartActionError, setChartActionError] = useState("");

  const [simLoading, setSimLoading] = useState(false);
  const [simError, setSimError] = useState("");
  const [simResult, setSimResult] = useState(null);

  useEffect(() => {
    const term = (query || "").trim();
    if (term.length < 1) {
      setSuggestions([]);
      return;
    }

    const t = setTimeout(async () => {
      try {
        const res = await axios.get(`http://127.0.0.1:5000/autocomplete?q=${encodeURIComponent(term)}`);
        const rows = Array.isArray(res.data) ? res.data : [];
        setSuggestions(
          rows.map((r) => ({
            symbol: String(r.SYMBOL || "").toUpperCase(),
            name: r["NAME OF COMPANY"] || "",
          }))
        );
      } catch (e) {
        setSuggestions([]);
      }
    }, 200);

    return () => clearTimeout(t);
  }, [query]);

  const fetchHistory = async (symbol, nextRange) => {
    if (!symbol) return;
    setLoadingHistory(true);
    setHistoryError("");
    try {
      const res = await axios.get(
        `http://127.0.0.1:5000/api/simulate-trade/history?symbol=${encodeURIComponent(symbol)}&range=${nextRange}`
      );
      const series = Array.isArray(res.data?.series) ? res.data.series : [];
      setHistory(series);
      setBuyPoint(null);
      setSellPoint(null);
      setHoverPoint(null);
      setChartActionError("");
      setSimResult(null);
      setSimError("");
      setActiveAction("BUY");
    } catch (e) {
      setHistory([]);
      setHistoryError(e?.response?.data?.error || "Could not load historical chart for this symbol.");
    } finally {
      setLoadingHistory(false);
    }
  };

  const onSelectStock = async (stock) => {
    setSelectedStock(stock);
    setQuery(stock.symbol);
    setSuggestions([]);
    await fetchHistory(stock.symbol, rangeKey);
  };

  const applyPointSelection = (point) => {
    if (!point) {
      setChartActionError("Hover a point on the line, then click.");
      return false;
    }

    setChartActionError("");
    setSimError("");
    setSimResult(null);

    if (activeAction === "BUY") {
      setBuyPoint(point);
      if (sellPoint && sellPoint.date <= point.date) {
        setSellPoint(null);
      }
      setActiveAction("SELL");
      return true;
    }

    if (!buyPoint) {
      setChartActionError("Set BUY first. SELL is enabled only after BUY is selected.");
      return false;
    }
    if (point.date <= buyPoint.date) {
      setChartActionError("SELL date must be after BUY date.");
      return false;
    }
    setSellPoint(point);
    return true;
  };

  const canSimulate = Boolean(
    selectedStock && buyPoint && sellPoint && Number(quantity) > 0
  );

  const runSimulation = async () => {
    if (!canSimulate) return;

    setSimLoading(true);
    setSimError("");
    try {
      const payload = {
        symbol: selectedStock.symbol,
        buy_date: buyPoint.date,
        sell_date: sellPoint.date,
        quantity: Number(quantity),
      };
      const res = await axios.post("http://127.0.0.1:5000/api/simulate-trade", payload);
      setSimResult(res.data);
    } catch (e) {
      setSimResult(null);
      setSimError(e?.response?.data?.error || "Simulation failed. Please try different dates.");
    } finally {
      setSimLoading(false);
    }
  };

  const performanceTone = useMemo(() => {
    const rp = Number(simResult?.return_percent || 0);
    return rp >= 0 ? "pos" : "neg";
  }, [simResult]);

  return (
    <div className="sim-wrap">
      <header className="sim-head">
        <h1>Trade Simulator</h1>
        <p>Pick a stock, hover to inspect price/date, click to set BUY/SELL, and simulate by quantity.</p>
      </header>

      <section className="sim-card sim-controls">
        <div className="sim-field">
          <label>Stock</label>
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search stock (e.g. RELIANCE)"
          />
          {suggestions.length > 0 && (
            <div className="sim-suggestions">
              {suggestions.map((s) => (
                <button key={s.symbol} onClick={() => onSelectStock(s)} className="sim-suggestion-item">
                  <strong>{s.symbol}</strong>
                  <span>{s.name}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="sim-field">
          <label>Time Range</label>
          <div className="sim-range-row">
            {RANGE_OPTIONS.map((r) => (
              <button
                key={r}
                className={`sim-chip ${rangeKey === r ? "active" : ""}`}
                onClick={() => {
                  setRangeKey(r);
                  if (selectedStock?.symbol) fetchHistory(selectedStock.symbol, r);
                }}
              >
                {r}
              </button>
            ))}
          </div>
        </div>

        <div className="sim-field">
          <label>Quantity</label>
          <input
            type="number"
            min="1"
            step="1"
            value={quantity}
            onChange={(e) => setQuantity(e.target.value.replace(/^0+/, "") || "")}
          />
        </div>

        <div className="sim-field">
          <label>Action Mode</label>
          <div className="sim-action-row">
            <button
              className={`sim-btn ${activeAction === "BUY" ? "buy" : ""}`}
              onClick={() => setActiveAction("BUY")}
            >
              BUY
            </button>
            <button
              className={`sim-btn ${activeAction === "SELL" ? "sell" : ""}`}
              onClick={() => setActiveAction("SELL")}
              disabled={!buyPoint}
              title={!buyPoint ? "Select BUY point first" : "Set SELL point"}
            >
              SELL
            </button>
          </div>
        </div>
      </section>

      <section className="sim-card sim-chart-card">
        <div className="sim-chart-head">
          <h2>
            {selectedStock?.symbol || "Select a stock"} {selectedStock?.name ? `- ${selectedStock.name}` : ""}
          </h2>
          <div className="sim-points">
            <span>BUY: {buyPoint?.date || "-"}</span>
            <span>SELL: {sellPoint?.date || "-"}</span>
          </div>
        </div>

        <div className="sim-helper">
          {hoverPoint
            ? `Click to set ${activeAction} at ${formatInr(hoverPoint.close)} on ${hoverPoint.date}`
            : `Hover over chart, then left or right click to set ${activeAction}`}
        </div>
        {chartActionError && <div className="sim-chart-error">{chartActionError}</div>}

        {loadingHistory ? (
          <div className="sim-empty">Loading chart...</div>
        ) : historyError ? (
          <div className="sim-empty error">{historyError}</div>
        ) : history.length === 0 ? (
          <div className="sim-empty">Select a stock to view historical chart.</div>
        ) : (
          <div
            className="sim-chart-wrap"
            onMouseUpCapture={(e) => {
              // Left click anywhere on chart area commits current hovered point.
              if (e.button !== 0) return;
              applyPointSelection(hoverPoint);
            }}
            onContextMenuCapture={(e) => {
              // Right click support: prevent browser menu and commit hovered point.
              e.preventDefault();
              applyPointSelection(hoverPoint);
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                applyPointSelection(hoverPoint);
              }
            }}
            role="button"
            tabIndex={0}
          >
            <ResponsiveContainer width="100%" height={400}>
  <LineChart
    data={history}
    onMouseMove={(evt) => setHoverPoint(evt?.activePayload?.[0]?.payload || null)}
    onMouseLeave={() => setHoverPoint(null)}
  >
    <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
    <XAxis dataKey="date" tick={{ fill: "#9fb0bf", fontSize: 12 }} minTickGap={24} />
    <YAxis
      tick={{ fill: "#9fb0bf", fontSize: 12 }}
      tickFormatter={(v) => `INR ${Number(v).toFixed(0)}`}
    />
    <Tooltip
      formatter={(value) => [formatInr(value), "Close"]}
      labelFormatter={(label) => `Date: ${label}`}
      wrapperStyle={{ pointerEvents: "none" }}
    />

    {/* Main Line */}
    <Line
      type="monotone"
      dataKey="close"
      stroke="#4ecbff"
      dot={false} // hide default dots, we will overlay ReferenceDots
      strokeWidth={2}
    />

    {/* Hover line */}
    {hoverPoint && (
      <ReferenceLine
        x={hoverPoint.date}
        stroke="#4ecbff"
        strokeDasharray="4 4"
        strokeOpacity={0.5}
      />
    )}

    {/* BUY / SELL points */}
    {buyPoint && (
      <ReferenceDot
        x={buyPoint.date}
        y={buyPoint.close}
        r={6}
        fill="#1fd07d"
        stroke="#0d301f"
        label={{ value: "B", position: "top", fill: "#1fd07d" }}
      />
    )}
    {sellPoint && (
      <ReferenceDot
        x={sellPoint.date}
        y={sellPoint.close}
        r={6}
        fill="#ff6b6b"
        stroke="#3a1010"
        label={{ value: "S", position: "top", fill: "#ff6b6b" }}
      />
    )}

    {/* Invisible clickable overlay for all points */}
    {history.map((p) => (
      <ReferenceDot
        key={p.date}
        x={p.date}
        y={p.close}
        r={10} // large clickable area
        fill="transparent"
        onClick={() => applyPointSelection(p)}
        cursor="pointer"
      />
    ))}
  </LineChart>
</ResponsiveContainer>
          </div>
        )}
      </section>

      <section className="sim-card sim-result">
        <button className="sim-run" disabled={!canSimulate || simLoading} onClick={runSimulation}>
          {simLoading ? "Simulating..." : "Run Simulation"}
        </button>
        {simError && <div className="sim-msg error">{simError}</div>}

        {simResult && (
          <div className="sim-output">
            <div>
              <span>Final Value</span>
              <strong>{formatInr(simResult.final_value)}</strong>
            </div>
            <div>
              <span>Return</span>
              <strong className={performanceTone}>
                {Number(simResult.return_percent) >= 0 ? "+" : ""}
                {Number(simResult.return_percent).toFixed(2)}%
              </strong>
            </div>
            <div>
              <span>Buy/Sell</span>
              <strong>
                {simResult.buy_date} -&gt; {simResult.sell_date}
              </strong>
            </div>
            <div>
              <span>Quantity</span>
              <strong>{Number(simResult.quantity ?? quantity).toLocaleString("en-IN")}</strong>
            </div>
            <div>
              <span>Invested</span>
              <strong>{formatInr(simResult.invested_amount)}</strong>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
