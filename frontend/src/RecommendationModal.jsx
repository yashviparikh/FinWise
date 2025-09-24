import React, { useEffect, useState } from "react";
import axios from "axios";
import { motion } from "framer-motion";
import { TrendingUp, TrendingDown, Star } from "lucide-react";

export default function RecommendationModal({ onClose, userId }) {
  const [recommendations, setRecommendations] = useState([]);

  useEffect(() => {
    const fetchRecommendations = async () => {
      try {
        const res = await axios.get(`http://127.0.0.1:5000/recommendations/${userId}`);
        setRecommendations(res.data.recommendations || []);
      } catch (err) {
        console.error("Error fetching recommendations:", err);
      }
    };
    fetchRecommendations();
  }, [userId]);

  if (!recommendations || recommendations.length === 0) return null;

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
        <div className="flex justify-between items-center mb-5">
          <h2 className="text-xl font-bold text-cyan-400">Recommended Stocks for You</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-white transition text-xl">✕</button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-5">
          {recommendations.map((stock) => (
            <motion.div
              key={stock.stockname}
              whileHover={{ scale: 1.05 }}
              className="bg-slate-800 p-4 rounded-xl border border-slate-700 hover:border-cyan-500/40 transition"
            >
              <div className="flex justify-between items-center mb-2">
                <h3 className="text-lg font-semibold text-white">{stock.stockname}</h3>
                {stock.buy_prob > 0.5 ? (
                  <TrendingUp className="text-green-400" size={18} />
                ) : (
                  <TrendingDown className="text-red-400" size={18} />
                )}
              </div>
              <p className="text-slate-400 text-sm">{stock.companyname}</p>
              {stock.price && <p className="text-lg font-bold mt-2">${Number(stock.price).toFixed(2)}</p>}
              <div className="flex items-center gap-1 mt-2 text-yellow-400 text-sm">
                <Star size={14} /> {(stock.buy_prob * 100).toFixed(1)}% Match
              </div>
            </motion.div>
          ))}
        </div>
      </motion.div>
    </motion.div>
  );
}
