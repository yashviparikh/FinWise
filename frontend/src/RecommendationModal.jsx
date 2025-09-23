import React from "react";
import { motion } from "framer-motion";
import { TrendingUp, TrendingDown, Star } from "lucide-react";

const dummyRecommendations = [
  { symbol: "TSLA", name: "Tesla", price: 278.12, change: "+2.4%", trend: "up", score: 92 },
  { symbol: "MSFT", name: "Microsoft", price: 331.40, change: "-0.8%", trend: "down", score: 88 },
  { symbol: "GOOGL", name: "Alphabet", price: 128.55, change: "+1.2%", trend: "up", score: 85 },
  { symbol: "AMZN", name: "Amazon", price: 142.18, change: "+0.5%", trend: "up", score: 83 },
  { symbol: "NFLX", name: "Netflix", price: 406.25, change: "-1.1%", trend: "down", score: 81 },
{ symbol: "NFLX", name: "Netflix", price: 406.25, change: "-1.1%", trend: "down", score: 81 }
];
export default function RecommendationModal({ onClose, recommendations = dummyRecommendations }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/60 flex items-center justify-center z-50"
    >
      <motion.div
        initial={{ scale: 0.9, y: 30 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.9, y: 30 }}
        transition={{ duration: 0.3 }}
        className="bg-slate-900 p-6 rounded-2xl shadow-2xl max-w-3xl w-full border border-slate-700"
      >
        {/* Header */}
        <div className="flex justify-between items-center mb-5">
          <h2 className="text-xl font-bold text-cyan-400">Recommended Stocks for You</h2>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white transition text-xl"
          >
            ✕
          </button>
        </div>

        {/* Stocks grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-5">
          {recommendations.map((stock) => (
            <motion.div
              key={stock.symbol}
              whileHover={{ scale: 1.05 }}
              className="bg-slate-800 p-4 rounded-xl border border-slate-700 hover:border-cyan-500/40 transition"
            >
              <div className="flex justify-between items-center mb-2">
                <h3 className="text-lg font-semibold text-white">{stock.symbol}</h3>
                {stock.trend === "up" ? (
                  <TrendingUp className="text-green-400" size={18} />
                ) : (
                  <TrendingDown className="text-red-400" size={18} />
                )}
              </div>
              <p className="text-slate-400 text-sm">{stock.name}</p>
              <p className="text-lg font-bold mt-2">${stock.price.toFixed(2)}</p>
              <p
                className={`text-sm ${
                  stock.trend === "up" ? "text-green-400" : "text-red-400"
                }`}
              >
                {stock.change}
              </p>
              <div className="flex items-center gap-1 mt-2 text-yellow-400 text-sm">
                <Star size={14} /> {stock.score}% Match
              </div>
              
            </motion.div>
          ))}
        </div>
      </motion.div>
    </motion.div>
  );
}
