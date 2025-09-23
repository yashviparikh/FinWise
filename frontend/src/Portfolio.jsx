// import React, { useState, useMemo, useEffect, useRef } from "react";
// import axios from "axios";
// import "./Portfolio.css";
// import RecommendationModal from "./RecommendationModal";

// function useAnimatedNumber(value, duration = 700) {
//   const [display, setDisplay] = useState(value);
//   const rafRef = useRef(null);
//   const startRef = useRef(null);
//   const fromRef = useRef(value);

//   useEffect(() => {
//     cancelAnimationFrame(rafRef.current);
//     fromRef.current = display;
//     const start = performance.now();
//     startRef.current = start;
//     const diff = value - fromRef.current;
//     const animate = (now) => {
//       const t = Math.min(1, (now - start) / duration);
//       const eased = 1 - Math.pow(1 - t, 3);
//       setDisplay(fromRef.current + diff * eased);
//       if (t < 1) rafRef.current = requestAnimationFrame(animate);
//     };
//     rafRef.current = requestAnimationFrame(animate);
//     return () => cancelAnimationFrame(rafRef.current);
//     // eslint-disable-next-line react-hooks/exhaustive-deps
//   }, [value, duration]);

//   return display;
// }

// export default function Portfolio({ userid = 1 }) {
//   const [portfolio, setPortfolio] = useState([]);
//   const [wallet, setWallet] = useState(0);
//   const [selectedStock, setSelectedStock] = useState(null);
//   const [selectedHolding, setSelectedHolding] = useState(null);
//   const [quantity, setQuantity] = useState("");
//   const [showModal, setShowModal] = useState(false);
//   const [modalType, setModalType] = useState("");
//   const [modalError, setModalError] = useState("");
//   const [showReco, setShowReco] = useState(false);

//   // ✅ Fetch wallet + portfolio from backend
//   const fetchPortfolioAndWallet = async () => {
//     try {
//       const [portfolioRes, walletRes] = await Promise.all([
//         axios.get(`http://127.0.0.1:5000/portfolio/${userid}`),
//         axios.get(`http://127.0.0.1:5000/user/${userid}`),
//       ]);
//       setPortfolio(portfolioRes.data || []);
//       if (walletRes.data.money !== undefined) {
//         setWallet(parseFloat(walletRes.data.money));
//       }
//     } catch (err) {
//       console.error("Error fetching portfolio/wallet:", err);
//     }
//   };

//   useEffect(() => {
//     fetchPortfolioAndWallet();
//   }, [userid]);

//   // ✅ Filter out zero-quantity holdings
//   const filteredPortfolio = useMemo(() => {
//     return (portfolio || []).filter((h) => h.totalquantity > 0);
//   }, [portfolio]);

//   // totals derived directly from DB-backed portfolio
//   const totals = useMemo(() => {
//     let totalValue = 0;
//     let totalInvested = 0;
//     filteredPortfolio.forEach((h) => {
//       totalValue += h.ltp * h.totalquantity;
//       totalInvested += h.averagebuyprice * h.totalquantity;
//     });
//     const totalPnL = totalValue - totalInvested;
//     const totalReturn =
//       totalInvested > 0 ? (totalPnL / totalInvested) * 100 : 0;
//     return { totalValue, totalInvested, totalPnL, totalReturn };
//   }, [filteredPortfolio]);

//   const animatedTotalValue = useAnimatedNumber(totals.totalValue, 900);
//   const animatedPnL = useAnimatedNumber(totals.totalPnL, 900);
//   const animatedReturn = useAnimatedNumber(totals.totalReturn, 900);

//   const formatCurrency = (n) => {
//     if (Number.isNaN(n) || n === undefined) return "₹0.00";
//     return `${n < 0 ? "-" : ""}₹${Math.abs(n).toFixed(2)}`;
//   };

//   const closeModal = () => {
//     setShowModal(false);
//     setSelectedStock(null);
//     setSelectedHolding(null);
//     setQuantity("");
//     setModalError("");
//     document.body.style.overflow = "";
//   };

//   const openModal = (type, stock) => {
//     setSelectedStock(stock);
//     setSelectedHolding(stock);
//     setQuantity("");
//     setModalError("");
//     setModalType(type);
//     setShowModal(true);
//     document.body.style.overflow = "hidden";
//   };

//   // ✅ Execute buy/sell through backend
//   const executeTransaction = async () => {
//     if (!selectedStock || !quantity) {
//       setModalError("Please enter a quantity.");
//       return;
//     }
//     const numQuantity = Number(quantity);
//     if (!Number.isFinite(numQuantity) || numQuantity <= 0) {
//       setModalError("Quantity must be a positive number.");
//       return;
//     }

//     try {
//       if (modalType === "buy") {
//         await axios.post("http://127.0.0.1:5000/buy", {
//           userid,
//           stockname: selectedStock.stockname,
//           companyname: selectedStock.companyname,
//           qty: numQuantity,
//           price: selectedStock.ltp,
//         });
//       } else {
//         await axios.post("http://127.0.0.1:5000/sell", {
//           userid,
//           stockname: selectedStock.stockname,
//           companyname: selectedStock.companyname,
//           qty: numQuantity,
//           price: selectedStock.ltp,
//         });
//       }

//       // refresh portfolio + wallet after transaction
//       await fetchPortfolioAndWallet();
//       closeModal();
//       setShowReco(true);
//     } catch (err) {
//       console.error("Transaction error:", err);
//       setModalError("Transaction failed. Check backend logs.");
//     }
//   };



import React, { useState, useMemo, useEffect, useRef } from "react";
import axios from "axios";
import "./Portfolio.css";
import RecommendationModal from "./RecommendationModal";

function useAnimatedNumber(value, duration = 700) {
  const [display, setDisplay] = useState(value);
  const rafRef = useRef(null);
  const startRef = useRef(null);
  const fromRef = useRef(value);

  useEffect(() => {
    cancelAnimationFrame(rafRef.current);
    fromRef.current = display;
    const start = performance.now();
    startRef.current = start;
    const diff = value - fromRef.current;
    const animate = (now) => {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      setDisplay(fromRef.current + diff * eased);
      if (t < 1) rafRef.current = requestAnimationFrame(animate);
    };
    rafRef.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(rafRef.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value, duration]);

  return display;
}

export default function Portfolio({ userid = 1 }) {
  const [portfolio, setPortfolio] = useState([]);
  const [wallet, setWallet] = useState(0);
  const [selectedStock, setSelectedStock] = useState(null);
  const [selectedHolding, setSelectedHolding] = useState(null);
  const [quantity, setQuantity] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [modalType, setModalType] = useState("");
  const [modalError, setModalError] = useState("");
  const [showReco, setShowReco] = useState(false);

  // ✅ Correct backend endpoints
  const PORTFOLIO_ENDPOINT = `http://127.0.0.1:5000/portfolio/${userid}`;
  const WALLET_ENDPOINT = `http://127.0.0.1:5000/get_wallet/${userid}`;

  const fetchPortfolioAndWallet = async () => {
    try {
      const [portfolioRes, walletRes] = await Promise.all([
        axios.get(PORTFOLIO_ENDPOINT),
        axios.get(WALLET_ENDPOINT),
      ]);
      setPortfolio(portfolioRes.data || []);
      if (walletRes.data.money !== undefined) {
        setWallet(parseFloat(walletRes.data.money));
      }
    } catch (err) {
      console.error("Error fetching portfolio/wallet:", err);
    }
  };

  useEffect(() => {
    fetchPortfolioAndWallet();
  }, [userid]);

  const filteredPortfolio = useMemo(() => {
    return (portfolio || []).filter((h) => h.totalquantity > 0);
  }, [portfolio]);

  const totals = useMemo(() => {
    let totalValue = 0;
    let totalInvested = 0;
    filteredPortfolio.forEach((h) => {
      totalValue += h.ltp * h.totalquantity;
      totalInvested += h.averagebuyprice * h.totalquantity;
    });
    const totalPnL = totalValue - totalInvested;
    const totalReturn =
      totalInvested > 0 ? (totalPnL / totalInvested) * 100 : 0;
    return { totalValue, totalInvested, totalPnL, totalReturn };
  }, [filteredPortfolio]);

  const animatedTotalValue = useAnimatedNumber(totals.totalValue, 900);
  const animatedPnL = useAnimatedNumber(totals.totalPnL, 900);
  const animatedReturn = useAnimatedNumber(totals.totalReturn, 900);

  const formatCurrency = (n) => {
    if (Number.isNaN(n) || n === undefined) return "₹0.00";
    return `${n < 0 ? "-" : ""}₹${Math.abs(n).toFixed(2)}`;
  };

  const closeModal = () => {
    setShowModal(false);
    setSelectedStock(null);
    setSelectedHolding(null);
    setQuantity("");
    setModalError("");
    document.body.style.overflow = "";
  };

  const openModal = (type, stock) => {
    setSelectedStock(stock);
    setSelectedHolding(stock);
    setQuantity("");
    setModalError("");
    setModalType(type);
    setShowModal(true);
    document.body.style.overflow = "hidden";
  };

  const executeTransaction = async () => {
    if (!selectedStock || !quantity) {
      setModalError("Please enter a quantity.");
      return;
    }
    const numQuantity = Number(quantity);
    if (!Number.isFinite(numQuantity) || numQuantity <= 0) {
      setModalError("Quantity must be a positive number.");
      return;
    }

    try {
      if (modalType === "buy") {
        await axios.post("http://127.0.0.1:5000/buy", {
          userid,
          stockname: selectedStock.stockname,
          companyname: selectedStock.companyname,
          qty: numQuantity,
          price: selectedStock.ltp,
        });
      } else {
        await axios.post("http://127.0.0.1:5000/sell", {
          userid,
          stockname: selectedStock.stockname,
          companyname: selectedStock.companyname,
          qty: numQuantity,
          price: selectedStock.ltp,
        });
      }
      await fetchPortfolioAndWallet();
      closeModal();
      setShowReco(true);
    } catch (err) {
      console.error("Transaction error:", err);
      setModalError("Transaction failed. Check backend logs.");
    }
  };
  return (
    <div className="portfolio-wrap ultra">
      <header className="portfolio-top">
        <div className="brand-title">
          <div className="logo-blob" aria-hidden>
            <svg viewBox="0 0 24 24" width="18" height="18">
              <path
                d="M3 12h3l2-4 4 8 4-6 4 4"
                strokeWidth="1.6"
                strokeLinecap="round"
                strokeLinejoin="round"
                stroke="currentColor"
              />
            </svg>
          </div>
          <div>
            <h1>Portfolio</h1>
            <p className="subtitle">Track your investments & performance</p>
          </div>
        </div>

        <div className="summary-cards">
          <div className="card floaty">
            <div className="card-left">
              <div className="card-label">Total Value</div>
              <div className="card-value large">
                <span className="animated-money">
                  {formatCurrency(animatedTotalValue)}
                </span>
              </div>
            </div>
            <div className="card-icon wallet">💰</div>
          </div>

          <div className="card floaty">
            <div className="card-left">
              <div className="card-label">Total P&amp;L</div>
              <div
                className={`card-value ${
                  totals.totalPnL >= 0 ? "green" : "red"
                }`}
              >
                <span className="animated-money">
                  {totals.totalPnL >= 0 ? "+" : "-"}
                  {formatCurrency(Math.abs(animatedPnL))}
                </span>
              </div>
            </div>
            <div className="card-icon trend">📈</div>
          </div>

          <div className="card floaty">
            <div className="card-left">
              <div className="card-label">Total Return</div>
              <div
                className={`card-value ${
                  totals.totalReturn >= 0 ? "green" : "red"
                }`}
              >
                <span className="animated-money">
                  {animatedReturn.toFixed(2)}%
                </span>
              </div>
            </div>
            <div className="card-icon pct">📊</div>
          </div>
        </div>
      </header>

      <main className="portfolio-main">
        <div className="wallet-strip">
          <div>Wallet Balance</div>
          <div className="wallet-amount">{formatCurrency(wallet)}</div>
        </div>

        <section className="holdings-card ultra-card">
          <div className="holdings-header">
            <h2>Holdings</h2>
          </div>

          <div className="holdings-table">
            <div className="table-head">
              <div>Stock Name</div>
              <div>Total Quantity</div>
              <div>Average Buy Price</div>
              <div>Total Invested</div>
              <div>LTP</div>
              <div>Profit or Loss</div>
              <div>Percentage</div>
              <div>Now Value</div>
              <div>Action</div>
            </div>

            {filteredPortfolio.length === 0 && (
              <div className="table-empty">
                No holdings yet — buy a stock to see it here.
              </div>
            )}

            {filteredPortfolio.map((holding, idx) => {
              const currentValue = holding.ltp * holding.totalquantity;
              return (
                <div
                  key={`${holding.stockname}-${idx}`}
                  className="table-row"
                  style={{ transitionDelay: `${idx * 30}ms` }}
                >
                  <div className="stock-col">
                    <div className="symbol">{holding.stockname}</div>
                    <div className="company">{holding.companyname}</div>
                  </div>
                  <div>{holding.totalquantity}</div>
                  <div>{formatCurrency(holding.averagebuyprice)}</div>
                  <div>{formatCurrency(holding.totalinvested)}</div>
                  <div>{formatCurrency(holding.ltp)}</div>
                  <div
                    className={holding.profitorloss >= 0 ? "green" : "red"}
                  >
                    {holding.profitorloss >= 0 ? "+" : "-"}
                    {formatCurrency(Math.abs(holding.profitorloss))}
                  </div>
                  <div
                    className={holding.profitorloss >= 0 ? "green" : "red"}
                  >
                    {holding.percentage.toFixed(2)}%
                  </div>
                  <div>{formatCurrency(holding.nowvalue)}</div>
                  <div className="row-actions">
                    <button
                      onClick={() => openModal("buy", holding)}
                      className="btn-primary action-equal"
                    >
                      + Buy
                    </button>
                    <button
                      onClick={() => openModal("sell", holding)}
                      className="btn-danger action-equal"
                    >
                      Sell
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      </main>

      {showModal && selectedStock && (
        <div className="modal-backdrop" role="dialog" aria-modal="true">
          <div className="modal-card">
            <div className="modal-head">
              <div>
                <h3>
                  {modalType === "buy" ? "Buy" : "Sell"}{" "}
                  <span className="muted">{selectedStock.stockname}</span>
                </h3>
                <div className="muted small">{selectedStock.companyname}</div>
              </div>
              <button className="close-x" onClick={closeModal}>
                ✕
              </button>
            </div>

            <div className="modal-body">
              {modalType === "sell" && selectedHolding && (
                <div className="muted">
                  You own: <strong>{selectedHolding.totalquantity}</strong>{" "}
                  shares
                </div>
              )}

              <label className="input-label">Quantity</label>
              <input
                className="number-input"
                type="number"
                min="1"
                max={
                  modalType === "sell" ? selectedHolding?.totalquantity : undefined
                }
                value={quantity}
                onChange={(e) =>
                  setQuantity(e.target.value.replace(/^0+/, ""))
                }
                placeholder="0"
              />

              {quantity && (
                <div className="calc-row">
                  <div className="muted">
                    {modalType === "buy" ? "Total Cost" : "Estimated Revenue"}
                  </div>
                  <div className="calc-value">
                    {formatCurrency(selectedStock.ltp * Number(quantity))}
                  </div>
                </div>
              )}

              {modalError && (
                <div className="modal-error">{modalError}</div>
              )}
            </div>

            <div className="modal-footer">
              <button className="btn-cancel" onClick={closeModal}>
                Cancel
              </button>
              <button className="btn-submit" onClick={executeTransaction}>
                {modalType === "buy" ? "Buy" : "Sell"}
              </button>
            </div>
          </div>
        </div>
      )}

      {showReco && <RecommendationModal onClose={() => setShowReco(false)} />}
    </div>
  );
}
 

