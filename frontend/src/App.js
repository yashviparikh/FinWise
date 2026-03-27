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
import TradeSimulator from "./TradeSimulator.jsx";
import Log from './Log.jsx';
import Signup from './Signup';
import OtpReset from './OTPReset';

function App() {
  const [wallet, setWallet] = useState(50000);

  const [portfolio, setPortfolio] = useState([]);

  const [transactions, setTransactions] = useState([]);

  const [allStocks] = useState([]);

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
        <Route path="/trade-simulator" element={<TradeSimulator />} />

            
          <Route path="/Log" element={<Log />} />
          
          <Route path="/signup" element={<Signup />} />
          <Route path="/forgot-password" element={<OtpReset />} />

        </Routes>
      </Layout>
    </Router>
    
  );
}

export default App;
