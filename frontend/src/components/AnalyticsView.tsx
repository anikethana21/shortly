"use client";
import { useEffect, useState } from "react";
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from "recharts";
import { getAnalytics, type AnalyticsResponse } from "../lib/api";

interface Props {
  shortCode: string;
}

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="card-sm" style={{ fontSize: "0.8125rem" }}>
      <p className="muted" style={{ marginBottom: 4 }}>{label}</p>
      <p style={{ fontFamily: "var(--mono)", color: "var(--accent)", fontWeight: 600 }}>
        {payload[0].value} clicks
      </p>
    </div>
  );
}

export default function AnalyticsView({ shortCode }: Props) {
  const [data, setData] = useState<AnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    setError("");
    getAnalytics(shortCode)
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [shortCode]);

  if (loading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", padding: "40px 0" }}>
        <span className="spinner" style={{ width: 24, height: 24 }} />
      </div>
    );
  }

  if (error || !data) {
    return <div className="empty-state"><p className="error-text">{error || "No data."}</p></div>;
  }

  const chartData = data.clicks_by_date.map((d) => ({
    date: new Date(d.date).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
    clicks: d.count,
  }));

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      {/* ── Summary ── */}
      <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
        <div className="card-sm" style={{ flex: 1, minWidth: 120 }}>
          <p className="muted" style={{ fontSize: "0.75rem", marginBottom: 4 }}>TOTAL CLICKS</p>
          <p style={{ fontFamily: "var(--mono)", fontSize: "1.5rem", fontWeight: 700, color: "var(--accent)" }}>
            {data.total_clicks.toLocaleString()}
          </p>
        </div>
        <div className="card-sm" style={{ flex: 1, minWidth: 120 }}>
          <p className="muted" style={{ fontSize: "0.75rem", marginBottom: 4 }}>SHORT CODE</p>
          <p style={{ fontFamily: "var(--mono)", fontSize: "1.5rem", fontWeight: 700 }}>
            {data.short_code}
          </p>
        </div>
      </div>

      {/* ── Clicks over time chart ── */}
      <div className="chart-container">
        <h3 style={{ marginBottom: 20, color: "var(--muted-alt)" }}>Clicks over time</h3>
        {chartData.length === 0 ? (
          <p className="muted" style={{ textAlign: "center", padding: "32px 0" }}>No click data yet.</p>
        ) : (
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={chartData} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="clickGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#4E9F6E" stopOpacity={0.25} />
                  <stop offset="95%" stopColor="#4E9F6E" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="#222B25" strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="date" tick={{ fill: "#6E8276", fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: "#6E8276", fontSize: 11 }} axisLine={false} tickLine={false} allowDecimals={false} />
              <Tooltip content={<CustomTooltip />} />
              <Area
                type="monotone"
                dataKey="clicks"
                stroke="#4E9F6E"
                strokeWidth={2}
                fill="url(#clickGrad)"
                dot={false}
                activeDot={{ r: 4, fill: "#4E9F6E" }}
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* ── Top referrers ── */}
      <div className="chart-container">
        <h3 style={{ marginBottom: 16, color: "var(--muted-alt)" }}>Top referrers</h3>
        {data.top_referrers.length === 0 ? (
          <p className="muted" style={{ textAlign: "center", padding: "20px 0" }}>No referrer data yet.</p>
        ) : (
          <table style={{ fontSize: "0.875rem" }}>
            <thead>
              <tr>
                <th style={{ textAlign: "left", color: "var(--muted)", padding: "0 0 10px", fontWeight: 600, fontSize: "0.75rem", letterSpacing: "0.05em", textTransform: "uppercase" }}>
                  Referrer
                </th>
                <th style={{ textAlign: "right", color: "var(--muted)", padding: "0 0 10px", fontWeight: 600, fontSize: "0.75rem", letterSpacing: "0.05em", textTransform: "uppercase" }}>
                  Clicks
                </th>
              </tr>
            </thead>
            <tbody>
              {data.top_referrers.map((r, i) => (
                <tr key={i}>
                  <td style={{ padding: "8px 0", borderBottom: "1px solid var(--border)", color: "var(--muted-alt)" }}>
                    {r.referrer}
                  </td>
                  <td style={{ padding: "8px 0", borderBottom: "1px solid var(--border)", textAlign: "right", fontFamily: "var(--mono)", fontWeight: 600 }}>
                    {r.count.toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
