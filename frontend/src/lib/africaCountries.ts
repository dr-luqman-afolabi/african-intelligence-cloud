export interface AfricanCountry {
  iso3: string;
  name: string;
}

// All 54 AU member states, sorted alphabetically by name.
export const AFRICAN_COUNTRIES: AfricanCountry[] = [
  { iso3: "DZA", name: "Algeria" },
  { iso3: "AGO", name: "Angola" },
  { iso3: "BEN", name: "Benin" },
  { iso3: "BWA", name: "Botswana" },
  { iso3: "BFA", name: "Burkina Faso" },
  { iso3: "BDI", name: "Burundi" },
  { iso3: "CPV", name: "Cabo Verde" },
  { iso3: "CMR", name: "Cameroon" },
  { iso3: "CAF", name: "Central African Republic" },
  { iso3: "TCD", name: "Chad" },
  { iso3: "COM", name: "Comoros" },
  { iso3: "COG", name: "Congo, Rep." },
  { iso3: "COD", name: "Congo, Dem. Rep." },
  { iso3: "CIV", name: "Côte d'Ivoire" },
  { iso3: "DJI", name: "Djibouti" },
  { iso3: "EGY", name: "Egypt" },
  { iso3: "GNQ", name: "Equatorial Guinea" },
  { iso3: "ERI", name: "Eritrea" },
  { iso3: "SWZ", name: "Eswatini" },
  { iso3: "ETH", name: "Ethiopia" },
  { iso3: "GAB", name: "Gabon" },
  { iso3: "GMB", name: "Gambia" },
  { iso3: "GHA", name: "Ghana" },
  { iso3: "GIN", name: "Guinea" },
  { iso3: "GNB", name: "Guinea-Bissau" },
  { iso3: "KEN", name: "Kenya" },
  { iso3: "LSO", name: "Lesotho" },
  { iso3: "LBR", name: "Liberia" },
  { iso3: "LBY", name: "Libya" },
  { iso3: "MDG", name: "Madagascar" },
  { iso3: "MWI", name: "Malawi" },
  { iso3: "MLI", name: "Mali" },
  { iso3: "MRT", name: "Mauritania" },
  { iso3: "MUS", name: "Mauritius" },
  { iso3: "MAR", name: "Morocco" },
  { iso3: "MOZ", name: "Mozambique" },
  { iso3: "NAM", name: "Namibia" },
  { iso3: "NER", name: "Niger" },
  { iso3: "NGA", name: "Nigeria" },
  { iso3: "RWA", name: "Rwanda" },
  { iso3: "STP", name: "São Tomé and Príncipe" },
  { iso3: "SEN", name: "Senegal" },
  { iso3: "SYC", name: "Seychelles" },
  { iso3: "SLE", name: "Sierra Leone" },
  { iso3: "SOM", name: "Somalia" },
  { iso3: "ZAF", name: "South Africa" },
  { iso3: "SSD", name: "South Sudan" },
  { iso3: "SDN", name: "Sudan" },
  { iso3: "TZA", name: "Tanzania" },
  { iso3: "TGO", name: "Togo" },
  { iso3: "TUN", name: "Tunisia" },
  { iso3: "UGA", name: "Uganda" },
  { iso3: "ZMB", name: "Zambia" },
  { iso3: "ZWE", name: "Zimbabwe" },
];

export const ADMIN_LEVELS = [
  { value: "ADM0", label: "Country" },
  { value: "ADM1", label: "Province / Region / State" },
  { value: "ADM2", label: "District / County" },
  { value: "ADM3", label: "Sector / Subdistrict" },
] as const;

export const BOUNDARY_SOURCES = [
  { value: "gadm", label: "GADM" },
  { value: "hdx", label: "HDX" },
  { value: "ocha_cod_ab", label: "OCHA COD-AB" },
  { value: "natural_earth", label: "Natural Earth" },
  { value: "custom_upload", label: "Custom upload" },
] as const;

export const CHART_TYPES = [
  { value: "bar", label: "Bar" },
  { value: "line", label: "Line" },
  { value: "pie", label: "Pie" },
  { value: "map", label: "Map" },
] as const;
