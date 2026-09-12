"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Link2, LayoutDashboard } from "lucide-react";

export default function Navbar() {
  const path = usePathname();

  return (
    <nav className="navbar">
      <Link href="/" className="navbar-logo">
        short.ly
      </Link>
      <div className="navbar-links">
        <Link
          href="/"
          className={`btn btn-ghost ${path === "/" ? "active" : ""}`}
          style={path === "/" ? { color: "var(--accent)", borderColor: "var(--accent)" } : {}}
        >
          <Link2 size={15} />
          Shorten
        </Link>
        <Link
          href="/dashboard"
          className={`btn btn-ghost ${path === "/dashboard" ? "active" : ""}`}
          style={path === "/dashboard" ? { color: "var(--accent)", borderColor: "var(--accent)" } : {}}
        >
          <LayoutDashboard size={15} />
          Dashboard
        </Link>
      </div>
    </nav>
  );
}
