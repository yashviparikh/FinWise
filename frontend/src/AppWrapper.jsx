import React, { useState, useEffect } from 'react';
import { Routes, Route } from 'react-router-dom';
import Watchlist from './Watchlist';
import Portfolio from './Portfolio';
import Dashboard from './Dashboard.jsx';
import Learnings from './Learnings.jsx';
import Home from './Home.jsx';
import Log from './Log.jsx';
import Signup from './Signup';
import OtpReset from './OTPReset';
import StockPrediction from './StockPrediction.jsx';
import TradeSimulator from './TradeSimulator.jsx';
function AppWrapper() {

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


  const [portfolio, setPortfolio] = useState(() => {
    const saved = localStorage.getItem('portfolio');
    return saved ? JSON.parse(saved) : [];
  });

  const [wallet, setWallet] = useState(() => {
    const saved = localStorage.getItem('wallet');
    return saved ? parseFloat(saved) : 50000;
  });

  const [watchlist, setWatchlist] = useState(() => {
    const saved = localStorage.getItem('watchlist');
    return saved ? JSON.parse(saved) : [];
  });

  const [transactions] = useState(() => {
  const saved = localStorage.getItem("transactions");
  return saved ? JSON.parse(saved) : [
    { type: "BUY", symbol: "AAPL", shares: 10, price: 180, amount: 1800, date: "2025-09-01 10:00 AM" },
    { type: "BUY", symbol: "GOOGL", shares: 5, price: 140, amount: 700, date: "2025-09-02 2:00 PM" },
  ];
});

useEffect(() => {
  localStorage.setItem("transactions", JSON.stringify(transactions));
}, [transactions]);

  useEffect(() => {
    localStorage.setItem('portfolio', JSON.stringify(portfolio));
  }, [portfolio]);

  useEffect(() => {
    localStorage.setItem('wallet', wallet.toString());
  }, [wallet]);

  useEffect(() => {
    localStorage.setItem('watchlist', JSON.stringify(watchlist));
  }, [watchlist]);

  return (
    <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/Log" element={<Log />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/forgot-password" element={<OtpReset />} />
      <Route path="/watchlist" element={
          <Watchlist
            portfolio={portfolio}
            setPortfolio={setPortfolio}
            wallet={wallet}
            setWallet={setWallet}
            watchlist={watchlist}
            setWatchlist={setWatchlist}
          />
      } />
      <Route path="/portfolio" element={
          <Portfolio
            portfolio={portfolio}
            setPortfolio={setPortfolio}
            wallet={wallet}
            setWallet={setWallet}
          />
      } />
      <Route
        path="/dashboard"
        element={
            <Dashboard
              portfolio={portfolio}
              setPortfolio={setPortfolio}
              wallet={wallet}
              setWallet={setWallet}
              watchlist={watchlist}
              setWatchlist={setWatchlist}
              transactions={transactions}
              allStocks={allStocks}
            />
        }
      />

      <Route path='/learnings' element={
        <Learnings />
      }
      />
      <Route path='/stockprediction' element={
        <StockPrediction />
      }
      />
      <Route path='/trade-simulator' element={<TradeSimulator />} />
    </Routes>
  );
}

export default AppWrapper;
