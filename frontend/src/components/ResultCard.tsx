"use client";
import { useState } from "react";
import { Copy, Check, Download } from "lucide-react";
import type { LinkResponse } from "../lib/api";

interface Props {
  result: LinkResponse;
}

function VerifiedBadge({ status }: { status: string }) {
  if (status === "verified") {
    return (
      <span className="badge badge-verified">
        <span className="dot-verified" />
        Verified
      </span>
    );
  }
  if (status === "unreachable") {
    return (
      <span className="badge badge-unreachable">
        <span className="dot-unreachable" />
        Unreachable
      </span>
    );
  }
  return (
    <span className="badge badge-pending">
      <span className="dot-pending" />
      Verifying…
    </span>
  );
}

export default function ResultCard({ result }: Props) {
  const [copied, setCopied] = useState(false);

  async function copyUrl() {
    await navigator.clipboard.writeText(result.short_url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  function downloadQr() {
    const link = document.createElement("a");
    link.href = `data:image/png;base64,${result.qr_code_base64}`;
    link.download = `shortly-${result.short_code}.png`;
    link.click();
  }

  return (
    <div className="result-card">
      {/* ── Short URL row ── */}
      <div className="short-url-row">
        <span className="short-url-text">{result.short_url}</span>
        <button
          id="copy-url-btn"
          className="btn-icon"
          onClick={copyUrl}
          title="Copy to clipboard"
        >
          {copied ? <Check size={15} style={{ color: "var(--accent)" }} /> : <Copy size={15} />}
        </button>
      </div>
      {copied && (
        <p className="copy-flash" style={{ marginTop: 6, paddingLeft: 4 }}>
          Copied!
        </p>
      )}

      {/* ── QR code ── */}
      <div className="qr-container">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={`data:image/png;base64,${result.qr_code_base64}`}
          alt={`QR code for ${result.short_url}`}
        />
      </div>

      {/* ── Meta row ── */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 12,
          flexWrap: "wrap",
        }}
      >
        <VerifiedBadge status={result.verified} />

        <div style={{ display: "flex", gap: 8 }}>
          {result.expires_at && (
            <span className="muted" style={{ fontSize: "0.75rem" }}>
              Expires{" "}
              {new Date(result.expires_at).toLocaleDateString("en-US", {
                month: "short",
                day: "numeric",
                hour: "numeric",
                minute: "2-digit",
              })}
            </span>
          )}
          <button
            id="download-qr-btn"
            className="btn btn-ghost"
            style={{ padding: "6px 12px", fontSize: "0.8125rem" }}
            onClick={downloadQr}
          >
            <Download size={13} />
            QR PNG
          </button>
        </div>
      </div>
    </div>
  );
}
