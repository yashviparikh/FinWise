from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import pandas as pd
import yfinance as yf


RANGE_TO_PERIOD = {
    "3M": "3mo",
    "6M": "6mo",
    "1Y": "1y",
}


def normalize_symbol(symbol: str) -> str:
    raw = (symbol or "").strip().upper()
    if not raw:
        return ""
    return raw if raw.endswith(".NS") else f"{raw}.NS"


def build_symbol_candidates(symbol: str) -> list[str]:
    raw = (symbol or "").strip().upper()
    if not raw:
        return []

    candidates: list[str] = []
    for sym in (raw, normalize_symbol(raw)):
        if sym and sym not in candidates:
            candidates.append(sym)

    if raw.endswith(".NS"):
        base = raw[:-3]
        if base and base not in candidates:
            candidates.append(base)
    else:
        bo = f"{raw}.BO"
        if bo not in candidates:
            candidates.append(bo)

    return candidates


def _coerce_history_frame(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=["date", "close"])

    out = df.reset_index().copy()
    if isinstance(out.columns, pd.MultiIndex):
        out.columns = [
            "__".join([str(x).strip() for x in c if str(x).strip()])
            for c in out.columns
        ]
    else:
        out.columns = [str(c).strip() for c in out.columns]

    if out.empty or len(out.columns) == 0:
        return pd.DataFrame(columns=["date", "close"])

    lower_map = {str(c).lower(): c for c in out.columns}

    date_col = None
    for key in ("date", "datetime", "index"):
        if key in lower_map:
            date_col = lower_map[key]
            break
    if date_col is None:
        date_like = [c for c in out.columns if "date" in str(c).lower()]
        date_col = date_like[0] if date_like else out.columns[0]

    close_col = None
    for key in ("close", "adj close", "adj_close"):
        if key in lower_map:
            close_col = lower_map[key]
            break
    if close_col is None:
        close_like = [c for c in out.columns if "close" in str(c).lower()]
        close_col = close_like[0] if close_like else None
    if close_col is None:
        num_cols = out.select_dtypes(include=["number"]).columns.tolist()
        close_col = num_cols[0] if num_cols else None
    if close_col is None:
        return pd.DataFrame(columns=["date", "close"])

    out["Date"] = pd.to_datetime(out[date_col], errors="coerce")
    out["Close"] = pd.to_numeric(out[close_col], errors="coerce")
    out = out.dropna(subset=["Date", "Close"]).sort_values("Date")
    if out.empty:
        return pd.DataFrame(columns=["date", "close"])

    return pd.DataFrame(
        {
            "date": out["Date"].dt.strftime("%Y-%m-%d"),
            "close": out["Close"].round(2),
        }
    )


def fetch_history(symbol: str, range_key: str = "6M") -> dict[str, Any]:
    candidates = build_symbol_candidates(symbol)
    if not candidates:
        return {"error": "Missing symbol"}

    period = RANGE_TO_PERIOD.get((range_key or "").upper(), "6mo")
    for ticker in candidates:
        data = yf.download(
            ticker,
            period=period,
            interval="1d",
            auto_adjust=False,
            progress=False,
        )
        series = _coerce_history_frame(data)
        if not series.empty:
            return {
                "symbol": ticker,
                "range": (range_key or "6M").upper(),
                "series": series.to_dict(orient="records"),
            }

    return {"error": f"No historical data found for {symbol}"}


def _pick_on_or_after(df: pd.DataFrame, dt: pd.Timestamp) -> tuple[pd.Timestamp | None, float | None]:
    candidates = df[df["date_obj"] >= dt]
    if candidates.empty:
        return None, None
    row = candidates.iloc[0]
    return row["date_obj"], float(row["close"])


def simulate_trade(payload: dict[str, Any]) -> tuple[dict[str, Any], int]:
    symbol = payload.get("symbol", "")
    buy_date_raw = payload.get("buy_date")
    sell_date_raw = payload.get("sell_date")
    capital = 10000.0
    quantity_raw = payload.get("quantity", payload.get("qty"))

    ticker = normalize_symbol(symbol)
    if not ticker:
        return {"error": "symbol is required"}, 400
    if not buy_date_raw or not sell_date_raw:
        return {"error": "buy_date and sell_date are required"}, 400

    try:
        buy_date = pd.to_datetime(buy_date_raw).normalize()
        sell_date = pd.to_datetime(sell_date_raw).normalize()
    except Exception:
        return {"error": "Invalid date format. Use YYYY-MM-DD"}, 400

    if sell_date <= buy_date:
        return {"error": "SELL date must be after BUY date"}, 400

    start = (buy_date - timedelta(days=7)).strftime("%Y-%m-%d")
    end = (sell_date + timedelta(days=7)).strftime("%Y-%m-%d")
    frame = pd.DataFrame()
    used_ticker = ticker
    for candidate in build_symbol_candidates(symbol):
        data = yf.download(
            candidate,
            start=start,
            end=end,
            interval="1d",
            auto_adjust=False,
            progress=False,
        )
        candidate_frame = _coerce_history_frame(data)
        if not candidate_frame.empty:
            frame = candidate_frame
            used_ticker = candidate
            break
    if frame.empty:
        return {"error": f"No historical data found for {symbol}"}, 404

    frame["date_obj"] = pd.to_datetime(frame["date"], errors="coerce")
    frame = frame.dropna(subset=["date_obj"]).sort_values("date_obj")
    if frame.empty:
        return {"error": f"No valid trading dates for {ticker}"}, 404

    buy_effective_date, buy_price = _pick_on_or_after(frame, buy_date)
    sell_effective_date, sell_price = _pick_on_or_after(frame, sell_date)

    if buy_price is None or sell_price is None:
        return {"error": "Unable to resolve trading prices for selected dates"}, 400
    if sell_effective_date <= buy_effective_date:
        return {"error": "SELL trading day must be after BUY trading day"}, 400

    if quantity_raw is not None:
        try:
            quantity = float(quantity_raw)
        except Exception:
            return {"error": "quantity must be a number"}, 400
        if quantity <= 0:
            return {"error": "quantity must be positive"}, 400
        invested_amount = quantity * buy_price
    else:
        quantity = capital / buy_price
        invested_amount = capital

    final_value = quantity * sell_price
    return_percent = ((final_value - invested_amount) / invested_amount) * 100

    return (
        {
            "symbol": used_ticker,
            "buy_date": buy_effective_date.strftime("%Y-%m-%d"),
            "sell_date": sell_effective_date.strftime("%Y-%m-%d"),
            "buy_price": round(buy_price, 2),
            "sell_price": round(sell_price, 2),
            "shares": round(quantity, 6),
            "quantity": round(quantity, 6),
            "invested_amount": round(invested_amount, 2),
            "final_value": round(final_value, 2),
            "return_percent": round(return_percent, 2),
        },
        200,
    )
