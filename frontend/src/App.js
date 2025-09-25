import React, { useState } from "react";
import { BrowserRouter as Router, Routes, Route, useLocation } from "react-router-dom";
import Navbar from "./Navbar.jsx";
import AppWrapper from "./AppWrapper.jsx";
import Dashboard from "./Dashboard.jsx";
import Portfolio from "./Portfolio.jsx";
import Watchlist from "./Watchlist.jsx";
import Learnings from "./Learnings.jsx";
import Home from "./Home.jsx";
import StockPrediction from "./StockPrediction.jsx";
import Log from './Log.jsx';
import Signup from './Signup';
import OtpReset from './OTPReset';

function App() {
  const [wallet, setWallet] = useState(10000);

  const [portfolio, setPortfolio] = useState([
    { stockId: 1, symbol: "AAPL", shares: 10, avgPrice: 180 },
    { stockId: 2, symbol: "GOOGL", shares: 5, avgPrice: 140 },
  ]);

  const [transactions, setTransactions] = useState([
    {
      type: "BUY",
      symbol: "AAPL",
      shares: 10,
      price: 180,
      amount: 1800,
      date: "2025-09-01 10:00 AM",
    },
    {
      type: "BUY",
      symbol: "GOOGL",
      shares: 5,
      price: 140,
      amount: 700,
      date: "2025-09-02 2:00 PM",
    },
  ]);

  const [allStocks] = useState([
    { id: 1, symbol: "AAPL", name: "Apple Inc.", price: 185.43, sector: "Tech" },
    { id: 2, symbol: "GOOGL", name: "Alphabet Inc.", price: 142.56, sector: "Tech" },
    { id: 3, symbol: "MSFT", name: "Microsoft Corporation", price: 412.78, sector: "Tech" },
    { id: 4, symbol: "TSLA", name: "Tesla, Inc.", price: 238.92, sector: "Auto" },
    { id: 5, symbol: "NVDA", name: "NVIDIA Corporation", price: 891.34, sector: "Tech" },
    { id: 6, symbol: "AMZN", name: "Amazon.com Inc.", price: 156.78, sector: "Retail" },
    { id: 7, symbol: "META", name: "Meta Platforms Inc.", price: 484.67, sector: "Tech" },
    { id: 8, symbol: "BTC", name: "Bitcoin", price: 67432.12, sector: "Crypto" },
    { id: 9, symbol: "RELIANCE", name: "Reliance Industries", price: 2500, sector: "Energy" },
    { id: 10, symbol: "TCS", name: "Tata Consultancy Services", price: 3500, sector: "Tech" },
  ]);

  const addTransaction = (type, stock, shares, price) => {
    const tx = {
      type: type.toUpperCase(),
      symbol: stock.symbol,
      shares,
      price,
      amount: shares * price,
      date: new Date().toLocaleString(),
    };
    setTransactions((prev) => [tx, ...prev.slice(0, 9)]);
  };

  // ✅ Wrapper to control Navbar visibility
  function Layout({ children }) {
    const location = useLocation();
    const hideNavbar = location.pathname === "/"; // hide only on Home

    return (
      <div className="watchlist-container">
        {!hideNavbar && <Navbar />}
        <AppWrapper>{children}</AppWrapper>
      </div>
    );
  }

  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route
            path="/dashboard"
            element={
              <Dashboard
                wallet={wallet}
                portfolio={portfolio}
                transactions={transactions}
                allStocks={allStocks}
              />
            }
          />
          <Route
            path="/portfolio"
            element={
              <Portfolio
                portfolio={portfolio}
                setPortfolio={setPortfolio}
                wallet={wallet}
                setWallet={setWallet}
                addTransaction={addTransaction}
                allStocks={allStocks}
              />
            }
          />
          <Route
            path="/watchlist"
            element={
              <Watchlist
                portfolio={portfolio}
                setPortfolio={setPortfolio}
                wallet={wallet}
                setWallet={setWallet}
                addTransaction={addTransaction}
              />
            }
          />
          <Route path="/learnings" element={<Learnings />} />
       
        <Route path="/stockprediction" element={<StockPrediction />} />

            
          <Route path="/Log" element={<Log />} />
          
          <Route path="/signup" element={<Signup />} />
          <Route path="/forgot-password" element={<OtpReset />} />

        </Routes>
      </Layout>
    </Router>
    
  );
}

export default App;
