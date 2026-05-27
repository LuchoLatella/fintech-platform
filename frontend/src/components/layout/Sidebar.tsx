"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, TrendingUp, Brain, Briefcase,
  Flag, Bell, BarChart2, Settings, ChevronLeft, ChevronRight
} from "lucide-react";
import { useAppStore } from "@/lib/store";
import clsx from "clsx";

const NAV = [
  { href: "/",           icon: LayoutDashboard, label: "Dashboard"    },
  { href: "/mercado",    icon: TrendingUp,       label: "Mercado"      },
  { href: "/senales",    icon: Brain,            label: "Señales IA"   },
  { href: "/portafolio", icon: Briefcase,        label: "Portafolio"   },
  { href: "/argentina",  icon: Flag,             label: "Argentina"    },
  { href: "/alertas",    icon: Bell,             label: "Alertas"      },
  { href: "/analisis",   icon: BarChart2,        label: "Análisis"     },
];

export function Sidebar() {
  const pathname = usePathname();
  const { sidebarOpen, setSidebarOpen } = useAppStore();

  return (
    <aside
      className={clsx(
        "flex flex-col bg-bg-surface border-r border-bg-border transition-all duration-300 shrink-0",
        sidebarOpen ? "w-56" : "w-16"
      )}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 py-5 border-b border-bg-border">
        <div className="w-8 h-8 rounded-lg bg-accent-green/10 border border-accent-green/30 flex items-center justify-center shrink-0">
          <TrendingUp size={15} className="text-accent-green" />
        </div>
        {sidebarOpen && (
          <span className="font-display text-sm font-medium text-text-primary tracking-wide truncate">
            FINTECH<span className="text-accent-green">.</span>AI
          </span>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 py-4 space-y-1 px-2">
        {NAV.map(({ href, icon: Icon, label }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={clsx(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-150 group",
                active
                  ? "bg-accent-green/10 text-accent-green"
                  : "text-text-secondary hover:text-text-primary hover:bg-bg-hover"
              )}
            >
              <Icon size={17} className="shrink-0" />
              {sidebarOpen && (
                <span className="text-sm font-medium truncate">{label}</span>
              )}
              {active && sidebarOpen && (
                <div className="ml-auto w-1.5 h-1.5 rounded-full bg-accent-green" />
              )}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-2 pb-4 space-y-1 border-t border-bg-border pt-3">
        <Link
          href="/configuracion"
          className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-text-secondary hover:text-text-primary hover:bg-bg-hover transition-all"
        >
          <Settings size={17} className="shrink-0" />
          {sidebarOpen && <span className="text-sm">Configuración</span>}
        </Link>
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-text-muted hover:text-text-secondary hover:bg-bg-hover transition-all"
        >
          {sidebarOpen
            ? <><ChevronLeft size={17} /><span className="text-sm">Colapsar</span></>
            : <ChevronRight size={17} />
          }
        </button>
      </div>
    </aside>
  );
}
