import type { ReactNode } from "react";
import { Menu } from "lucide-react";
import { useState } from "react";
import { Sidebar, MobileBottomNav } from "@/components/layout/Sidebar";
import { NavLink, Link } from "react-router-dom";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";
import { DemoModeBadge } from "@/components/common/DemoModeBadge";
import {
  LayoutDashboard,
  Package,
  LineChart,
  BarChart3,
  AlertTriangle,
  ShoppingCart,
  FlaskConical,
  Settings,
} from "lucide-react";

const ALL_NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/inventory", label: "Inventory", icon: Package },
  { to: "/sales", label: "Sales Data", icon: BarChart3 },
  { to: "/forecasts", label: "Forecasts", icon: LineChart },
  { to: "/alerts", label: "Alerts", icon: AlertTriangle },
  { to: "/recommendations", label: "Recommendations", icon: ShoppingCart },
  { to: "/scenarios", label: "Scenario Simulator", icon: FlaskConical },
  { to: "/settings", label: "Settings", icon: Settings },
];

export function AppShell({ children, title }: { children: ReactNode; title?: string }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const { isGuest } = useAuth();

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />

      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="absolute inset-0 bg-black/40" onClick={() => setMobileOpen(false)} />
          <div className="relative z-10 h-full w-72 bg-card p-4">
            <Link
              to="/"
              onClick={() => setMobileOpen(false)}
              aria-label="StockPilot AI home"
              className="mb-4 inline-flex items-center rounded-lg bg-white p-1.5"
            >
              <img
                src="/assets/logo.png"
                alt="StockPilot AI — Inventory Intelligence"
                className="h-9 w-auto max-w-[170px] object-contain"
              />
            </Link>
            <nav className="space-y-1">
              {ALL_NAV_ITEMS.map(({ to, label, icon: Icon }) => (
                <NavLink
                  key={to}
                  to={to}
                  onClick={() => setMobileOpen(false)}
                  className={({ isActive }) =>
                    cn(
                      "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium",
                      isActive ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-muted"
                    )
                  }
                >
                  <Icon className="h-4 w-4" />
                  {label}
                </NavLink>
              ))}
            </nav>
          </div>
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-16 items-center gap-3 border-b border-border bg-card px-4 lg:px-8">
          <button
            className="rounded-md p-2 text-muted-foreground hover:bg-muted lg:hidden"
            onClick={() => setMobileOpen(true)}
            aria-label="Open navigation menu"
          >
            <Menu className="h-5 w-5" />
          </button>
          {title && <h1 className="text-lg font-semibold text-foreground">{title}</h1>}
          {isGuest && <DemoModeBadge className="ml-auto sm:ml-2" />}
        </header>

        <main className="flex-1 overflow-x-hidden px-4 pb-20 pt-6 lg:px-8 lg:pb-8">{children}</main>
      </div>

      <MobileBottomNav />
    </div>
  );
}