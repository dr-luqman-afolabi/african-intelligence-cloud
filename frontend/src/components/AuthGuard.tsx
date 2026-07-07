"use client";
import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import Spinner from "@/components/ui/Spinner";

// Marketing and auth pages stay public; everything else requires a session.
const PUBLIC_PATHS = ["/", "/about", "/login", "/register"];

function isPublicPath(pathname: string): boolean {
  return PUBLIC_PATHS.includes(pathname);
}

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [authorized, setAuthorized] = useState(false);

  const publicRoute = isPublicPath(pathname ?? "/");

  useEffect(() => {
    if (publicRoute) {
      setAuthorized(true);
      return;
    }
    const token = localStorage.getItem("aic_token");
    if (!token) {
      setAuthorized(false);
      router.replace(`/login?next=${encodeURIComponent(pathname ?? "/dashboard")}`);
      return;
    }
    setAuthorized(true);
  }, [pathname, publicRoute, router]);

  if (!publicRoute && !authorized) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <Spinner />
      </div>
    );
  }

  return <>{children}</>;
}
