import Link from "next/link";
import { useRouter } from "next/router";
import { Activity, LayoutDashboard, TrendingUp } from "lucide-react";
import ModelSelector from "../dashboard/ModelSelector";
import clsx from "clsx";

const NAV = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/portfolio", label: "Portfolio", icon: TrendingUp },
];

export default function Navbar() {
  const { pathname } = useRouter();

  return (
    <header className="sticky top-0 z-50 border-b border-bg-border bg-bg-secondary/80 backdrop-blur-md">
      <div className="max-w-screen-2xl mx-auto px-4 h-14 flex items-center justify-between gap-4">
        {/* Logo */}
        <div className="flex items-center gap-2 shrink-0">
          <Activity className="w-5 h-5 text-accent-purple" />
          <span className="font-mono font-semibold text-text-primary tracking-wide">
            AI<span className="text-accent-purple">Trade</span>
          </span>
        </div>

        {/* Nav links */}
        <nav className="flex items-center gap-1">
          {NAV.map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              className={clsx(
                "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors",
                pathname === href
                  ? "bg-accent-purple/15 text-accent-purple"
                  : "text-text-secondary hover:text-text-primary hover:bg-bg-card"
              )}
            >
              <Icon className="w-4 h-4" />
              {label}
            </Link>
          ))}
        </nav>

        {/* Model selector */}
        <ModelSelector />
      </div>
    </header>
  );
}
