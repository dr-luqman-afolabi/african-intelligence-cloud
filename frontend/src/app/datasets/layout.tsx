import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Datasets — Upload & Analyze African Survey and Microdata",
  description:
    "Upload, clean and analyze CSV, Excel, Stata and zipped survey datasets for Africa. Shared catalog of household microdata for poverty, agriculture and spatial analysis.",
  alternates: { canonical: "/datasets" },
  openGraph: { title: "Datasets — Upload & Analyze African Survey and Microdata", description: "Upload, clean and analyze CSV, Excel, Stata and zipped survey datasets for Africa. Shared catalog of household microdata for poverty, agriculture and spatial analysis.", url: "/datasets", type: "website" },
};

export default function DatasetsLayout({ children }: { children: React.ReactNode }) {
  return children;
}
