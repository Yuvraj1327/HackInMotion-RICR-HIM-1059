import { NavLink, Link } from "react-router-dom";
import {
  LayoutDashboard,
  Package,
  LineChart,
  BarChart3,
  AlertTriangle,
  ShoppingCart,
  FlaskConical,
  Settings,
  LogOut,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";
import { DemoModeBadge } from "@/components/common/DemoModeBadge";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/inventory", label: "Inventory", icon: Package },
  { to: "/sales", label: "Sales Data", icon: BarChart3 },
  { to: "/forecasts", label: "Forecasts", icon: LineChart },
  { to: "/alerts", label: "Alerts", icon: AlertTriangle },
  { to: "/recommendations", label: "Recommendations", icon: ShoppingCart },
  { to: "/scenarios", label: "Scenario Simulator", icon: FlaskConical },
  { to: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const { businessEmail, isGuest, logout } = useAuth();

  return (
    <aside className="hidden h-screen w-64 shrink-0 flex-col border-r border-border bg-card lg:flex">
      <div className="flex h-16 items-center border-b border-border px-4">
        <Link to="/" aria-label="StockPilot AI home" className="flex items-center rounded-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary">
          <img src="/assets/logo.png" alt="StockPilot AI — Inventory Intelligence" className="h-14 w-auto" />
        </Link>
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto p-3">
        {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )
            }
          >
            <Icon className="h-4 w-4 shrink-0" />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-border p-3">
        {isGuest && (
          <div className="mb-2 px-3">
            <DemoModeBadge />
          </div>
        )}
        <div className="flex items-center gap-2 rounded-md px-3 py-2">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted text-xs font-semibold text-foreground">
            {isGuest ? "G" : (businessEmail?.[0]?.toUpperCase() ?? "?")}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-xs font-medium text-foreground">
              {isGuest ? "Guest Demo Account" : businessEmail}
            </p>
          </div>
        </div>
        <button
          onClick={() => logout()}
          className="mt-1 flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-muted hover:text-foreground"
        >
          <LogOut className="h-4 w-4" />
          Log out
        </button>
      </div>
    </aside>
  );
}

export function MobileBottomNav() {
  const primaryItems = NAV_ITEMS.slice(0, 5);
  return (
    <nav className="fixed bottom-0 left-0 right-0 z-40 flex border-t border-border bg-card lg:hidden">
      {primaryItems.map(({ to, label, icon: Icon }) => (
        <NavLink
          key={to}
          to={to}
          className={({ isActive }) =>
            cn(
              "flex flex-1 flex-col items-center gap-0.5 py-2 text-[10px] font-medium",
              isActive ? "text-primary" : "text-muted-foreground"
            )
          }
        >
          <Icon className="h-5 w-5" />
          {label.split(" ")[0]}
        </NavLink>
      ))}
    </nav>
  );
}