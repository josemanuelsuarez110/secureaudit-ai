"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { scansApi, getApiError, type ScanJobDetail } from "@/lib/api";
import { ArrowLeft, CheckCircle, XCircle, AlertTriangle, Info, Loader2, Clock } from "lucide-react";

const severityConfig = {
  critical: { color: "text-red-700", bg: "bg-red-50", border: "border-red-200", icon: XCircle },
  high: { color: "text-orange-700", bg: "bg-orange-50", border: "border-orange-200", icon: AlertTriangle },
  medium: { color: "text-yellow-700", bg: "bg-yellow-50", border: "border-yellow-200", icon: AlertTriangle },
  low: { color: "text-blue-700", bg: "bg-blue-50", border: "border-blue-200", icon: Info },
  info: { color: "text-gray-700", bg: "bg-gray-50", border: "border-gray-200", icon: Info },
};

export default function ScanDetailPage() {
  const params = useParams();
  const router = useRouter();
  const scanId = params.id as string;

  const [scan, setScan] = useState<ScanJobDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadScan() {
    try {
      const data = await scansApi.get(scanId);
      setScan(data);
    } catch (err) {
      setError(getApiError(err));
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadScan();
  }, [scanId]);

  // Polling si el scan está pendiente o en curso
  useEffect(() => {
    if (!scan) return;
    if (scan.status !== "pending" && scan.status !== "running") return;

    const interval = setInterval(loadScan, 3000);
    return () => clearInterval(interval);
  }, [scan?.status]);

  if (isLoading) {
    return <p className="text-gray-500">Cargando...</p>;
  }

  if (error) {
    return (
      <div className="p-3 bg-red-50 border border-red-200 rounded text-red-700">
        {error}
      </div>
    );
  }

  if (!scan) {
    return <p className="text-gray-500">No encontrado</p>;
  }

  const findingsByCategory = scan.results.reduce((acc, result) => {
    if (!acc[result.category]) acc[result.category] = [];
    acc[result.category].push(result);
    return acc;
  }, {} as Record<string, typeof scan.results>);

  const stats = {
    total: scan.results.length,
    critical: scan.results.filter((r) => r.severity === "critical").length,
    high: scan.results.filter((r) => r.severity === "high").length,
    medium: scan.results.filter((r) => r.severity === "medium").length,
    low: scan.results.filter((r) => r.severity === "low").length,
    pass: scan.results.filter((r) => r.status === "pass").length,
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link
          href="/scans"
          className="p-2 hover:bg-gray-100 rounded-md transition-colors"
        >
          <ArrowLeft className="w-5 h-5 text-gray-600" />
        </Link>
        <div className="flex-1">
          <h1 className="text-3xl font-bold text-gray-900">
            Auditoría {scan.scan_type}
          </h1>
          <p className="text-gray-600 mt-1">
            {new Date(scan.created_at).toLocaleString("es-ES")}
          </p>
        </div>
        <div>
          {scan.status === "pending" && (
            <span className="inline-flex items-center gap-2 px-3 py-1 bg-yellow-100 text-yellow-700 rounded-full text-sm">
              <Clock className="w-4 h-4" /> Pendiente
            </span>
          )}
          {scan.status === "running" && (
            <span className="inline-flex items-center gap-2 px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm">
              <Loader2 className="w-4 h-4 animate-spin" /> Ejecutando
            </span>
          )}
          {scan.status === "completed" && (
            <span className="inline-flex items-center gap-2 px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm">
              <CheckCircle className="w-4 h-4" /> Completada
            </span>
          )}
          {scan.status === "failed" && (
            <span className="inline-flex items-center gap-2 px-3 py-1 bg-red-100 text-red-700 rounded-full text-sm">
              <XCircle className="w-4 h-4" /> Fallida
            </span>
          )}
        </div>
      </div>

      {/* Error del scan */}
      {scan.error_message && (
        <div className="p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
          <strong>Error:</strong> {scan.error_message}
        </div>
      )}

      {/* Stats */}
      {scan.results.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <p className="text-xs text-gray-500 uppercase">Total</p>
            <p className="text-2xl font-bold text-gray-900">{stats.total}</p>
          </div>
          <div className="bg-red-50 rounded-lg border border-red-200 p-4">
            <p className="text-xs text-red-600 uppercase">Críticos</p>
            <p className="text-2xl font-bold text-red-700">{stats.critical}</p>
          </div>
          <div className="bg-orange-50 rounded-lg border border-orange-200 p-4">
            <p className="text-xs text-orange-600 uppercase">Altos</p>
            <p className="text-2xl font-bold text-orange-700">{stats.high}</p>
          </div>
          <div className="bg-yellow-50 rounded-lg border border-yellow-200 p-4">
            <p className="text-xs text-yellow-600 uppercase">Medios</p>
            <p className="text-2xl font-bold text-yellow-700">{stats.medium}</p>
          </div>
          <div className="bg-blue-50 rounded-lg border border-blue-200 p-4">
            <p className="text-xs text-blue-600 uppercase">Bajos</p>
            <p className="text-2xl font-bold text-blue-700">{stats.low}</p>
          </div>
          <div className="bg-green-50 rounded-lg border border-green-200 p-4">
            <p className="text-xs text-green-600 uppercase">OK</p>
            <p className="text-2xl font-bold text-green-700">{stats.pass}</p>
          </div>
        </div>
      )}

      {/* Resultados por categoría */}
      {scan.results.length === 0 ? (
        <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
          <Loader2 className="w-12 h-12 text-gray-300 mx-auto mb-3 animate-spin" />
          <p className="text-gray-500">
            {scan.status === "completed"
              ? "Sin resultados"
              : "Procesando auditoría..."}
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {Object.entries(findingsByCategory).map(([category, findings]) => (
            <div key={category}>
              <h2 className="text-xl font-bold text-gray-900 mb-3 capitalize">
                {category}
              </h2>
              <div className="space-y-2">
                {findings.map((finding) => {
                  const config = severityConfig[finding.severity] || severityConfig.info;
                  const Icon = config.icon;
                  return (
                    <div
                      key={finding.id}
                      className={`rounded-lg border p-4 ${config.bg} ${config.border}`}
                    >
                      <div className="flex items-start gap-3">
                        <Icon className={`w-5 h-5 ${config.color} mt-0.5 shrink-0`} />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between gap-3">
                            <div>
                              <p className={`font-medium ${config.color}`}>
                                {finding.title}
                              </p>
                              <p className="text-xs text-gray-500 mt-0.5">
                                {finding.check_name}
                              </p>
                            </div>
                            <span className={`px-2 py-1 rounded text-xs font-medium ${config.color} ${config.bg} border ${config.border}`}>
                              {finding.severity}
                            </span>
                          </div>

                          {finding.description && (
                            <p className="text-sm text-gray-700 mt-2">
                              {finding.description}
                            </p>
                          )}

                          {finding.recommendation && (
                            <div className="mt-3 pt-3 border-t border-current/10">
                              <p className="text-xs font-medium text-gray-700 mb-1">
                                Recomendación:
                              </p>
                              <p className="text-sm text-gray-700">
                                {finding.recommendation}
                              </p>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
