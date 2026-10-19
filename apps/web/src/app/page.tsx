"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/auth-store";

export default function HomePage() {
  const router = useRouter();
  const { token } = useAuthStore();

  useEffect(() => {
    // Si hay token, ir al dashboard. Si no, ir al login.
    if (token) {
      router.push("/dashboard");
    } else {
      router.push("/login");
    }
  }, [token, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <p className="text-gray-500">Redirigiendo...</p>
    </div>
  );
}
