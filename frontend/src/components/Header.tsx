import { NavLink } from "react-router-dom";
import { ProviderBadge } from "./ProviderBadge";
import { cn } from "@/lib/utils";

const links = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/runbooks", label: "Runbooks" },
  { to: "/admin/settings", label: "Admin" },
];

export function Header() {
  return (
    <header className="border-b border-border bg-card">
      <div className="container flex h-14 items-center justify-between">
        <div className="flex items-center gap-8">
          <div className="flex items-center gap-2">
            <div className="h-7 w-7 rounded bg-primary/10 flex items-center justify-center text-primary font-bold">
              R
            </div>
            <span className="font-semibold tracking-tight">Ranger</span>
            <span className="text-xs text-muted-foreground">IoT incident triage</span>
          </div>
          <nav className="flex items-center gap-1">
            {links.map((l) => (
              <NavLink
                key={l.to}
                to={l.to}
                end={l.end}
                className={({ isActive }) =>
                  cn(
                    "px-3 py-1.5 text-sm rounded-md transition-colors",
                    isActive
                      ? "bg-accent text-accent-foreground"
                      : "text-muted-foreground hover:text-foreground",
                  )
                }
              >
                {l.label}
              </NavLink>
            ))}
          </nav>
        </div>
        <ProviderBadge />
      </div>
    </header>
  );
}
