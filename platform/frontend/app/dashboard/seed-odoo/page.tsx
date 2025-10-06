"use client";

import React, { useState } from "react";

const apiBase = process.env.NEXT_PUBLIC_API_URL || "";

export default function SeedOdooPage() {
  const [crm, setCrm] = useState(5);
  const [invoices, setInvoices] = useState(3);
  const [ecom, setEcom] = useState(3);
  const [pos, setPos] = useState(0);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const seed = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      if (!apiBase) throw new Error("NEXT_PUBLIC_API_URL is not set");
      const res = await fetch(`${apiBase}/hybrid/demo/seed-odoo`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        // Assumes auth is handled via cookies/headers by your setup
        credentials: "include",
        body: JSON.stringify({ crm, invoices, ecom, pos }),
      });
      const body = await res.json();
      if (!res.ok) {
        throw new Error(body?.detail || "Seeding failed");
      }
      setResult(JSON.stringify(body, null, 2));
    } catch (error: unknown) {
      setError(error instanceof Error ? error.message : String(error));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-2xl">
      <h1 className="text-2xl font-semibold mb-4">Seed Odoo Demo Data</h1>
      <p className="text-sm text-gray-600 mb-4">
        Admin-only utility. Requires HYBRID or PLATFORM_ADMIN and appropriate env on the backend.
      </p>
      <div className="grid grid-cols-2 gap-4 mb-4">
        <label className="flex flex-col">
          <span>CRM opportunities</span>
          <input type="number" value={crm} onChange={(e) => setCrm(parseInt(e.target.value, 10) || 0)} className="border p-2" />
        </label>
        <label className="flex flex-col">
          <span>Invoices</span>
          <input type="number" value={invoices} onChange={(e) => setInvoices(parseInt(e.target.value, 10) || 0)} className="border p-2" />
        </label>
        <label className="flex flex-col">
          <span>E‑commerce orders</span>
          <input type="number" value={ecom} onChange={(e) => setEcom(parseInt(e.target.value, 10) || 0)} className="border p-2" />
        </label>
        <label className="flex flex-col">
          <span>POS orders</span>
          <input type="number" value={pos} onChange={(e) => setPos(parseInt(e.target.value, 10) || 0)} className="border p-2" />
        </label>
      </div>
      <button
        onClick={seed}
        disabled={loading}
        className="px-4 py-2 bg-blue-600 text-white rounded disabled:opacity-50"
      >
        {loading ? "Seeding..." : "Seed Now"}
      </button>
      {error && <pre className="mt-4 text-red-600 whitespace-pre-wrap">{error}</pre>}
      {result && <pre className="mt-4 bg-gray-50 p-3 rounded whitespace-pre-wrap">{result}</pre>}
    </div>
  );
}
