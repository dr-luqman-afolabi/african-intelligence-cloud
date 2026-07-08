import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "African Survey Catalogue — LSMS, DHS, MICS & More",
  description:
    "Browse household survey datasets for Africa: LSMS panels, DHS, MICS, EICV, Afrobarometer, and national statistical office surveys, with access conditions and documentation links.",
  alternates: { canonical: "/surveys" },
};

export default function SurveysLayout({ children }: { children: React.ReactNode }) {
  return children;
}
