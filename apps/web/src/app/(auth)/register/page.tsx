"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useAuthStore } from "@/lib/auth-store";

const registerSchema = z.object({
  email: z.string().email("Email inválido"),
  password: z.string().min(8, "Mínimo 8 caracteres"),
  full_name: z.string().min(2, "Mínimo 2 caracteres"),
  organization_name: z.string().min(2, "Mínimo 2 caracteres"),
  organization_slug: z
    .string()
    .min(3, "Mínimo 3 caracteres")
    .regex(/^[a-z0-9-]+$/, "Solo minúsculas, números y guiones"),
});

type RegisterForm = z.infer<typeof registerSchema>;

export default function RegisterPage() {
  const router = useRouter();
  const { register: registerUser, isLoading } = useAuthStore();
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = async (data: RegisterForm) => {
    try {
      setError(null);
      await registerUser(data);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Error al registrarse");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
      <div className="w-full max-w-md bg-white rounded-lg shadow-lg p-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Crear cuenta
        </h1>
        <p className="text-gray-600 mb-6">
          Empieza a auditar la seguridad de tus dominios
        </p>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Nombre completo
            </label>
            <input
              {...register("full_name")}
              type="text"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Juan Pérez"
            />
            {errors.full_name && (
              <p className="mt-1 text-sm text-red-600">{errors.full_name.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Email
            </label>
            <input
              {...register("email")}
              type="email"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="tu@email.com"
            />
            {errors.email && (
              <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Contraseña
            </label>
            <input
              {...register("password")}
              type="password"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Mínimo 8 caracteres"
            />
            {errors.password && (
              <p className="mt-1 text-sm text-red-600">{errors.password.message}</p>
            )}
          </div>

          <div className="border-t pt-4 mt-4">
            <p className="text-sm text-gray-600 mb-3">
              Crea tu organización (podrás invitar a más usuarios después)
            </p>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Nombre de la organización
              </label>
              <input
                {...register("organization_name")}
                type="text"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Mi Empresa S.A."
              />
              {errors.organization_name && (
                <p className="mt-1 text-sm text-red-600">
                  {errors.organization_name.message}
                </p>
              )}
            </div>
            <div className="mt-3">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Identificador (slug)
              </label>
              <input
                {...register("organization_slug")}
                type="text"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="mi-empresa"
              />
              {errors.organization_slug && (
                <p className="mt-1 text-sm text-red-600">
                  {errors.organization_slug.message}
                </p>
              )}
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
          >
            {isLoading ? "Creando cuenta..." : "Crear cuenta"}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-gray-600">
          ¿Ya tienes cuenta?{" "}
          <Link href="/login" className="text-blue-600 hover:underline font-medium">
            Inicia sesión
          </Link>
        </p>
      </div>
    </div>
  );
}
