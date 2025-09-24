import React, { useState, useEffect } from "react";
import axios from "axios";
import "./Watchlist.css";
import RecommendationModal from "./RecommendationModal";

const ArrowUpRight = () => <span aria-hidden>📈</span>;
const ArrowDownRight = () => <span aria-hidden>📉</span>;
const SearchIcon = () => <span aria-hidden>🔍</span>;

function Watchlist({ userid = 1 }) {
  const [searchTerm, setSearchTerm] = useState("");
  const [autocompleteResults, setAutocompleteResults] = useState([]);
  const [trackedStocks, setTrackedStocks] = useState([]);
  const [selectedStock, setSelectedStock] = useState(null);
  const [quantity, setQuantity] = useState("");
  const [wallet, setWallet] = useState(0);

  const [showCelebrate, setShowCelebrate] = useState(false);
  const [showBuyModal, setShowBuyModal] = useState(false);
  const [showSuccessModal, setShowSuccessModal] = useState(false);
  const [purchasedStock, setPurchasedStock] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [showErrorModal, setShowErrorModal] = useState(false);

  // ---------------- fetchers ----------------
  const fetchWallet = () => {
    axios
      .get(`http://127.0.0.1:5000/get_wallet/${userid}`)
      .then((res) => {
        if (res.data && res.data.money !== undefined) {
          const m = Number(res.data.money);
          setWallet(Number.isFinite(m) ? m : 0);
        }
      })
      .catch((err) => {
        console.error("Wallet fetch error:", err);
        setWallet(0);
      });
  };

  const fetchWatchlist = () => {
    axios
      .get(`http://127.0.0.1:5000/get_watchlist/${userid}`)
      .then((res) => {
        const data = Array.isArray(res.data)
          ? res.data
          : res.data.watchlist || [];
        const normalized = data.map((it) => ({
          ...it,
          symbol: (it.symbol || it.stock_symbol || "")
            .replace(/\.NS$/i, "")
            .toUpperCase(),
          name: it.name || it.stock_name || it.companyname || "",
        }));
        setTrackedStocks(normalized);
      })
      .catch((err) => {
        console.error("Watchlist fetch error:", err);
        setTrackedStocks([]);
      });
  };

  useEffect(() => {
    fetchWallet();
    fetchWatchlist();
  }, [userid]);

  // ---------------- autocomplete ----------------
  useEffect(() => {
    if (searchTerm.trim() === "") {
      setAutocompleteResults([]);
      return;
    }
    const q = encodeURIComponent(searchTerm.trim());
    axios
      .get(`http://127.0.0.1:5000/autocomplete?q=${q}`)
      .then((res) => {
        const results = Array.isArray(res.data)
          ? res.data
          : res.data.results || [];
        const normalized = results.map((r) => ({
          ...r,
          SYMBOL: (r.SYMBOL || "").toUpperCase(),
          "NAME OF COMPANY": r["NAME OF COMPANY"] || r.stock_name || "",
          price: r.price !== undefined ? r.price : null,
        }));
        setAutocompleteResults(normalized);
      })
      .catch((err) => {
        console.error("Autocomplete error:", err);
        setAutocompleteResults([]);
      });
  }, [searchTerm]);

  // ---------------- trackStock ----------------
  const trackStock = (symbolRaw) => {
    const symbol = (symbolRaw || "")
      .replace(/\.NS$/i, "") // remove NSE suffix
      .replace(/:.*$/i, "") // remove :1, :EQ, etc.
      .toUpperCase();

    axios
      .get(`http://127.0.0.1:5000/get_stock_id/${symbol}`)
      .then((res) => {
        const stock_id = res.data.stock_id;
        if (!stock_id) throw new Error("Stock not found in DB");
        return axios.post("http://127.0.0.1:5000/add_to_watchlist", {
          userid,
          stock_id,
        });
      })
      .then(() => fetchWatchlist())
      .catch((err) => {
        console.error("Add to watchlist error:", err);
        setErrorMessage(
          err?.response?.data?.error || err.message || "Failed to add"
        );
        setShowErrorModal(true);
      });
  };

  // ---------------- remove ----------------
  const removeTracked = (stockId) => {
    axios
      .post(`http://127.0.0.1:5000/remove_from_watchlist/${userid}/${stockId}`)
      .then(() =>
        setTrackedStocks((prev) => prev.filter((s) => s.stock_id !== stockId))
      )
      .catch((err) => {
        console.error("Remove error:", err);
        setErrorMessage(
          err?.response?.data?.error || err.message || "Failed to remove"
        );
        setShowErrorModal(true);
      });
  };

  // ---------------- buy flow ----------------
  const openBuyModal = (stock) => {
    setSelectedStock(stock);
    setQuantity("");
    setShowBuyModal(true);
  };
  const closeBuyModal = () => {
    setShowBuyModal(false);
    setSelectedStock(null);
    setQuantity("");
  };

  const executePurchase = () => {
    if (!selectedStock || !quantity) return;
    const numQuantity = Number(quantity);
    if (isNaN(numQuantity) || numQuantity <= 0) {
      setErrorMessage("Enter a valid number of shares.");
      setShowErrorModal(true);
      return;
    }

    axios
      .post("http://127.0.0.1:5000/buy_from_watchlist", {
        userid,
        symbol: selectedStock.symbol,
        quantity: numQuantity,
      })
      .then((res) => {
        const resp = res.data || {};
        if (resp.new_wallet !== undefined) {
          setWallet(Number(resp.new_wallet));
        } else {
          fetchWallet();
        }

        const totalCost = Number(selectedStock.price || 0) * numQuantity;
        setPurchasedStock({
          ...selectedStock,
          quantity: numQuantity,
          totalCost,
        });
        setShowSuccessModal(true);
        closeBuyModal();
        fetchWatchlist();
      })
      .catch((err) => {
        console.error("Purchase error:", err);
        setErrorMessage(
          err?.response?.data?.error || err.message || "Purchase failed"
        );
        setShowErrorModal(true);
      });
  };

  // ---------------- derived stats ----------------
  const portfolioCount = trackedStocks.length;
  const totalPositions = trackedStocks.reduce(
    (a, p) => a + (p.shares || 0),
    0
  );

  // ---------------- render ----------------
  return (
    <div className="wl-root">
      {/* Top bar */}
      <header className="wl-topbar">
        <div className="wl-titlewrap">
          <h1 className="wl-title">Watchlist</h1>
          <span className="wl-title-glow" aria-hidden />
        </div>

        <div className="wl-stats">
          <div className="chip chip-blue" title="Cash in wallet">
            <span className="chip-label">Wallet</span>
            <span className="chip-value">₹{wallet.toLocaleString()}</span>
          </div>
          <div className="chip chip-green" title="Positions tracked">
            <span className="chip-label">Positions</span>
            <span className="chip-value">{portfolioCount}</span>
          </div>
          <div className="chip chip-white" title="Total shares">
            <span className="chip-label">Shares</span>
            <span className="chip-value">{totalPositions}</span>
          </div>
        </div>
      </header>

      {/* Search */}
      <section className="wl-search">
        <div className="wl-searchbox">
          <SearchIcon />
          <input
            aria-label="Search stocks"
            placeholder="Search by symbol or name..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <span className="wl-focusring" aria-hidden />
        </div>

        {searchTerm.trim() && (
          <div className="wl-results">
            {autocompleteResults.map((s, idx) => (
              <div key={idx} className="wl-result-row">
                <div className="wl-result-left">
                  <span className="sym">{s.SYMBOL}</span>
                  <span className="name">{s["NAME OF COMPANY"]}</span>
                  {s.price !== null && s.price !== undefined && (
                    <span className="price">₹{s.price}</span>
                  )}
                </div>
                <div className="wl-result-right">
                  <button
                    className="btn btn-buy"
                    onClick={() =>
                      trackStock(
                        (s.SYMBOL || "").replace(/\.NS$/i, "").toUpperCase()
                      )
                    }
                  >
                    Track
                  </button>
                </div>
              </div>
            ))}
            {autocompleteResults.length === 0 && (
              <div className="wl-empty">No matches found.</div>
            )}
          </div>
        )}
      </section>

      {/* Watchlist table */}
      <section className="wl-card">
        <div className="wl-table-head" role="row">
          <span>Stock</span>
          <span>Price</span>
          <span>Change</span>
          <span>Action</span>
        </div>

        <div className="wl-table-body">
          {trackedStocks.map((stock) => {
            const up = (stock.change || 0) >= 0;
            return (
              <div
                key={stock.stock_id || stock.symbol}
                className="wl-row"
              >
                {/* Stock */}
                <div className="wl-cell stock">
                  <div className={`trend-dot ${up ? "up" : "down"}`}>
                    {up ? <ArrowUpRight /> : <ArrowDownRight />}
                  </div>
                  <div className="stock-meta">
                    <div className="sym">
                      {stock.symbol || stock.stock_symbol}
                    </div>
                    <div className="name">
                      {stock.name || stock.stock_name || stock.companyname}
                    </div>
                  </div>
                </div>

                {/* Price */}
                <div className="wl-cell price">₹{stock.price}</div>

                {/* Change */}
                <div className="wl-cell">
                  <span
                    className={`badge ${up ? "badge-up" : "badge-down"}`}
                  >
                    {stock.change} ({stock.change_percent}%)
                  </span>
                </div>

                {/* Action */}
                <div className="wl-cell action">
                  <button
                    className="btn btn-buy"
                    onClick={() => openBuyModal(stock)}
                  >
                    + Buy
                  </button>
                  <button
                    className="btn btn-cancel"
                    onClick={() => removeTracked(stock.stock_id)}
                    style={{ marginLeft: 8 }}
                  >
                    Remove
                  </button>
                </div>
              </div>
            );
          })}

          {trackedStocks.length === 0 && (
            <div className="wl-empty">
              Your watchlist is empty. Search a stock above and click{" "}
              <strong>Track</strong>.
            </div>
          )}
        </div>
      </section>

      {/* Buy Modal */}
      {showBuyModal && selectedStock && (
        <div className="wl-backdrop" role="dialog" aria-modal="true">
          <div className="wl-modal">
            <div className="wl-modal-head">
              <div className="tick blue" aria-hidden />
              <div className="wl-modal-title">
                Buy <strong>{selectedStock.symbol}</strong>
              </div>
            </div>

            <div className="wl-modal-sub">{selectedStock.name}</div>
            <div className="wl-modal-price">
              Price per share: <strong>₹{selectedStock.price}</strong>
            </div>

            <div className="wl-input">
              <input
                type="number"
                min="1"
                step="1"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                placeholder="Number of shares"
              />
              <span className="wl-focusring" aria-hidden />
            </div>

            {quantity && (
              <div className="wl-total">
                Total:{" "}
                <strong>
                  ₹{(selectedStock.price * Number(quantity)).toFixed(2)}
                </strong>
              </div>
            )}

            <div className="wl-modal-actions">
              <button className="btn btn-confirm" onClick={executePurchase}>
                Buy
              </button>
              <button className="btn btn-cancel" onClick={closeBuyModal}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Success Modal */}
      {showSuccessModal && purchasedStock && (
        <div className="wl-backdrop" role="dialog" aria-modal="true">
          <div className="wl-modal success">
            <div className="wl-modal-head">
              <div className="tick green" aria-hidden />
              <div className="wl-modal-title">Purchase Successful</div>
            </div>

            <div className="wl-modal-sub">
              You bought <strong>{purchasedStock.quantity}</strong> shares of{" "}
              <strong>{purchasedStock.symbol}</strong>
            </div>
            <div className="wl-total">
              Total Spent:{" "}
              <strong>₹{purchasedStock.totalCost.toFixed(2)}</strong>
            </div>

            <div className="wl-modal-actions">
              <button
                className="btn btn-confirm"
                onClick={() => {
                  setShowSuccessModal(false);
                  setShowCelebrate(true);
                }}
              >
                Awesome
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Celebration / Recommendation Modal */}
      {showCelebrate && purchasedStock && (
        <RecommendationModal
          userId={userid}
          stock={purchasedStock}
          type="buy"
          onClose={() => setShowCelebrate(false)}
        />
      )}

      {/* Error Modal */}
      {showErrorModal && (
        <div className="wl-backdrop" role="dialog" aria-modal="true">
          <div className="wl-modal error">
            <div className="wl-modal-head">
              <div className="tick red" aria-hidden />
              <div className="wl-modal-title">Error</div>
            </div>
            <div className="wl-modal-sub">{errorMessage}</div>
            <div className="wl-modal-actions">
              <button
                className="btn btn-cancel"
                onClick={() => setShowErrorModal(false)}
              >
                OK
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Watchlist;
