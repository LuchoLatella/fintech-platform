import type { Metadata } from "next";
import "./globals.css";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import { Toaster } from "react-hot-toast";

export const metadata: Metadata = {
  title: "Fintech Platform — Inteligencia de Inversión",
  description: "Análisis financiero e IA para detectar oportunidades de inversión",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body className="bg-bg-base text-text-primary font-body">
        <div className="flex h-screen overflow-hidden">
          <Sidebar />
          <div className="flex flex-col flex-1 overflow-hidden">
            <Topbar />
            <main className="flex-1 overflow-y-auto p-6 bg-grid-pattern bg-grid">
              {children}
            </main>
          </div>
        </div>
        <Toaster
          position="bottom-right"
          toastOptions={{
            style: { background: "#111926", color: "#E8EDF5", border: "1px solid #1C2A3A" },
          }}
        />
      </body>
    </html>
  );
}
