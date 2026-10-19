"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuthStore } from "@/lib/auth-store";
import { organizationsApi, assetsApi, scansApi, type Organization, type Asset, type ScanJob } from "@/lib/api";
import { Building2, Globe, ScanLine, Plus, ArrowRight } from "lucide-react";

export default function DashboardPage() {
  const { user } = useAuthStore();
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [assets, setAssets] = useState<Asset[]>([]);
  const [scans, setScans] = useState<ScanJob[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const orgs = await organizationsApi.list();
        setOrganizations(orgs);

        if (orgs.length > 0) {
          const orgId = orgs[0].id;
          const [assetsData, scansData] = await Promise.all([
            assetsApi.list(orgId),
            scansApi.list(orgId),
          ]);
          setAssets(assetsData);
          setScans(scansData);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, []);

  if (isLoading) {
    return <p className="text-gray-500">Cargando...</p>;
  }

  const stats = [
    {
      label: "Organizaciones",
      value: organizations.length,
      icon: Building2,
      color: "blue",
      href: "/dashboard",
    },
    {
      label: "Assets",
      value: assets.length,
      icon: Globe,
      color: "green",
      href: "/assets",
    },
    {
      label: "Auditorías",
      value: scans.length,
      icon: ScanLine,
      color: "purple",
      href: "/scans",
    },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">
          Hola, {user?.full_name?.split(" ")[0] || "Usuario"}
        </h1>
        <p className="text-gray-600 mt-1">
          Resumen de tu actividad en SecureAudit AI
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {stats.map((stat) => {
          const Icon = stat.icon;
          const colorClasses = {
            blue: "bg-blue-50 text-blue-700",
            green: "bg-green-50 text-green-700",
            purple: "bg-purple-50 text-purple-700",
          }[stat.color];

          return (
            <Link
              key={stat.label}
              href={stat.href}
              className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
            >
              <div className="flex items-center justify-between mb-4">
                <div className={`w-12 h-12 rounded-lg ${colorClasses} flex items-center justify-center`}>
                  <Icon className="w-6 h-6" />
                </div>
                <ArrowRight className="w-5 h-5 text-gray-400" />
              </div>
              <p className="text-3xl font-bold text-gray-900">{stat.value}</p>
              <p className="text-sm text-gray-600 mt-1">{stat.label}</p>
            </Link>
          );
        })}
      </div>

      {/* Recent scans */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-xl font-bold text-gray-900">Auditorías recientes</h2>
          <Link
            href="/scans"
            className="text-sm text-blue-600 hover:underline flex items-center gap-1"
          >
            Ver todas <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        {scans.length === 0 ? (
          <div className="p-12 text-center">
            <ScanLine className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500 mb-4">No hay auditorías todavía</p>
            <Link
              href="/assets"
              className="inline-flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
            >
              <Plus className="w-4 h-4" />
              Añadir asset
            </Link>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {scans.slice(0, 5).map((scan) => (
              <Link
                key={scan.id}
                href={`/scans/${scan.id}`}
                className="block p-4 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-900">
                      Auditoría {scan.scan_type}
                    </p>
                    <p className="text-sm text-gray-500">
                      {new Date(scan.created_at).toLocaleString("es-ES")}
                    </p>
                  </div>
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-medium ${
                      scan.status === "completed"
                        ? "bg-green-100 text-green-700"
                        : scan.status === "running"
                        ? "bg-blue-100 text-blue-700"
                        : scan.status === "failed"
                        ? "bg-red-100 text-red-700"
                        : "bg-gray-100 text-gray-700"
                    }`}
                  >
                    {scan.status}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
