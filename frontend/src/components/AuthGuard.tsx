"use client";
import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import Spinner from "@/components/ui/Spinner";

// Pages built on open, aggregated public data (World Bank, SDG, survey
// catalogues) are public and crawlable — this is what lets Google index the
// platform. Anything involving user uploads, private microdata, or account
// state stays behind login.
const PUBLIC_PATHS = [
  "/",
  "/about",
  "/login",
  "/register",
  "/dashboard",
  "/sdg",
  "/docs",
  "/search",
  "/surveys",
  "/microdata/indicators",
  "/harveststat",
  "/health",
];
const PUBLIC_PREFIXES = ["/research"];

function isPublicPath(pathname: string): boolean {
  if (PUBLIC_PATHS.includes(pathname)) return true;
  return PUBLIC_PREFIXES.some((p) => pathname === p || pathname.startsWith(p + "/"));
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
