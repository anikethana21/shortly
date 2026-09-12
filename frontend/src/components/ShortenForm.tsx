"use client";
import { useState } from "react";
import { ChevronDown, ChevronUp, AlertCircle } from "lucide-react";
import { createLink, type CreateLinkPayload, type LinkResponse } from "../lib/api";
import ResultCard from "./ResultCard";

const EXPIRY_OPTIONS = [
  { label: "No expiry", value: "" },
  { label: "15 minutes", value: "15" },
  { label: "1 hour", value: "60" },
  { label: "24 hours", value: "1440" },
  { label: "7 days", value: "10080" },
  { label: "30 days", value: "43200" },
];

export default function ShortenForm() {
  const [longUrl, setLongUrl] = useState("");
  const [customCode, setCustomCode] = useState("");
  const [expiry, setExpiry] = useState("");
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<LinkResponse | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setResult(null);

    if (!longUrl.trim()) {
      setError("Please enter a URL.");
      return;
    }

    const payload: CreateLinkPayload = { long_url: longUrl.trim() };
    if (customCode.trim()) payload.custom_code = customCode.trim();
    if (expiry) payload.expires_in_minutes = Number(expiry);

    setLoading(true);
    try {
      const res = await createLink(payload);
      setResult(res);
      setLongUrl("");
      setCustomCode("");
      setExpiry("");
      setShowAdvanced(false);
    } catch (err: any) {
      setError(err.message ?? "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ width: "100%", maxWidth: 600 }}>
      <form onSubmit={handleSubmit} className="card" style={{ display: "flex", flexDirection: "column", gap: 0 }}>
        {/* ── URL input ── */}
        <div className="form-group" style={{ marginBottom: 20 }}>
          <label className="form-label">Long URL</label>
          <input
            id="long-url-input"
            className="input"
            type="url"
            placeholder="https://example.com/very/long/url"
            value={longUrl}
            onChange={(e) => setLongUrl(e.target.value)}
            disabled={loading}
            autoFocus
          />
        </div>

        {/* ── Advanced toggle ── */}
        <button
          type="button"
          className="advanced-toggle"
          onClick={() => setShowAdvanced((s) => !s)}
          id="advanced-options-toggle"
          style={{ marginBottom: 12 }}
        >
          {showAdvanced ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          Advanced options
        </button>

        {/* ── Advanced panel ── */}
        <div className={`advanced-panel ${showAdvanced ? "open" : "closed"}`}>
          <div style={{ paddingTop: 4, display: "flex", flexDirection: "column", gap: 16 }}>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">Custom code</label>
              <input
                id="custom-code-input"
                className="input input-mono"
                type="text"
                placeholder="my-brand (3–20 alphanumeric)"
                value={customCode}
                onChange={(e) => setCustomCode(e.target.value)}
                disabled={loading}
                maxLength={20}
              />
            </div>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">Expires</label>
              <select
                id="expiry-select"
                className="input"
                value={expiry}
                onChange={(e) => setExpiry(e.target.value)}
                disabled={loading}
              >
                {EXPIRY_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div style={{ height: 16 }} />
        </div>

        {/* ── Error ── */}
        {error && (
          <div className="form-error" style={{ marginBottom: 12 }}>
            <AlertCircle size={14} />
            {error}
          </div>
        )}

        {/* ── Submit ── */}
        <button
          id="shorten-btn"
          type="submit"
          className="btn btn-primary"
          disabled={loading}
          style={{ width: "100%", justifyContent: "center", marginTop: 4 }}
        >
          {loading ? (
            <>
              <span className="spinner" />
              Shortening…
            </>
          ) : (
            "Shorten"
          )}
        </button>
      </form>

      {/* ── Result ── */}
      {result && <ResultCard result={result} />}
    </div>
  );
}
