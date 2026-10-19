"use client";

import { useEffect, useState } from "react";
import { useAuthStore } from "@/lib/auth-store";
import { organizationsApi, assetsApi, getApiError, type Asset } from "@/lib/api";
import { Globe, Plus, Shield, ShieldCheck, ShieldOff, Trash2, X } from "lucide-react";

export default function AssetsPage() {
  const { user } = useAuthStore();
  const [assets, setAssets] = useState<Asset[]>([]);
  const [organizationId, setOrganizationId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [newDomain, setNewDomain] = useState("");
  const [newDisplayName, setNewDisplayName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

  async function loadAssets() {
    try {
      const orgs = await organizationsApi.list();
      if (orgs.length > 0) {
        setOrganizationId(orgs[0].id);
        const data = await assetsApi.list(orgs[0].id);
        setAssets(data);
      }
    } catch (err) {
      setError(getApiError(err));
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadAssets();
  }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!organizationId) return;

    setCreating(true);
    setError(null);

    try {
      await assetsApi.create(organizationId, {
        domain: newDomain,
        display_name: newDisplayName || undefined,
      });
      setShowModal(false);
      setNewDomain("");
      setNewDisplayName("");
      await loadAssets();
    } catch (err) {
      setError(getApiError(err));
    } finally {
      setCreating(false);
    }
  }

  async function handleVerify(assetId: string) {
    try {
      const result = await assetsApi.verify(assetId);
      if (result.verified) {
        await loadAssets();
      } else {
        setError(result.message);
      }
    } catch (err) {
      setError(getApiError(err));
    }
  }

  async function handleDelete(assetId: string) {
    if (!confirm("¿Eliminar este asset?")) return;
    try {
      await assetsApi.delete(assetId);
      await loadAssets();
    } catch (err) {
      setError(getApiError(err));
    }
  }

  if (isLoading) {
    return <p className="text-gray-500">Cargando...</p>;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Assets</h1>
          <p className="text-gray-600 mt-1">
            Dominios que puedes auditar
          </p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="inline-flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
        >
          <Plus className="w-4 h-4" />
          Añadir asset
        </button>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)}>
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Assets list */}
      {assets.length === 0 ? (
        <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
          <Globe className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500 mb-4">
            No tienes assets todavía. Añade tu primer dominio.
          </p>
          <button
            onClick={() => setShowModal(true)}
            className="inline-flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
          >
            <Plus className="w-4 h-4" />
            Añadir primer asset
          </button>
        </div>
      ) : (
        <div className="grid gap-4">
          {assets.map((asset) => (
            <div
              key={asset.id}
              className="bg-white rounded-lg border border-gray-200 p-4 flex items-center justify-between"
            >
              <div className="flex items-center gap-4">
                {asset.status === "active" ? (
                  <div className="w-10 h-10 rounded-lg bg-green-50 flex items-center justify-center">
                    <ShieldCheck className="w-5 h-5 text-green-600" />
                  </div>
                ) : (
                  <div className="w-10 h-10 rounded-lg bg-yellow-50 flex items-center justify-center">
                    <ShieldOff className="w-5 h-5 text-yellow-600" />
                  </div>
                )}
                <div>
                  <p className="font-medium text-gray-900">
                    {asset.display_name || asset.domain}
                  </p>
                  <p className="text-sm text-gray-500">{asset.domain}</p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <span
                  className={`px-3 py-1 rounded-full text-xs font-medium ${
                    asset.status === "active"
                      ? "bg-green-100 text-green-700"
                      : asset.status === "pending_verification"
                      ? "bg-yellow-100 text-yellow-700"
                      : "bg-gray-100 text-gray-700"
                  }`}
                >
                  {asset.status === "active"
                    ? "Verificado"
                    : asset.status === "pending_verification"
                    ? "Pendiente"
                    : asset.status}
                </span>

                {asset.status === "pending_verification" && (
                  <button
                    onClick={() => handleVerify(asset.id)}
                    className="text-sm text-blue-600 hover:underline"
                  >
                    Verificar
                  </button>
                )}

                <button
                  onClick={() => handleDelete(asset.id)}
                  className="text-gray-400 hover:text-red-600"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-gray-900">
                Añadir asset
              </h2>
              <button onClick={() => setShowModal(false)}>
                <X className="w-5 h-5 text-gray-400" />
              </button>
            </div>

            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Dominio *
                </label>
                <input
                  type="text"
                  value={newDomain}
                  onChange={(e) => setNewDomain(e.target.value)}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="ejemplo.com"
                />
                <p className="mt-1 text-xs text-gray-500">
                  Solo el dominio, sin https:// ni rutas
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nombre (opcional)
                </label>
                <input
                  type="text"
                  value={newDisplayName}
                  onChange={(e) => setNewDisplayName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Mi sitio principal"
                />
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
                  {creating ? "Creando..." : "Crear"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
