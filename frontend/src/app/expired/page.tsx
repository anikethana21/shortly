import type { Metadata } from "next";
import Link from "next/link";
import { Clock } from "lucide-react";

export const metadata: Metadata = {
  title: "Link Expired — Short.ly",
  description: "This short link has expired and is no longer available.",
};

export default function ExpiredPage() {
  return (
    <div className="page-center">
      <div className="card" style={{ maxWidth: 440, width: "100%", textAlign: "center" }}>
        <div
          style={{
            width: 56,
            height: 56,
            borderRadius: "50%",
            background: "rgba(110,130,118,.1)",
            border: "1px solid var(--border)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            margin: "0 auto 20px",
          }}
        >
          <Clock size={24} style={{ color: "var(--muted)" }} />
        </div>
        <h1 style={{ fontSize: "1.25rem", marginBottom: 10 }}>Link expired</h1>
        <p className="muted" style={{ marginBottom: 24, lineHeight: 1.7 }}>
          This short link has passed its expiry time and is no longer active.
          The destination has not been deleted.
        </p>
        <Link href="/" className="btn btn-primary" style={{ display: "inline-flex" }}>
          Create a new link
        </Link>
      </div>
    </div>
  );
}
