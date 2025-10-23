const API_BASE_URL = "http://127.0.0.1:5000";

export async function fetchAutocomplete(query) {
  const res = await fetch(`${API_BASE_URL}/autocomplete?q=${query}`);
  return res.json();
}

export async function fetchStockPrice(symbol) {
  const res = await fetch(`${API_BASE_URL}/get-price/${symbol}`);
  return res.json();
}

export async function fetchWatchlist(userId) {
  const res = await fetch(`${API_BASE_URL}/get_watchlist/${userId}`);
  return res.json();
}

export async function addToWatchlist(data) {
  const res = await fetch(`${API_BASE_URL}/add_to_watchlist`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function removeFromWatchlist(userId, stockId) {
  const res = await fetch(`${API_BASE_URL}/remove_from_watchlist/${userId}/${stockId}`, {
    method: "POST",
  });
  return res.json();
}

export async function buyStock(data) {
  const res = await fetch(`${API_BASE_URL}/buy`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function sellStock(data) {
  const res = await fetch(`${API_BASE_URL}/sell`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function fetchPortfolio(userId) {
  const res = await fetch(`${API_BASE_URL}/portfolio/${userId}`);
  return res.json();
}
