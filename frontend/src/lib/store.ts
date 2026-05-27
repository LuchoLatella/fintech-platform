/**
 * Store global con Zustand.
 * Estado compartido: usuario, precios en tiempo real, señales, Argentina.
 */
import { create } from "zustand";

interface User {
  id: string;
  email: string;
  username: string;
  full_name?: string;
  plan: string;
}

interface Quote {
  symbol: string;
  price: number;
  change_pct?: number;
  volume?: number;
}

interface ArgSnapshot {
  dolar: { mep?: number; ccl?: number; blue?: number; oficial?: number; tarjeta?: number };
  riesgo_pais: number;
  inflacion_mensual?: number;
  tasa_politica_monetaria?: number;
  opportunities: any[];
}

interface AppStore {
  // Auth
  user: User | null;
  token: string | null;
  setUser: (user: User | null) => void;
  setToken: (token: string | null) => void;
  logout: () => void;

  // Precios en tiempo real
  quotes: Record<string, Quote>;
  updateQuote: (quote: Quote) => void;

  // Argentina
  argSnapshot: ArgSnapshot | null;
  setArgSnapshot: (snap: ArgSnapshot) => void;

  // UI
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
  selectedPortfolioId: string | null;
  setSelectedPortfolioId: (id: string | null) => void;
}

export const useAppStore = create<AppStore>((set) => ({
  user: null,
  token: typeof window !== "undefined" ? localStorage.getItem("access_token") : null,
  setUser: (user) => set({ user }),
  setToken: (token) => {
    if (token) localStorage.setItem("access_token", token);
    else localStorage.removeItem("access_token");
    set({ token });
  },
  logout: () => {
    localStorage.clear();
    set({ user: null, token: null });
  },

  quotes: {},
  updateQuote: (quote) =>
    set((state) => ({ quotes: { ...state.quotes, [quote.symbol]: quote } })),

  argSnapshot: null,
  setArgSnapshot: (snap) => set({ argSnapshot: snap }),

  sidebarOpen: true,
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  selectedPortfolioId: null,
  setSelectedPortfolioId: (id) => set({ selectedPortfolioId: id }),
}));