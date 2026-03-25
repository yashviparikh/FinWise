import React, { useState, useEffect } from "react";
import axios from "axios";
import "./Learnings.css";

function Learning() {
  const [selectedTopic, setSelectedTopic] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [hoveredNews, setHoveredNews] = useState(null);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const [newsHeadlines, setNewsHeadlines] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 4;

  // --------- Static Topics ----------
  const learningTopics = [
  {
    id: 1,
    icon: "📊",
    title: "Moving Averages (MA)",
    summary: "Understand trend direction using average price over time.",
    content: `
      <h3>Moving Averages (MA)</h3>
      <p>A moving average smooths price data to identify the overall trend.</p>
      <ul>
        <li><strong>Simple MA (SMA):</strong> Average of prices over a period (e.g., 100 days).</li>
        <li><strong>Exponential MA (EMA):</strong> Gives more weight to recent prices.</li>
        <li><strong>Trend Signal:</strong> Price above MA → uptrend, below → downtrend.</li>
        <li><strong>Crossover:</strong> Short-term MA crossing long-term MA = buy/sell signal.</li>
      </ul>
      <div class="highlight">Use Case: Identify whether a stock is trending up or down.</div>
    `,
    resources: [
    {
      type: "article",
      title: "Moving Averages Explained",
      url: "https://www.investopedia.com/terms/m/movingaverage.asp",
      source: "Investopedia"
    },
    {
      type: "course",
      title: "Moving Averages - Zerodha Varsity",
      url: "https://zerodha.com/varsity/chapter/moving-averages/",
      source: "Zerodha Varsity"
    },
    {
      type: "video",
      title: "Moving Averages Trading Strategy",
      url: "https://www.youtube.com/watch?v=1f3k3d7xJ7o",
      source: "YouTube (TradingView/educational)"
    }
  ]
  },
  {
    id: 2,
    icon: "⚡",
    title: "Relative Strength Index (RSI)",
    summary: "Measure if a stock is overbought or oversold.",
    content: `
      <h3>Relative Strength Index (RSI)</h3>
      <p>RSI is a momentum indicator that ranges from 0 to 100.</p>
      <ul>
        <li><strong>Above 70:</strong> Overbought (price may fall)</li>
        <li><strong>Below 30:</strong> Oversold (price may rise)</li>
        <li><strong>50 Level:</strong> Neutral zone</li>
        <li><strong>Divergence:</strong> RSI vs price mismatch can signal reversal</li>
      </ul>
      <div class="highlight">Use Case: Find good entry/exit points.</div>
    `,
    resources: [
    {
      type: "article",
      title: "RSI Indicator Explained",
      url: "https://www.investopedia.com/terms/r/rsi.asp",
      source: "Investopedia"
    },
    {
      type: "course",
      title: "RSI - Zerodha Varsity",
      url: "https://zerodha.com/varsity/chapter/relative-strength-index/",
      source: "Zerodha Varsity"
    },
    {
      type: "video",
      title: "RSI Trading Strategy Explained",
      url: "https://www.youtube.com/watch?v=2y6v3gQ5KXc",
      source: "YouTube (educational)"
    }
  ]
  },
  {
    id: 3,
    icon: "📉",
    title: "MACD Indicator",
    summary: "Track momentum and trend changes.",
    content: `
      <h3>MACD (Moving Average Convergence Divergence)</h3>
      <p>MACD shows the relationship between two moving averages.</p>
      <ul>
        <li><strong>MACD Line:</strong> Difference between short and long EMAs</li>
        <li><strong>Signal Line:</strong> EMA of MACD line</li>
        <li><strong>Buy Signal:</strong> MACD crosses above signal line</li>
        <li><strong>Sell Signal:</strong> MACD crosses below signal line</li>
      </ul>
      <div class="highlight">Use Case: Confirm trends and detect reversals.</div>
    `,
     resources: [
    {
      type: "article",
      title: "MACD Indicator Guide",
      url: "https://www.investopedia.com/terms/m/macd.asp",
      source: "Investopedia"
    },
    {
      type: "course",
      title: "MACD - Zerodha Varsity",
      url: "https://zerodha.com/varsity/chapter/macd/",
      source: "Zerodha Varsity"
    }
  ]
  },
  {
    id: 4,
    icon: "🕯️",
    title: "Candlestick Patterns",
    summary: "Understand price action and market psychology.",
    content: `
      <h3>Candlestick Basics</h3>
      <p>Candlesticks show price movement in a given time period.</p>
      <ul>
        <li><strong>Green Candle:</strong> Price increased</li>
        <li><strong>Red Candle:</strong> Price decreased</li>
        <li><strong>Wicks:</strong> Show high and low prices</li>
        <li><strong>Body:</strong> Shows open and close</li>
      </ul>

      <h4>Common Patterns:</h4>
      <ul>
        <li><strong>Doji:</strong> Market indecision</li>
        <li><strong>Hammer:</strong> Possible reversal upwards</li>
        <li><strong>Engulfing:</strong> Strong trend reversal signal</li>
      </ul>

      <div class="highlight">Use Case: Time your entries and exits more precisely.</div>
    `,
    resources: [
    {
      type: "article",
      title: "Candlestick Charting Basics",
      url: "https://www.investopedia.com/trading/candlestick-charting-what-is-it/",
      source: "Investopedia"
    },
    {
      type: "course",
      title: "Candlestick Patterns - Zerodha Varsity",
      url: "https://zerodha.com/varsity/chapter/single-candlestick-patterns/",
      source: "Zerodha Varsity"
    }
  ]
  },
  {
  id: 5,
  icon: "📏",
  title: "Support & Resistance",
  summary: "Identify key price levels where stocks tend to reverse.",
  content: `
    <h3>Support & Resistance</h3>
    <p>These are price levels where the stock repeatedly stops and reverses.</p>
    <ul>
      <li><strong>Support:</strong> Price level where demand prevents further fall</li>
      <li><strong>Resistance:</strong> Price level where selling pressure stops rise</li>
      <li><strong>Breakout:</strong> When price crosses resistance → strong upward move</li>
      <li><strong>Breakdown:</strong> When price falls below support → strong downward move</li>
    </ul>
    <div class="highlight">Use Case: Decide entry and exit zones.</div>
  `,
  "resources": [
{
"type": "article",
"title": "Support and Resistance Basics",
"url": "https://www.investopedia.com/trading/support-and-resistance-basics/",
"source": "Investopedia"
},
{
"type": "course",
"title": "Support & Resistance - Zerodha Varsity",
"url": "https://zerodha.com/varsity/chapter/support-resistance/",
"source": "Zerodha Varsity"
},
{
"type": "video",
"title": "Support and Resistance Explained (Clean Strategy)",
"url": "https://www.youtube.com/watch?v=K6k7K0mU4bY",
"source": "YouTube (Rayner Teo)"
}
]
},
{
  id: 6,
  icon: "📉",
  title: "Bollinger Bands",
  summary: "Measure volatility and identify overbought/oversold zones.",
  content: `
    <h3>Bollinger Bands</h3>
    <p>Consist of a moving average and two bands above and below it.</p>
    <ul>
      <li><strong>Upper Band:</strong> Overbought zone</li>
      <li><strong>Lower Band:</strong> Oversold zone</li>
      <li><strong>Squeeze:</strong> Low volatility → breakout expected</li>
      <li><strong>Expansion:</strong> High volatility → strong movement</li>
    </ul>
    <div class="highlight">Use Case: Spot volatility and breakout opportunities.</div>
  `,
  "resources": [
{
"type": "article",
"title": "Bollinger Bands Explained",
"url": "https://www.investopedia.com/terms/b/bollingerbands.asp",
"source": "Investopedia"
},
{
"type": "course",
"title": "Bollinger Bands - Zerodha Varsity",
"url": "https://zerodha.com/varsity/chapter/bollinger-bands/",
"source": "Zerodha Varsity"
},
{
"type": "video",
"title": "Bollinger Bands Trading Strategy",
"url": "https://www.youtube.com/watch?v=2x2F5lH0x6k",
"source": "YouTube (Trading Strategy)"
}
]
},
{
  id: 7,
  icon: "🧠",
  title: "RSI Divergence",
  summary: "When price and RSI disagree — a powerful reversal signal.",
  content: `
    <h3>RSI Divergence</h3>
    <p>Divergence happens when price and RSI move in opposite directions.</p>
    <ul>
      <li><strong>Bullish Divergence:</strong> Price makes lower lows, RSI makes higher lows → possible upward reversal</li>
      <li><strong>Bearish Divergence:</strong> Price makes higher highs, RSI makes lower highs → possible downward reversal</li>
      <li><strong>Why it works:</strong> Momentum is weakening even though price continues</li>
    </ul>
    <div class="highlight">Use Case: Catch reversals before they happen.</div>
  `,
  resources: [
    {
      type: "article",
      title: "RSI Divergence Explained",
      url: "https://www.investopedia.com/articles/trading/04/031004.asp",
      source: "Investopedia"
    },
    {
      type: "video",
      title: "RSI Divergence Strategy",
      url: "https://www.youtube.com/watch?v=7R9l9h7cF7M",
      source: "YouTube (educational)"
    }
  ]
},
{
  id: 8,
  icon: "⚡",
  title: "Liquidity & Stop Hunting",
  summary: "Understand how big players trigger retail stop-losses.",
  content: `
    <h3>Liquidity & Stop Hunting</h3>
    <p>Markets often move to areas where many stop-losses are placed.</p>
    <ul>
      <li><strong>Liquidity Zones:</strong> Areas above highs or below lows</li>
      <li><strong>Stop Hunting:</strong> Price briefly breaks levels to trigger stops, then reverses</li>
      <li><strong>False Breakouts:</strong> Common trap for beginners</li>
    </ul>
    <div class="highlight">Use Case: Avoid entering trades on fake breakouts.</div>
  `,
  resources: [
    {
      type: "article",
      title: "Market Liquidity Explained",
      url: "https://www.investopedia.com/terms/l/liquidity.asp",
      source: "Investopedia"
    },
    {
      type: "video",
      title: "Stop Hunting Explained",
      url: "https://www.youtube.com/watch?v=QgaTlTfQnZI",
      source: "YouTube (price action education)"
    }
  ]
},
{
  id: 9,
  icon: "📦",
  title: "Consolidation & Breakouts",
  summary: "Identify when a stock is preparing for a big move.",
  content: `
    <h3>Consolidation & Breakouts</h3>
    <p>Consolidation is when price moves in a tight range before a breakout.</p>
    <ul>
      <li><strong>Consolidation:</strong> Low volatility, sideways movement</li>
      <li><strong>Breakout:</strong> Strong move after consolidation</li>
      <li><strong>Volume Spike:</strong> Confirms breakout strength</li>
    </ul>
    <div class="highlight">Use Case: Enter before large price moves.</div>
  `,
  "resources": [
{
"type": "article",
"title": "Breakout Trading Strategy",
"url": "https://www.investopedia.com/articles/trading/08/trading-breakouts.asp",
"source": "Investopedia"
},
{
"type": "video",
"title": "How to Trade Breakouts Properly",
"url": "https://www.youtube.com/watch?v=rlZRtQkfK04",
"source": "YouTube (Rayner Teo)"
}
]
},
{
  id: 10,
  icon: "📊",
  title: "Multi-Timeframe Analysis",
  summary: "Analyze the same stock across different timeframes.",
  content: `
    <h3>Multi-Timeframe Analysis</h3>
    <p>Look at the same stock on different timeframes to get better context.</p>
    <ul>
      <li><strong>Higher Timeframe:</strong> Shows overall trend (daily/weekly)</li>
      <li><strong>Lower Timeframe:</strong> Helps with entry timing</li>
      <li><strong>Alignment:</strong> Trade in direction of higher timeframe</li>
    </ul>
    <div class="highlight">Use Case: Avoid trading against the main trend.</div>
  `,
  "resources": [
{
"type": "article",
"title": "Multiple Time Frame Analysis",
"url": "https://www.investopedia.com/articles/trading/11/multiple-time-frames.asp",
"source": "Investopedia"
},
{
"type": "video",
"title": "Multi Timeframe Trading Explained",
"url": "https://www.youtube.com/watch?v=8s6xWc6w6zY",
"source": "YouTube (TradingView)"
}
]
},
{
  id: 11,
  icon: "🎯",
  title: "Position Sizing",
  summary: "How much to invest in a trade based on risk.",
  content: `
    <h3>Position Sizing</h3>
    <p>Determines how much capital to allocate to a trade.</p>
    <ul>
      <li><strong>Risk per trade:</strong> Usually 1–2% of total capital</li>
      <li><strong>Depends on stop-loss distance</strong></li>
      <li><strong>Prevents large losses</strong></li>
    </ul>
    <div class="highlight">Use Case: Stay in the game even after losses.</div>
  `,
  "resources": [
{
"type": "article",
"title": "Position Sizing Strategies",
"url": "https://www.investopedia.com/terms/p/positionsizing.asp",
"source": "Investopedia"
},
{
"type": "course",
"title": "Position Sizing - Zerodha Varsity",
"url": "https://zerodha.com/varsity/chapter/position-sizing/",
"source": "Zerodha Varsity"
},
{
"type": "video",
"title": "Position Sizing Explained (Risk Management)",
"url": "https://www.youtube.com/watch?v=G10v0yP5w9k",
"source": "YouTube (Trading Education)"
}
]
},
{
  id: 12,
  icon: "📉",
  title: "Drawdown",
  summary: "Measure how much your investment drops from its peak.",
  content: `
    <h3>Drawdown</h3>
    <p>Drawdown is the decline from a peak to a low in your portfolio.</p>
    <ul>
      <li><strong>Max Drawdown:</strong> Biggest loss from peak</li>
      <li><strong>Recovery:</strong> Larger drawdowns need bigger gains to recover</li>
      <li><strong>Example:</strong> 50% loss needs 100% gain to recover</li>
    </ul>
    <div class="highlight">Use Case: Evaluate risk of strategies.</div>
  `
},
{
  id: 13,
  icon: "🔍",
  title: "Alpha vs Beta",
  summary: "Measure performance vs market movement.",
  content: `
    <h3>Alpha vs Beta</h3>
    <p>Used to evaluate investment performance.</p>
    <ul>
      <li><strong>Alpha:</strong> Extra return above market</li>
      <li><strong>Beta:</strong> Sensitivity to market movement</li>
      <li><strong>High Beta:</strong> More volatile than market</li>
    </ul>
    <div class="highlight">Use Case: Understand if gains are skill or market-driven.</div>
  `,
  "resources": [
{
"type": "article",
"title": "Maximum Drawdown Explained",
"url": "https://www.investopedia.com/terms/m/maximum-drawdown-mdd.asp",
"source": "Investopedia"
},
{
"type": "video",
"title": "Drawdown Explained for Traders",
"url": "https://www.youtube.com/watch?v=7m3X7Z0Z8R0",
"source": "YouTube (Finance Education)"
}
]

},
{
  id: 14,
  icon: "⚖️",
  title: "Risk-Reward Ratio",
  summary: "Evaluate if a trade is worth taking.",
  content: `
    <h3>Risk-Reward Ratio</h3>
    <p>Compares potential profit to potential loss in a trade.</p>
    <ul>
      <li><strong>Example:</strong> Risk ₹100 to gain ₹300 → 1:3 ratio</li>
      <li><strong>Good Trades:</strong> Usually 1:2 or better</li>
      <li><strong>Stop-Loss:</strong> Defines your risk</li>
      <li><strong>Target Price:</strong> Defines your reward</li>
    </ul>
    <div class="highlight">Use Case: Avoid bad trades and manage losses.</div>
  `,
  "resources": [
{
"type": "article",
"title": "Alpha and Beta Explained",
"url": "https://www.investopedia.com/terms/a/alpha.asp",
"source": "Investopedia"
},
{
"type": "course",
"title": "Risk Metrics - Zerodha Varsity",
"url": "https://zerodha.com/varsity/chapter/risk-part-1/",
"source": "Zerodha Varsity"
},
{
"type": "video",
"title": "Alpha vs Beta Explained",
"url": "https://www.youtube.com/watch?v=Y0Gk1HcRZtA",
"source": "YouTube (Finance Basics)"
}
]
},
  ];

  // --------- Fetch News from Backend ----------
  useEffect(() => {
    const fetchNews = async () => {
      try {
        const res = await axios.get("http://127.0.0.1:5000/learnings/news");

        // ✅ Map backend fields → frontend structure
        const mapped = (res.data.news || []).map((item, idx) => ({
          id: idx + 1,
          title: item.headline,
          summary: item.summary,
          sentiment:
            item.sentiment?.toLowerCase() === "bullish"
              ? "Positive"
              : item.sentiment?.toLowerCase() === "bearish"
              ? "Negative"
              : "Neutral",
          category: item["market reaction"],
          learn: item["investor reaction"],
          time: res.data.last_updated
        }));

        setNewsHeadlines(mapped);
      } catch (err) {
        console.error("Error fetching news:", err);
        setNewsHeadlines([]);
      }
    };
    fetchNews();
  }, []);

  // --------- Handlers ----------
  const openModal = (topic) => {
    setSelectedTopic(topic);
    setShowModal(true);
    document.body.style.overflow = "hidden";
  };

  const closeModal = () => {
    setSelectedTopic(null);
    setShowModal(false);
    document.body.style.overflow = "";
  };

  const handleNewsHover = (news, e) => {
    setHoveredNews(news);
    setMousePos({ x: e.clientX, y: e.clientY });
  };

  const handleNewsLeave = () => setHoveredNews(null);

  return (
    <div className="learning-container">
      {/* Learning Section */}
      <h2 className="section-title">Basic Terms and Terminologies</h2>
      <div className="learning-grid">
        {learningTopics
          .slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage)
          .map((topic) => (
          <div className="learning-card" key={topic.id}>
            <div className="icon">{topic.icon}</div>
            <h3>{topic.title}</h3>
            <p>{topic.summary}</p>
            <button onClick={() => openModal(topic)}>Learn More</button>
          </div>
        ))}
      </div>

      {/* Pagination Controls */}
      <div className="pagination">
        <button 
          onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
          disabled={currentPage === 1}
          className="pagination-btn"
        >
          ← Previous
        </button>
        <span className="pagination-info">
          Page {currentPage} of {Math.ceil(learningTopics.length / itemsPerPage)}
        </span>
        <button 
          onClick={() => setCurrentPage(prev => Math.min(Math.ceil(learningTopics.length / itemsPerPage), prev + 1))}
          disabled={currentPage === Math.ceil(learningTopics.length / itemsPerPage)}
          className="pagination-btn"
        >
          Next →
        </button>
      </div>

      {/* News Section */}
      <h2 className="section-title">Top 5 News Headlines</h2>
      <div className="news-section">
        {newsHeadlines.length === 0 ? (
          <div className="news-empty">No news available right now.</div>
        ) : (
          newsHeadlines.map((news) => (
            <div
              className="news-card"
              key={news.id}
              onMouseEnter={(e) => handleNewsHover(news, e)}
              onMouseLeave={handleNewsLeave}
            >
              <div className="news-header">
                <span className="news-badge category">
                  {news.category || "—"}
                </span>
                <span
                  className={`news-badge sentiment ${
                    news.sentiment === "Positive"
                      ? "positive"
                      : news.sentiment === "Negative"
                      ? "negative"
                      : "neutral"
                  }`}
                >
                  {news.sentiment || "—"}
                </span>
                <span className="news-time">
                  {new Date(news.time).toLocaleString("en-IN", {
                    dateStyle: "medium",
                    timeStyle: "short"
                  })}
                </span>
              </div>
              <h3 className="news-title">
                {news.title || "Headline not available"}
              </h3>
              <p className="news-summary">
                {news.summary || "Summary not available."}
              </p>
            </div>
          ))
        )}
      </div>

      {/* Hover Popup */}
      {hoveredNews && (
        <div
          className="hover-popup"
          style={{
            left: mousePos.x + 20,
            top: mousePos.y + 10
          }}
        >
          <h4>{hoveredNews.title || "Headline not available"}</h4>
          <p>
            <strong>Summary:</strong>{" "}
            {hoveredNews.summary || "Summary not available."}
          </p>
          <p>
            <strong>Learn:</strong>{" "}
            {hoveredNews.learn || "No learnings yet."}
          </p>
          <p>
            <strong>Sentiment:</strong>{" "}
            <span
              className={`news-sentiment ${
                hoveredNews.sentiment === "Positive"
                  ? "positive"
                  : hoveredNews.sentiment === "Negative"
                  ? "negative"
                  : "neutral"
              }`}
            >
              {hoveredNews.sentiment || "—"}
            </span>
          </p>
        </div>
      )}

      {/* Modal */}
      {showModal && selectedTopic && (
  <div className="modal-backdrop" onClick={closeModal}>
    <div className="modal-content" onClick={(e) => e.stopPropagation()}>
      
      {/* Main Content */}
      <div
        dangerouslySetInnerHTML={{ __html: selectedTopic.content }}
      />

      {/* ✅ Resources Section */}
      {selectedTopic.resources && selectedTopic.resources.length > 0 && (
        <div className="resources-section">
          <h3>📚 Learn More</h3>

          {/* Group by type */}
          {["article", "video", "course"].map((type) => {
            const filtered = selectedTopic.resources.filter(
              (r) => r.type === type
            );

            if (filtered.length === 0) return null;

            return (
              <div key={type} className="resource-group">
                <h4>
                  {type === "article" && "📄 Articles"}
                  {type === "video" && "🎥 Videos"}
                  {type === "course" && "🎓 Courses"}
                </h4>

                <ul>
                  {filtered.map((res, index) => (
                    <li key={index}>
                      <a
                        href={res.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={() =>
                          console.log("Resource clicked:", res.title)
                        }
                      >
                        <span className="res-title">{res.title}</span>
                        <span className="res-source"> ({res.source})</span>
                        <span className="external"> ↗</span>
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            );
          })}
        </div>
      )}

      <button className="close-btn" onClick={closeModal}>
        Close
      </button>
    </div>
  </div>
)}
    </div>
  );
}

export default Learning;
