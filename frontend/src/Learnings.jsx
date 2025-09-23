import React, { useState, useEffect } from "react";
import axios from "axios";
import "./Learnings.css";

function Learning() {
  const [selectedTopic, setSelectedTopic] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [hoveredNews, setHoveredNews] = useState(null);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const [newsHeadlines, setNewsHeadlines] = useState([]);

  // --------- Static Topics ----------
  const learningTopics = [
    {
      id: 1,
      icon: "📈",
      title: "What is Stock?",
      summary: "Learn the fundamentals of stocks and equity ownership.",
      content: `
        <h3>Understanding Stocks</h3>
        <p>A stock represents a share in the ownership of a company. When you buy stock, you become a partial owner of that company and gain rights to its earnings and assets.</p>
        <ul>
          <li><strong>Ownership:</strong> Buying stock means owning a fraction of the company.</li>
          <li><strong>Dividends:</strong> Some companies share profits with shareholders.</li>
          <li><strong>Capital Gains:</strong> Profit earned by selling shares at a higher price.</li>
          <li><strong>Market Cap:</strong> Total value of all outstanding shares.</li>
        </ul>
        <div class="highlight">Tip: Stocks are ideal for long-term wealth creation.</div>
      `
    },
    {
      id: 2,
      icon: "💹",
      title: "How Trading Works",
      summary: "Understand the mechanics of buying and selling stocks.",
      content: `
        <h3>How Stock Trading Works</h3>
        <p>Trading involves buying and selling shares of publicly listed companies through stock exchanges.</p>
        <ul>
          <li><strong>Market Order:</strong> Buys/sells immediately at the current price.</li>
          <li><strong>Limit Order:</strong> Executes only when your target price is met.</li>
          <li><strong>Stop-Loss Order:</strong> Minimizes losses by selling when price falls.</li>
          <li><strong>After-Hours Trading:</strong> Trades made outside standard exchange hours.</li>
        </ul>
        <div class="highlight">Pro Tip: Always use stop-loss orders to manage risk!</div>
      `
    },
    {
      id: 3,
      icon: "🛡️",
      title: "Risk Management",
      summary: "Learn how to protect your investments and manage risk.",
      content: `
        <h3>Risk Management Strategies</h3>
        <p>Managing risk is critical for protecting your portfolio and achieving steady returns.</p>
        <ul>
          <li><strong>Diversification:</strong> Spread investments across sectors.</li>
          <li><strong>Position Sizing:</strong> Never invest too much in one asset.</li>
          <li><strong>Stop-Loss Orders:</strong> Protect capital by limiting downside.</li>
          <li><strong>Portfolio Rebalancing:</strong> Adjust allocations regularly.</li>
        </ul>
        <div class="highlight warning">Warning: High-risk trades without risk management can lead to significant losses.</div>
      `
    },
    {
      id: 4,
      icon: "🌱",
      title: "Long Term Investment",
      summary: "Discover the power of long-term wealth building.",
      content: `
        <h3>Why Long-Term Investing Works</h3>
        <p>Holding quality assets for years helps maximize returns and reduce volatility.</p>
        <ul>
          <li><strong>Compounding:</strong> Earnings generate further earnings over time.</li>
          <li><strong>Lower Taxes:</strong> Long-term capital gains are taxed less.</li>
          <li><strong>Reduced Stress:</strong> Less focus on daily market fluctuations.</li>
          <li><strong>Stability:</strong> Minimizes the effect of short-term volatility.</li>
        </ul>
        <div class="highlight success">Remember: Time in the market beats timing the market.</div>
      `
    }
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
        {learningTopics.map((topic) => (
          <div className="learning-card" key={topic.id}>
            <div className="icon">{topic.icon}</div>
            <h3>{topic.title}</h3>
            <p>{topic.summary}</p>
            <button onClick={() => openModal(topic)}>Learn More</button>
          </div>
        ))}
      </div>

      {/* News Section */}
      <h2 className="section-title">Top 10 News Headlines</h2>
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
            <div dangerouslySetInnerHTML={{ __html: selectedTopic.content }} />
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
