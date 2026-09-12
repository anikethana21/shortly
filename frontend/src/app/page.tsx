import type { Metadata } from "next";
import ShortenForm from "@/components/ShortenForm";

export const metadata: Metadata = {
  title: "Short.ly — Shorten your URL",
  description: "Create short links with analytics, QR codes, custom codes, and expiry timers.",
};

export default function HomePage() {
  return (
    <div className="page-center">
      <div style={{ width: "100%", maxWidth: 600, textAlign: "center", marginBottom: 40 }}>
        <h1 style={{ marginBottom: 12 }}>
          Short links that{" "}
          <span style={{ color: "var(--accent)" }}>mean something</span>
        </h1>
        <p className="muted" style={{ fontSize: "1rem" }}>
          Paste a URL, get a short link, QR code, and analytics — instantly.
        </p>
      </div>
      <ShortenForm />
    </div>
  );
}
