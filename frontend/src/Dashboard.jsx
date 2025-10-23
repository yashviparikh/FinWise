import React, { useState, useEffect } from "react";
import { saveAs } from "file-saver";

import axios from "axios";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  PieChart,
  Pie,
  Cell,
  Sector,
} from "recharts";
import { motion } from "framer-motion";
import { FiPieChart, FiActivity, FiDownload } from "react-icons/fi";
import { BsWallet2 } from "react-icons/bs";
import { MdInsights } from "react-icons/md";
import "./Dashboard.css";
function exportCSV(data) {
  const headers = ["Company", "Stock", "Quantity", "Avg Buy Price", "Invested", "LTP", "Now Value", "P/L"];
  const rows = data.map(p => [
    p.companyname,
    p.stockname,
    p.totalquantity,
    p.averagebuyprice,
    p.totalinvested,
    p.ltp,
    p.nowvalue,
    p.profitorloss
  ]);

  let csv = headers.join(",") + "\n" + rows.map(r => r.join(",")).join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  saveAs(blob, "portfolio_export.csv");
}

export default function Dashboard() {
  const [wallet, setWallet] = useState(0);
  const [portfolio, setPortfolio] = useState([]);
  const [metrics, setMetrics] = useState({});
  const [sectorSplit, setSectorSplit] = useState([]);
  const [portfolioValueSeries, setPortfolioValueSeries] = useState([]);
  const [plSeries, setPlSeries] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [activePieIndex, setActivePieIndex] = useState(-1);

  const fmtCurrency = (n) =>
    (n ?? 0).toLocaleString("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 2,
    });

  const pieColors = [
    "#2ED3A3",
    "#7C8CFF",
    "#54C5FF",
    "#00E676",
    "#FDBA8C",
    "#FF6B6B",
    "#FFD27F",
  ];

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await axios.get("http://127.0.0.1:5000/dashboard/1"); // Replace '1' with dynamic user ID
       
        setWallet(res.data.wallet || 0);
        setPortfolio(res.data.portfolio || []);
        setMetrics(res.data.metrics || {});
        setPortfolioValueSeries(res.data.portfolio_value_trend || []);
        setPlSeries(res.data.profit_loss_trend || []);
        setTransactions(res.data.transactions || []);

        // ✅ Group companies into sectors
        const sectorData = {};
        (res.data.investment_split || []).forEach((s) => {
          const sector = s.sector || "Other"; // use sector if available
          if (!sectorData[sector]) {
            sectorData[sector] = 0;
          }
          sectorData[sector] += s.amount;
        });

        setSectorSplit(
          Object.entries(sectorData).map(([sector, value]) => ({
            name: sector,
            value,
          }))
        );
      } catch (err) {
        console.error("Error fetching dashboard data:", err);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 15000); // Poll every 15s
    return () => clearInterval(interval);
  }, []);

  function renderActiveShape(props) {
    const { cx, cy, innerRadius, outerRadius, startAngle, endAngle, fill } =
      props;
    return (
      <Sector
        cx={cx}
        cy={cy}
        innerRadius={innerRadius}
        outerRadius={outerRadius + 8}
        startAngle={startAngle}
        endAngle={endAngle}
        fill={fill}
      />
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="dash page-bg"
    >
      {/* Header */}
      <div className="dash__header">
        <div>
          <h1 className="dash__title">Dashboard</h1>
          <p className="dash__subtitle">
            Your trading overview and performance metrics
          </p>
        </div>
        <div className="header-tools">
          <div className="wallet-pill">
            <BsWallet2 />
            <span>
              Wallet: <strong>{fmtCurrency(wallet)}</strong>
            </span>
          </div>
          <button
            className="export-btn"
            onClick={() => exportCSV(portfolio)}
          >
            <FiDownload /> Quick Export
          </button>
          <button
            className="export-btn"
            onClick={() => window.open("http://127.0.0.1:5000/dashboard/1/export")}
          >
            <FiDownload /> Full Export
          </button>
        </div>

      </div>

      {/* Metric Cards */}
      <div className="grid grid--4">
        <MetricCard
          icon={<BsWallet2 />}
          label="Portfolio Value"
          value={fmtCurrency(
            portfolio.reduce((acc, p) => acc + p.nowvalue, 0)
          )}
          sub={`Holdings: ${portfolio.length}`}
        />
        <MetricCard
          icon={<MdInsights />}
          label="Progress"
          value={`${metrics.progress_score || 0}%`}
          sub={metrics.level || "—"}
        />
        <MetricCard
          icon={<FiPieChart />}
          label="Holdings"
          value={portfolio.length}
          sub="Active positions"
        />
        <MetricCard
          icon={<FiActivity />}
          label="Login Streak"
          value={`${metrics.login_streak || 0} days`}
          sub="Consistency"
        />
      </div>

      {/* Charts */}
      <div className="grid grid--2">
        <ChartCard title="Portfolio Value" tag="overview">
          <ResponsiveContainer width="100%" height={320}>
            <AreaChart data={portfolioValueSeries}>
              <CartesianGrid
                stroke="rgba(255,255,255,0.03)"
                vertical={false}
              />
              <XAxis dataKey="date" tick={{ fill: "#AAB8C7" }} />
              <YAxis
                tick={{ fill: "#AAB8C7" }}
                tickFormatter={(val) =>
                  fmtCurrency(val).replace("₹", "₹ ")
                }
              />
              <Tooltip
                formatter={(value) => [fmtCurrency(value), "Value"]}
              />
              <Area
                type="monotone"
                dataKey="value"
                stroke="#26E07F"
                fill="rgba(38,224,127,0.25)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Profit & Loss" tag="overview">
          <ResponsiveContainer width="100%" height={320}>
            <AreaChart data={plSeries}>
              <CartesianGrid
                stroke="rgba(255,255,255,0.03)"
                vertical={false}
              />
              <XAxis dataKey="date" tick={{ fill: "#AAB8C7" }} />
              <YAxis
                tick={{ fill: "#AAB8C7" }}
                tickFormatter={(val) =>
                  fmtCurrency(val).replace("₹", "₹ ")
                }
              />
              <Tooltip
                formatter={(value) => [fmtCurrency(value), "P&L"]}
              />
              <Area
                type="monotone"
                dataKey="profit_loss"
                stroke="#7C8CFF"
                fill="rgba(124,140,255,0.25)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* Lower row */}
      <div className="grid grid--3">
        {/* Top performers */}
        <Card title="Top Performers">
          {portfolio.length === 0 ? (
            <div className="empty">
              <div className="empty__icon">📈</div>
              <div>No holdings to display</div>
            </div>
          ) : (
            <div className="list-container">
              {[...portfolio]
                .sort((a, b) => b.profitorloss - a.profitorloss)
                .slice(0, 5)
                .map((p, i) => (
                  <div key={i} className="list-box">
                    <span className="list-title">{p.companyname}</span>
                    <span
                      className={
                        p.profitorloss >= 0
                          ? "text-green-400"
                          : "text-red-400"
                      }
                    >
                      {fmtCurrency(p.profitorloss)}
                    </span>
                  </div>
                ))}
            </div>
          )}
        </Card>

        {/* Investment Split by sector */}
        <Card title="Investment Split">
          {sectorSplit.length === 0 ? (
            <div className="empty">
              <div className="empty__icon">🥧</div>
              <div>No data to display</div>
            </div>
          ) : (
            <div className="pie-wrapper">
              <ResponsiveContainer width="100%" height={260}>
                <PieChart>
                  <Pie
                    data={sectorSplit}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    innerRadius={58}
                    outerRadius={110}
                    paddingAngle={4}
                    startAngle={90}
                    endAngle={-270}
                    activeIndex={activePieIndex}
                    activeShape={renderActiveShape}
                    onMouseEnter={(_, idx) => setActivePieIndex(idx)}
                    onMouseLeave={() => setActivePieIndex(-1)}
                  >
                    {sectorSplit.map((_, i) => (
                      <Cell
                        key={`cell-${i}`}
                        fill={pieColors[i % pieColors.length]}
                      />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>

              {/* Legend */}
              <div className="legend legend-grid">
                {sectorSplit.map((s, i) => (
                  <div key={`${s.name}-${i}`} className="legend__row">
                    <span
                      className="dot"
                      style={{
                        background: pieColors[i % pieColors.length],
                      }}
                    />
                    <div className="legend__label">
                      <div className="legend__name">{s.name}</div>
                      <div className="legend__val">
                        {fmtCurrency(s.value)} (
                        {(
                          (s.value /
                            sectorSplit.reduce(
                              (acc, x) => acc + x.value,
                              0
                            )) *
                          100
                        ).toFixed(1)}
                        %)
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </Card>

        {/* Recent Transactions */}
        <Card title="Recent Transactions">
          {transactions.length === 0 ? (
            <div className="empty">
              <div className="empty__icon">🧾</div>
              <div>No recent activity</div>
            </div>
          ) : (
            <div className="list-container">
              {transactions.map((t, i) => (
                <div key={i} className="list-box">
                  <div className="list-left">
                    <span className={`tx-type ${t.type.toLowerCase()}`}>
                      {t.type.toUpperCase()}
                    </span>
                    <span className="list-title">{t.stockname}</span>
                    <span className="list-date">
                      {t.date ? new Date(t.date).toLocaleString() : ""}
                    </span>
                  </div>
                  <div className="list-right">
                    <span className="tx-price">
                      {fmtCurrency(t.price)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </motion.div>
  );
}

/* --- Small UI components --- */
function MetricCard({ icon, label, value, sub }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45 }}
      className="metric hover-lift"
    >
      <div className="metric__icon">{icon}</div>
      <div className="metric__body">
        <div className="metric__label">{label}</div>
        <div className="metric__value">{value}</div>
        {sub && <div className="metric__sub">{sub}</div>}
      </div>
    </motion.div>
  );
}

function ChartCard({ title, tag, children }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="chart-card hover-lift"
    >
      <div className="card__head">
        <h3>{title}</h3>
        <span className="tag">{tag}</span>
      </div>
      {/* Added 'chart-container' class for specific styling */}
      <div className="card__body chart-container">{children}</div>
    </motion.div>
  );
}

function Card({ title, children }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="chart-card hover-lift"
    >
      <div className="card__head" style={{ marginBottom: 12 }}>
        <h3>{title}</h3>
      </div>
      <div className="card__body">{children}</div>
    </motion.div>
  );
}