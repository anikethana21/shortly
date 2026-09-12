/**
 * All API calls go through the api-gateway.
 * Never calls link-service or redirect-service directly.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function getOwnerToken(): string {
  if (typeof window === "undefined") return "";
  let token = localStorage.getItem("shortly_owner_token");
  if (!token) {
    token = crypto.randomUUID();
    localStorage.setItem("shortly_owner_token", token);
  }
  return token;
}

function authHeaders(): Record<string, string> {
  return { "X-Owner-Token": getOwnerToken() };
}

// ── Types ──────────────────────────────────────────────────────────────────

export interface CreateLinkPayload {
  long_url: string;
  custom_code?: string;
  expires_in_minutes?: number;
}

export interface LinkResponse {
  short_code: string;
  short_url: string;
  long_url: string;
  qr_code_base64: string;
  created_at: string;
  expires_at: string | null;
  is_custom: boolean;
  verified: "pending" | "verified" | "unreachable";
  owner_token: string;
}

export interface LinkRecord {
  short_code: string;
  long_url: string;
  created_at: string;
  expires_at: string | null;
  is_custom: boolean;
  click_count: number;
  verified: "pending" | "verified" | "unreachable";
  owner_token: string;
}

export interface AnalyticsResponse {
  short_code: string;
  total_clicks: number;
  clicks_by_date: { date: string; count: number }[];
  top_referrers: { referrer: string; count: number }[];
}

// ── API calls ──────────────────────────────────────────────────────────────

export async function createLink(payload: CreateLinkPayload): Promise<LinkResponse> {
  const res = await fetch(`${API_BASE}/api/links`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
    },
    body: JSON.stringify(payload),
  });

  if (res.status === 409) {
    throw new Error("That custom code is already taken.");
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? "Failed to create link.");
  }
  return res.json();
}

export async function getMyLinks(): Promise<LinkRecord[]> {
  const res = await fetch(`${API_BASE}/api/links/mine`, {
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error("Failed to load your links.");
  return res.json();
}

export async function getAnalytics(shortCode: string): Promise<AnalyticsResponse> {
  const res = await fetch(`${API_BASE}/api/analytics/${shortCode}`, {
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error("Failed to load analytics.");
  return res.json();
}
