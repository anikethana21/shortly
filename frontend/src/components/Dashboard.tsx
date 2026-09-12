"use client";
import { useEffect, useState } from "react";
import { ExternalLink, BarChart2 } from "lucide-react";
import { getMyLinks, type LinkRecord } from "../lib/api";
import AnalyticsView from "./AnalyticsView";

function VerifiedDot({ status }: { status: string }) {
  if (status === "verified")    return <span className="dot-verified"    title="Verified" />;
  if (status === "unreachable") return <span className="dot-unreachable" title="Unreachable" />;
  return <span className="dot-pending" title="Verifying…" />;
}

function truncate(s: string, n = 40) {
  return s.length > n ? s.slice(0, n) + "…" : s;
}

function fmtDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short", day: "numeric", year: "numeric",
  });
}

function fmtExpiry(iso: string | null) {
  if (!iso) return <span className="muted">—</span>;
  const d = new Date(iso);
  const past = d < new Date();
  return (
    <span style={{ color: past ? "var(--error)" : "var(--muted)" }}>
      {fmtDate(iso)}
    </span>
  );
}

export default function Dashboard() {
  const [links, setLinks] = useState<LinkRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState<string | null>(null);

  useEffect(() => {
    getMyLinks()
      .then(setLinks)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", padding: "60px 0" }}>
        <span className="spinner" style={{ width: 28, height: 28 }} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="empty-state">
        <p className="error-text">{error}</p>
      </div>
    );
  }

  if (links.length === 0) {
    return (
      <div className="empty-state">
        <p>No links yet. Head to the <a href="/">home page</a> to create one.</p>
      </div>
    );
  }

  return (
    <>
      <div className="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>Code</th>
              <th>Destination</th>
              <th>Created</th>
              <th>Expires</th>
              <th style={{ textAlign: "right" }}>Clicks</th>
              <th style={{ textAlign: "center" }}>Status</th>
              <th style={{ textAlign: "center" }}>Analytics</th>
            </tr>
          </thead>
          <tbody>
            {links.map((link) => (
              <tr
                key={link.short_code}
                onClick={() => setSelected(link.short_code === selected ? null : link.short_code)}
                style={selected === link.short_code ? { background: "rgba(78,159,110,.06)" } : {}}
              >
                <td>
                  <span className="mono" style={{ color: "var(--accent)", fontSize: "0.875rem" }}>
                    {link.short_code}
                  </span>
                  {link.is_custom && (
                    <span className="badge badge-verified" style={{ marginLeft: 8, fontSize: "0.65rem" }}>
                      custom
                    </span>
                  )}
                </td>
                <td>
                  <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <a
                      href={link.long_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="muted"
                      onClick={(e) => e.stopPropagation()}
                    >
                      {truncate(link.long_url)}
                    </a>
                    <ExternalLink size={11} style={{ color: "var(--muted)", flexShrink: 0 }} />
                  </div>
                </td>
                <td className="muted">{fmtDate(link.created_at)}</td>
                <td>{fmtExpiry(link.expires_at)}</td>
                <td style={{ textAlign: "right", fontFamily: "var(--mono)", fontWeight: 600 }}>
                  {link.click_count.toLocaleString()}
                </td>
                <td style={{ textAlign: "center" }}>
                  <VerifiedDot status={link.verified} />
                </td>
                <td style={{ textAlign: "center" }}>
                  <BarChart2
                    size={15}
                    style={{ color: selected === link.short_code ? "var(--accent)" : "var(--muted)" }}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* ── Analytics drawer ── */}
      {selected && (
        <div style={{ marginTop: 24, animation: "slideUp 200ms ease" }}>
          <AnalyticsView shortCode={selected} />
        </div>
      )}
    </>
  );
}
