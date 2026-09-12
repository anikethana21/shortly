import type { Metadata } from "next";
import Link from "next/link";
import { Shield } from "lucide-react";

export const metadata: Metadata = {
  title: "Too Many Requests — Short.ly",
  description: "You have been temporarily rate-limited. Please slow down and try again shortly.",
};

export default function RateLimitedPage() {
  return (
    <div className="page-center">
      <div className="card" style={{ maxWidth: 440, width: "100%", textAlign: "center" }}>
        <div
          style={{
            width: 56,
            height: 56,
            borderRadius: "50%",
            background: "rgba(224,82,82,.08)",
            border: "1px solid rgba(224,82,82,.2)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            margin: "0 auto 20px",
          }}
        >
          <Shield size={24} style={{ color: "var(--error)" }} />
        </div>
        <h1 style={{ fontSize: "1.25rem", marginBottom: 10 }}>Slow down</h1>
        <p className="muted" style={{ marginBottom: 24, lineHeight: 1.7 }}>
          You have made too many requests in a short period. Please wait a moment
          before trying again. Check the{" "}
          <span className="mono" style={{ color: "var(--text)", fontSize: "0.875rem" }}>
            Retry-After
          </span>{" "}
          header for the exact wait time.
        </p>
        <Link href="/" className="btn btn-ghost" style={{ display: "inline-flex" }}>
          Back to home
        </Link>
      </div>
    </div>
  );
}
