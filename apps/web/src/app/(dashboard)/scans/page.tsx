"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { organizationsApi, scansApi, assetsApi, getApiError, type ScanJob, type Asset } from "@/lib/api";
import { ScanLine, Plus, X, ArrowRight, Clock, CheckCircle, XCircle, Loader2 } from "lucide-react";

export default function ScansPage() {
  const [scans, setScans] = useState<ScanJob[]>([]);
  const [assets, setAssets] = useState<Asset[]>([]);
  const [organizationId, setOrganizationId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [selectedAsset, setSelectedAsset] = useState("");
  const [scanType, setScanType] = useState("full");
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

  async function loadData() {
    try {
      const orgs = await organizationsApi.list();
      if (orgs.length > 0) {
        setOrganizationId(orgs[0].id);
        const [scansData, assetsData] = await Promise.all([
          scansApi.list(orgs[0].id),
          assetsApi.list(orgs[0].id),
        ]);
        setScans(scansData);
        setAssets(assetsData);
      }
    } catch (err) {
      setError(getApiError(err));
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadData();
    // Refrescar cada 5s si hay scans en curso
    const interval = setInterval(() => {
      if (scans.some((s) => s.status === "pending" || s.status === "running")) {
        loadData();
      }
    }, 5000);
    return () => clearInterval(interval);
  }, [scans.length]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!organizationId || !selectedAsset) return;

    setCreating(true);
    setError(null);

    try {
      await scansApi.create(organizationId, {
        asset_id: selectedAsset,
        scan_type: scanType,
      });
      setShowModal(false);
      setSelectedAsset("");
      await loadData();
    } catch (err) {
      setError(getApiError(err));
    } finally {
      setCreating(false);
    }
  }

  if (isLoading) {
    return <p className="text-gray-500">Cargando...</p>;
  }

  const verifiedAssets = assets.filter((a) => a.status === "active");

  function statusIcon(status: string) {
    switch (status) {
      case "completed":
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case "running":
        return <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />;
      case "pending":
        return <Clock className="w-5 h-5 text-yellow-600" />;
      case "failed":
        return <XCircle className="w-5 h-5 text-red-600" />;
      default:
        return <Clock className="w-5 h-5 text-gray-400" />;
    }
  }

  function statusBadge(status: string) {
    const classes = {
      completed: "bg-green-100 text-green-700",
      running: "bg-blue-100 text-blue-700",
      pending: "bg-yellow-100 text-yellow-700",
      failed: "bg-red-100 text-red-700",
      cancelled: "bg-gray-100 text-gray-700",
    }[status] || "bg-gray-100 text-gray-700";

    return (
      <span className={`px-3 py-1 rounded-full text-xs font-medium ${classes}`}>
        {status}
      </span>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Auditorías</h1>
          <p className="text-gray-600 mt-1">
            Historial de auditorías de tus assets
          </p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          disabled={verifiedAssets.length === 0}
          className="inline-flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Plus className="w-4 h-4" />
          Nueva auditoría
        </button>
      </div>

      {verifiedAssets.length === 0 && (
        <div className="p-3 bg-yellow-50 border border-yellow-200 rounded text-yellow-800 text-sm">
          Necesitas al menos un asset verificado para lanzar auditorías.{" "}
          <Link href="/assets" className="underline font-medium">
            Añadir asset
          </Link>
        </div>
      )}

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)}>
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Scans list */}
      {scans.length === 0 ? (
        <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
          <ScanLine className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">No hay auditorías todavía</p>
        </div>
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 divide-y divide-gray-200">
          {scans.map((scan) => (
            <Link
              key={scan.id}
              href={`/scans/${scan.id}`}
              className="flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center gap-4">
                {statusIcon(scan.status)}
                <div>
                  <p className="font-medium text-gray-900">
                    Auditoría {scan.scan_type}
                  </p>
                  <p className="text-sm text-gray-500">
                    {new Date(scan.created_at).toLocaleString("es-ES")}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                {statusBadge(scan.status)}
                <ArrowRight className="w-5 h-5 text-gray-400" />
              </div>
            </Link>
          ))}
        </div>
      )}

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-gray-900">
                Nueva auditoría
              </h2>
              <button onClick={() => setShowModal(false)}>
                <X className="w-5 h-5 text-gray-400" />
              </button>
            </div>

            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Asset *
                </label>
                <select
                  value={selectedAsset}
                  onChange={(e) => setSelectedAsset(e.target.value)}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Selecciona un asset</option>
                  {verifiedAssets.map((asset) => (
                    <option key={asset.id} value={asset.id}>
                      {asset.display_name || asset.domain}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tipo de auditoría
                </label>
                <select
                  value={scanType}
                  onChange={(e) => setScanType(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="full">Completa (TLS + HTTP + DNS)</option>
                  <option value="tls">Solo TLS</option>
                  <option value="http">Solo HTTP</option>
                  <option value="dns">Solo DNS</option>
                </select>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
                >
                  {creating ? "Creando..." : "Lanzar"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
