import type { Metadata } from "next";
import Dashboard from "@/components/Dashboard";

export const metadata: Metadata = {
  title: "Dashboard — Short.ly",
  description: "View and manage all your shortened links with click analytics.",
};

export default function DashboardPage() {
  return (
    <div className="container" style={{ paddingTop: 40, paddingBottom: 60 }}>
      <div style={{ marginBottom: 32 }}>
        <h1 style={{ marginBottom: 8 }}>Your links</h1>
        <p className="muted">
          Links created from this browser. Click a row to view analytics.
        </p>
      </div>
      <Dashboard />
    </div>
  );
}
