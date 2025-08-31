const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function fetchPositions() {
  const res = await fetch(`${API_BASE}/positions`);
  return res.json();
}

export async function fetchDailyPnL() {
  const res = await fetch(`${API_BASE}/pnl/daily`);
  return res.json();
}

export async function fetchTotalPnL() {
  const res = await fetch(`${API_BASE}/pnl/total`);
  return res.json();
}

export async function fetchTrends() {
  const res = await fetch(`${API_BASE}/trends`);
  return res.json();
}

export async function fetchSentiment() {
  const res = await fetch(`${API_BASE}/stats/sentiment`);
  return res.json();
}
