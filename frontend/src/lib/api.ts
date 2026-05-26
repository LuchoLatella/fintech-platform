/**
 * Cliente API centralizado.
 * Todos los requests al backend pasan por acá.
 */
import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const WS_URL  = process.env.NEXT_PUBLIC_WS_URL  || "ws://localhost:8000";

export const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  timeout: 15000,
});

// Inyectar token JWT en cada request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Refresh automático si el token vence
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    if (error.response?.status === 401) {
      const refresh = localStorage.getItem("refresh_token");
      if (refresh) {
        try {
          const res = await axios.post(`${API_URL}/api/v1/auth/refresh`, null, {
            params: { refresh_tok: refresh },
          });
          localStorage.setItem("access_token", res.data.access_token);
          localStorage.setItem("refresh_token", res.data.refresh_token);
          error.config.headers.Authorization = `Bearer ${res.data.access_token}`;
          return axios(error.config);
        } catch {
          localStorage.clear();
          window.location.href = "/login";
        }
      }
    }
    return Promise.reject(error);
  }
);

// ── Endpoints tipados ──────────────────────────────────────────────────────────
export const authAPI = {
  login:    (email: string, password: string) =>
    api.post("/auth/login", new URLSearchParams({ username: email, password })),
  register: (data: { email: string; username: string; password: string; full_name?: string }) =>
    api.post("/auth/register", data),
  me:       () => api.get("/auth/me"),
  logout:   () => api.post("/auth/logout"),
};

export const marketAPI = {
  quote:       (symbol: string) => api.get(`/market/quote/${symbol}`),
  history:     (symbol: string, timeframe = "1d") => api.get(`/market/history/${symbol}`, { params: { timeframe } }),
  batchQuotes: (symbols: string[]) => api.get("/market/quotes/batch", { params: { symbols: symbols.join(",") } }),
  search:      (q: string, asset_class?: string) => api.get("/market/search", { params: { q, asset_class } }),
  watchlists:  () => api.get("/market/watchlists"),
  addToWatchlist:      (watchlist_id: string, asset_id: string) => api.post(`/market/watchlists/${watchlist_id}/items`, null, { params: { asset_id } }),
  removeFromWatchlist: (watchlist_id: string, asset_id: string) => api.delete(`/market/watchlists/${watchlist_id}/items/${asset_id}`),
};

export const argentinaAPI = {
  snapshot:      () => api.get("/argentina/snapshot"),
  dolar:         () => api.get("/argentina/dolar"),
  riesgoPais:    () => api.get("/argentina/riesgo-pais"),
  bcra:          () => api.get("/argentina/bcra"),
  oportunidades: () => api.get("/argentina/oportunidades"),
};

export const signalsAPI = {
  list:     (params?: { signal_type?: string; asset_class?: string; min_confidence?: number }) =>
    api.get("/signals/", { params }),
  analyze:  (symbol: string, timeframe = "1d") => api.get(`/signals/analyze/${symbol}`, { params: { timeframe } }),
  ranking:  (top = 10, market?: string) => api.get("/signals/ranking", { params: { top, market } }),
};

export const portfolioAPI = {
  list:            () => api.get("/portfolio/"),
  create:          (data: any) => api.post("/portfolio/", data),
  positions:       (id: string) => api.get(`/portfolio/${id}/positions`),
  transactions:    (id: string) => api.get(`/portfolio/${id}/transactions`),
  addTransaction:  (id: string, data: any) => api.post(`/portfolio/${id}/transactions`, data),
  risk:            (id: string) => api.get(`/portfolio/${id}/risk`),
};

export const analysisAPI = {
  technical:   (symbol: string, timeframe = "1d") => api.get(`/analysis/technical/${symbol}`, { params: { timeframe } }),
  fundamental: (symbol: string) => api.get(`/analysis/fundamental/${symbol}`),
  screener:    (params: any) => api.get("/analysis/screener", { params }),
};

// ── WebSocket helpers ─────────────────────────────────────────────────────────
export function createPriceSocket(symbols: string[], onMessage: (data: any) => void): WebSocket {
  const ws = new WebSocket(`${WS_URL}/ws/v1/quotes?symbols=${symbols.join(",")}`);
  ws.onmessage = (e) => onMessage(JSON.parse(e.data));
  return ws;
}

export function createAlertSocket(token: string, onMessage: (data: any) => void): WebSocket {
  const ws = new WebSocket(`${WS_URL}/ws/v1/alerts`);
  ws.onopen = () => ws.send(token);
  ws.onmessage = (e) => onMessage(JSON.parse(e.data));
  return ws;
}