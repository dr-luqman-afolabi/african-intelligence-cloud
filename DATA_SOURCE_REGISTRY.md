# AIC Data Source Registry

African Intelligence Cloud — Data Source Governance & Connector Roadmap

---

## Classification System

| Tier | Label | Description | AIC Handling |
|------|-------|-------------|--------------|
| **A** | Open API | Live endpoint, open access, no signup required | AIC calls directly; auto-refresh on schedule |
| **B** | Open downloadable | Public file (CSV/XLSX/PDF); one-off or bulk download | AIC ingests and caches; re-downloads on schedule |
| **C** | Restricted microdata | Requires DUA, user approval, or licensed access | User uploads own approved copy; AIC never fetches directly |
| **D** | Client-owned | Private data owned by the client; never redistributed | AIC processes in-memory only; no external transfer |

---

## Source Registry

### 1. World Bank Open Data

| Field | Value |
|-------|-------|
| **source_id** | `world_bank` |
| **source_name** | World Bank Open Data |
| **source_type** | Macroeconomic indicators, development statistics |
| **access_method** | REST API (no key required) — `api.worldbank.org/v2/` |
| **license_category** | A — Open API |
| **update_frequency** | Annual (most series); quarterly for some financial indicators |
| **requires_approval** | No |
| **redistribution_allowed** | Yes — CC BY 4.0 |
| **citation_required** | Yes — "Source: World Bank, [indicator name], [year]" |
| **data_owner** | World Bank Group |
| **connector_status** | live |

**License risk:** None. Freely usable and redistributable with attribution.

**AIC handling:** Direct API calls via `worldbank_connector.py`. Scheduled sync of indicator/country pairs. Results stored in `macro_data` table with `data_source = "world_bank"`.

---

### 2. IMF Data (API endpoints)

| Field | Value |
|-------|-------|
| **source_id** | `imf_api` |
| **source_name** | IMF Data — JSON REST API |
| **source_type** | Macroeconomic indicators (WEO, IFS, DOTS, BOP) |
| **access_method** | REST API — `dataservices.imf.org/IMF.Rest/DataService/` |
| **license_category** | A — Open API |
| **update_frequency** | Semi-annual (WEO); quarterly (IFS, BOP) |
| **requires_approval** | No |
| **redistribution_allowed** | Yes — IMF open data policy |
| **citation_required** | Yes — "Source: International Monetary Fund" |
| **data_owner** | International Monetary Fund |
| **connector_status** | planned |

**License risk:** Low. IMF requests attribution but permits redistribution.

**AIC handling:** API connector to fetch WEO/IFS series by country and date range. IMF JSON API has irregular schema — connector must normalise response before storage.

---

### 3. UN SDG Indicators API

| Field | Value |
|-------|-------|
| **source_id** | `un_sdg` |
| **source_name** | UN SDG Indicators Global Database |
| **source_type** | Sustainable Development Goal progress indicators |
| **access_method** | REST API — `unstats.un.org/SDGAPI/v1/` |
| **license_category** | A — Open API |
| **update_frequency** | Annual |
| **requires_approval** | No |
| **redistribution_allowed** | Yes — CC BY-IGO 3.0 |
| **citation_required** | Yes — "Source: United Nations Statistics Division, SDG Indicators Database" |
| **data_owner** | United Nations Statistics Division |
| **connector_status** | planned |

**License risk:** None. UN IGO license permits educational and research use.

**AIC handling:** Fetch by goal, target, or series code; filter to African country ISO codes.

---

### 4. Climate / Rainfall Data (CHIRPS / ERA5)

| Field | Value |
|-------|-------|
| **source_id** | `climate_chirps` |
| **source_name** | CHIRPS Rainfall Estimates / ERA5 Reanalysis |
| **source_type** | Precipitation, temperature, climate anomaly rasters |
| **access_method** | REST API (CHIRPS via CHC data server) / Copernicus CDS API (ERA5) |
| **license_category** | A — Open API |
| **update_frequency** | Daily (CHIRPS near-real-time); monthly aggregates for analysis |
| **requires_approval** | No (CHIRPS); free account required (ERA5) |
| **redistribution_allowed** | Yes (CHIRPS); yes with attribution (ERA5) |
| **citation_required** | Yes — "Funk et al. (2015) / Copernicus Climate Change Service" |
| **data_owner** | UCSB Climate Hazards Center (CHIRPS); ECMWF (ERA5) |
| **connector_status** | planned |

**License risk:** Low. CHIRPS is fully open; ERA5 requires a free CDS account but no license fee.

**AIC handling:** Admin configures CDS API key for ERA5. CHIRPS fetched without credentials. Output: country-level or grid-level monthly averages stored as time-series.

---

### 5. Satellite Night-Time Lights (VIIRS / DMSP)

| Field | Value |
|-------|-------|
| **source_id** | `nighttime_lights` |
| **source_name** | VIIRS Day/Night Band (NASA Black Marble) |
| **source_type** | Radiance rasters proxying economic activity |
| **access_method** | NASA Earthdata REST API (`ladsweb.modaps.eosdis.nasa.gov`) |
| **license_category** | A — Open API |
| **update_frequency** | Monthly composites |
| **requires_approval** | No (free NASA Earthdata account required) |
| **redistribution_allowed** | Yes — NASA open data |
| **citation_required** | Yes — "Roman et al. (2018), NASA Black Marble" |
| **data_owner** | NASA / NOAA |
| **connector_status** | planned |

**License risk:** Low. NASA open data; attribution required.

**AIC handling:** Admin registers NASA Earthdata credentials. Connector downloads monthly GeoTIFF tiles, aggregates to admin-level polygons, stores radiance statistics in BigQuery.

---

### 6. Commodity Prices (IMF Primary Commodity Price API)

| Field | Value |
|-------|-------|
| **source_id** | `commodity_prices_imf` |
| **source_name** | IMF Primary Commodity Prices |
| **source_type** | Global commodity prices (oil, metals, food, agriculture) |
| **access_method** | REST API — `dataservices.imf.org/IMF.Rest/DataService/` (PCPS database) |
| **license_category** | A — Open API |
| **update_frequency** | Monthly |
| **requires_approval** | No |
| **redistribution_allowed** | Yes — IMF open data policy |
| **citation_required** | Yes — "Source: IMF Primary Commodity Prices" |
| **data_owner** | International Monetary Fund |
| **connector_status** | planned |

**License risk:** Low. Part of IMF open data; same policy as source #2.

**AIC handling:** Shared IMF connector fetches from PCPS database. Commodity time-series linked to African exports for terms-of-trade analysis.

---

### 7. African Development Bank Data Portal

| Field | Value |
|-------|-------|
| **source_id** | `afdb` |
| **source_name** | African Development Bank Data Portal |
| **source_type** | African socioeconomic statistics, infrastructure, finance |
| **access_method** | Bulk CSV/XLSX download from `dataportal.afdb.org` |
| **license_category** | B — Open downloadable |
| **update_frequency** | Annual |
| **requires_approval** | No |
| **redistribution_allowed** | Yes — AfDB open data policy |
| **citation_required** | Yes — "Source: African Development Bank, [dataset title]" |
| **data_owner** | African Development Bank Group |
| **connector_status** | planned |

**License risk:** Low. Open data with attribution.

**AIC handling:** Scheduled download of bulk CSV packages. Parser normalises multi-year wide format to long format before ingestion.

---

### 8. Rwanda NISR (National Institute of Statistics)

| Field | Value |
|-------|-------|
| **source_id** | `rwanda_nisr` |
| **source_name** | Rwanda National Institute of Statistics |
| **source_type** | National accounts, labour, trade, poverty, demographic statistics |
| **access_method** | File download from `statistics.gov.rw` |
| **license_category** | B — Open downloadable |
| **update_frequency** | Annual (main reports); quarterly (GDP flash) |
| **requires_approval** | No |
| **redistribution_allowed** | Conditional — cite source; check per-report terms |
| **citation_required** | Yes — "Source: Rwanda National Institute of Statistics, [report title]" |
| **data_owner** | Government of Rwanda / NISR |
| **connector_status** | planned |

**License risk:** Low-medium. Rwanda publishes most statistics as open PDF/Excel but some datasets note "not for redistribution" — verify per report.

**AIC handling:** Manual download ingestion or scheduled scrape of structured Excel reports. Admin flags redistribution status per dataset at upload time.

---

### 9. Nigeria NBS (National Bureau of Statistics)

| Field | Value |
|-------|-------|
| **source_id** | `nigeria_nbs` |
| **source_name** | Nigeria National Bureau of Statistics |
| **source_type** | CPI, GDP, trade, labour, poverty statistics |
| **access_method** | File download from `nigerianstat.gov.ng` |
| **license_category** | B — Open downloadable |
| **update_frequency** | Quarterly (CPI, GDP); annual (household surveys) |
| **requires_approval** | No |
| **redistribution_allowed** | Yes — NBS open data policy |
| **citation_required** | Yes — "Source: Nigeria National Bureau of Statistics" |
| **data_owner** | Government of Nigeria / NBS |
| **connector_status** | planned |

**License risk:** Low. Nigeria NBS states data is freely available.

**AIC handling:** Scheduled download of quarterly releases. PDF reports require extraction; Excel/CSV releases preferred.

---

### 10. Afrobarometer (Public Rounds)

| Field | Value |
|-------|-------|
| **source_id** | `afrobarometer_public` |
| **source_name** | Afrobarometer Public Summary Data |
| **source_type** | Public opinion, governance, democracy, economic sentiment |
| **access_method** | Aggregate summary statistics downloadable from `afrobarometer.org` |
| **license_category** | B — Open downloadable |
| **update_frequency** | Per survey round (~2–3 years) |
| **requires_approval** | No (summaries only) |
| **redistribution_allowed** | Yes for aggregates — see Afrobarometer data policy |
| **citation_required** | Yes — "Source: Afrobarometer, Round [N], [year]" |
| **data_owner** | Afrobarometer Network |
| **connector_status** | planned |

**License risk:** Low for summary/aggregate data. Microdata is Category C (see source #16).

**AIC handling:** Download aggregate country-level Excel files. Store sentiment and governance indicators per country-round.

---

### 11. Public Procurement Portals (OCDS-compliant)

| Field | Value |
|-------|-------|
| **source_id** | `procurement_ocds` |
| **source_name** | African Public Procurement Portals (OCDS) |
| **source_type** | Tender notices, awards, contract values |
| **access_method** | REST API or bulk JSON (Open Contracting Data Standard format) |
| **license_category** | B — Open downloadable |
| **update_frequency** | Real-time to weekly depending on country portal |
| **requires_approval** | No |
| **redistribution_allowed** | Yes — OCDS open standard |
| **citation_required** | Yes — cite the specific country portal |
| **data_owner** | Individual government procurement agencies |
| **connector_status** | planned |

**License risk:** Low. OCDS mandates open publication; individual portals may vary.

**AIC handling:** Country-specific connectors (Kenya AGPO, Ghana PRAG, Nigeria BPP). Normalise to OCDS schema. Flag country as data_owner attribute.

---

### 12. ILO Labour Force Surveys (Aggregates)

| Field | Value |
|-------|-------|
| **source_id** | `ilo_ilostat` |
| **source_name** | ILO ILOSTAT Database |
| **source_type** | Employment, unemployment, labour force participation by country |
| **access_method** | REST API or bulk CSV — `ilostat.ilo.org/resources/SDMX-JSON-service/` |
| **license_category** | B — Open downloadable |
| **update_frequency** | Annual; some quarterly |
| **requires_approval** | No |
| **redistribution_allowed** | Yes — ILO open data |
| **citation_required** | Yes — "Source: ILO, ILOSTAT database" |
| **data_owner** | International Labour Organization |
| **connector_status** | planned |

**License risk:** None. ILO CC BY 4.0.

**AIC handling:** SDMX or JSON API connector. Filter to African countries. Labour indicators stored alongside macro_data.

---

### 13. World Bank Enterprise Surveys

| Field | Value |
|-------|-------|
| **source_id** | `enterprise_surveys` |
| **source_name** | World Bank Enterprise Surveys |
| **source_type** | Firm-level business environment indicators (aggregated country profiles) |
| **access_method** | Bulk CSV/API download from `enterprisesurveys.worldbank.org` |
| **license_category** | B — Open downloadable |
| **update_frequency** | Per survey cycle (~3–5 years per country) |
| **requires_approval** | No (country aggregates); registration required for microdata |
| **redistribution_allowed** | Yes for aggregates — World Bank open data |
| **citation_required** | Yes — "Source: World Bank Enterprise Surveys, [year]" |
| **data_owner** | World Bank Group |
| **connector_status** | planned |

**License risk:** Low for aggregate indicators. Microdata requires DUA — treat as Category C.

**AIC handling:** Download country-level aggregate indicator CSV. Microdata is never fetched directly by AIC.

---

### 14. Commodity Prices — Bulk Historical (World Bank Pink Sheet)

| Field | Value |
|-------|-------|
| **source_id** | `commodity_prices_wb` |
| **source_name** | World Bank Commodity Price Data (Pink Sheet) |
| **source_type** | Monthly historical commodity prices (energy, metals, food, agriculture) |
| **access_method** | Excel file download from World Bank data site |
| **license_category** | B — Open downloadable |
| **update_frequency** | Monthly |
| **requires_approval** | No |
| **redistribution_allowed** | Yes — CC BY 4.0 |
| **citation_required** | Yes — "Source: World Bank, Commodity Markets Outlook" |
| **data_owner** | World Bank Group |
| **connector_status** | planned |

**License risk:** None. Same World Bank CC BY 4.0 license as source #1.

**AIC handling:** Monthly download of Pink Sheet Excel. Parser reads "Monthly Prices" tab. Stored as commodity price time-series distinct from IMF PCPS.

---

### 15. DHS Program (Demographic and Health Surveys)

| Field | Value |
|-------|-------|
| **source_id** | `dhs_program` |
| **source_name** | DHS Program Microdata |
| **source_type** | Household health, nutrition, fertility, mortality survey microdata |
| **access_method** | User registers at `dhsprogram.com`; downloads approved datasets |
| **license_category** | C — Restricted microdata |
| **update_frequency** | Per survey round (~5 years per country) |
| **requires_approval** | Yes — DHS registration and data use agreement per country |
| **redistribution_allowed** | No — DHS prohibits redistribution of microdata |
| **citation_required** | Yes — per DHS citation guidelines |
| **data_owner** | ICF International / USAID-funded DHS Program |
| **connector_status** | user_upload |

**License risk:** High. DHS microdata is subject to strict DUA. AIC must never fetch, store, or transfer DHS data on behalf of users.

**AIC handling:** User uploads their own approved DHS dataset (CSV/DTA/SAS). AIC processes it in-session only. Platform displays a DUA reminder at upload time. Files never stored on shared infrastructure.

---

### 16. Uganda National Panel Survey (UNPS / LSMS)

| Field | Value |
|-------|-------|
| **source_id** | `unps_lsms` |
| **source_name** | Uganda National Panel Survey (World Bank LSMS) |
| **source_type** | Longitudinal household welfare, agriculture, consumption panel data |
| **access_method** | World Bank Microdata Catalog — user registers and applies |
| **license_category** | C — Restricted microdata |
| **update_frequency** | Per survey wave (biennial) |
| **requires_approval** | Yes — World Bank data access request |
| **redistribution_allowed** | No |
| **citation_required** | Yes — World Bank LSMS citation format |
| **data_owner** | Uganda Bureau of Statistics / World Bank |
| **connector_status** | user_upload |

**License risk:** High. Access conditioned on approved research proposal. No third-party redistribution.

**AIC handling:** Same as DHS — user uploads own approved files. AIC validates file structure and displays license reminder.

---

### 17. World Bank Microdata Catalog (LSMS, other surveys)

| Field | Value |
|-------|-------|
| **source_id** | `wb_microdata` |
| **source_name** | World Bank Microdata Library |
| **source_type** | Household surveys, living standards measurement studies |
| **access_method** | `microdata.worldbank.org` — survey-specific access; some open, most licensed |
| **license_category** | C — Restricted microdata |
| **update_frequency** | Per survey |
| **requires_approval** | Varies — public access for some; Licensed or Confidential for others |
| **redistribution_allowed** | No for licensed/confidential tiers |
| **citation_required** | Yes |
| **data_owner** | World Bank Group |
| **connector_status** | user_upload |

**License risk:** Medium-high. AIC cannot determine access tier without per-survey check. Default to C; user confirms their access level at upload.

**AIC handling:** User uploads approved dataset. At upload, user selects their DUA tier (public/licensed/confidential). Confidential data processed with stricter isolation flags.

---

### 18. IPUMS International / USA

| Field | Value |
|-------|-------|
| **source_id** | `ipums` |
| **source_name** | IPUMS International Census Microdata |
| **source_type** | Harmonised census and survey microdata for African countries |
| **access_method** | `ipums.org` — free registration; data use agreement per project |
| **license_category** | C — Restricted microdata |
| **update_frequency** | Per census round (decennial) |
| **requires_approval** | Yes — IPUMS registration and project-level DUA |
| **redistribution_allowed** | No — IPUMS explicitly prohibits redistribution |
| **citation_required** | Yes — IPUMS citation format with version number |
| **data_owner** | University of Minnesota / IPUMS |
| **connector_status** | user_upload |

**License risk:** High. IPUMS DUA explicitly prohibits using data to identify individuals and prohibits redistribution.

**AIC handling:** User uploads IPUMS extract (.csv or .dat + .xml codebook). AIC reads codebook to label variables. DUA reminder displayed at every upload session.

---

### 19. Afrobarometer (Licensed Microdata Rounds)

| Field | Value |
|-------|-------|
| **source_id** | `afrobarometer_licensed` |
| **source_name** | Afrobarometer Licensed Microdata |
| **source_type** | Individual-level survey responses on governance, economy, society |
| **access_method** | Apply at `afrobarometer.org/data/` — licensed access for researchers |
| **license_category** | C — Restricted microdata |
| **update_frequency** | Per survey round (~2–3 years) |
| **requires_approval** | Yes — Afrobarometer data access request |
| **redistribution_allowed** | No |
| **citation_required** | Yes — Afrobarometer citation format |
| **data_owner** | Afrobarometer Network |
| **connector_status** | user_upload |

**License risk:** High. Microdata not for redistribution; distinguish from public summary data (source #10).

**AIC handling:** User uploads approved licensed file. AIC tags the dataset as `afrobarometer_licensed` to distinguish from public aggregates (source #10). License reminder at upload.

---

### 20. KoboToolbox / ODK Client Data

| Field | Value |
|-------|-------|
| **source_id** | `kobotoolbox_client` |
| **source_name** | Client KoboToolbox / ODK Survey Data |
| **source_type** | Custom field surveys, M&E data, program monitoring data |
| **access_method** | Client exports from own KoboToolbox/ODK account; uploads to AIC |
| **license_category** | D — Client-owned |
| **update_frequency** | On demand / project-driven |
| **requires_approval** | N/A — client owns data |
| **redistribution_allowed** | No — client IP; never share outside their organisation |
| **citation_required** | N/A |
| **data_owner** | AIC client organisation |
| **connector_status** | live |

**License risk:** None externally, but maximum confidentiality obligation. Data never leaves client's organisation scope.

**AIC handling:** Handled via existing `UploadedDataset` model with `DatasetPrivacy.PRIVATE`. AIC processes in-memory, stores only in client-scoped GCS prefix. Not included in any cross-client aggregation.

---

## Summary Table

| # | source_id | Name | Tier | Connector Status |
|---|-----------|------|------|-----------------|
| 1 | `world_bank` | World Bank Open Data | A | live |
| 2 | `imf_api` | IMF Data API | A | planned |
| 3 | `un_sdg` | UN SDG Indicators | A | planned |
| 4 | `climate_chirps` | CHIRPS / ERA5 Climate | A | planned |
| 5 | `nighttime_lights` | VIIRS Night-Time Lights | A | planned |
| 6 | `commodity_prices_imf` | IMF Commodity Prices API | A | planned |
| 7 | `afdb` | AfDB Data Portal | B | planned |
| 8 | `rwanda_nisr` | Rwanda NISR | B | planned |
| 9 | `nigeria_nbs` | Nigeria NBS | B | planned |
| 10 | `afrobarometer_public` | Afrobarometer (public rounds) | B | planned |
| 11 | `procurement_ocds` | Procurement Portals (OCDS) | B | planned |
| 12 | `ilo_ilostat` | ILO ILOSTAT | B | planned |
| 13 | `enterprise_surveys` | WB Enterprise Surveys | B | planned |
| 14 | `commodity_prices_wb` | WB Pink Sheet | B | planned |
| 15 | `dhs_program` | DHS Program Microdata | C | user_upload |
| 16 | `unps_lsms` | UNPS / World Bank LSMS | C | user_upload |
| 17 | `wb_microdata` | World Bank Microdata Library | C | user_upload |
| 18 | `ipums` | IPUMS International | C | user_upload |
| 19 | `afrobarometer_licensed` | Afrobarometer (licensed) | C | user_upload |
| 20 | `kobotoolbox_client` | KoboToolbox / ODK Client Data | D | live |

---

## Connector Status Definitions

| Status | Meaning |
|--------|---------|
| `live` | Connector implemented and in production |
| `planned` | On the roadmap; architecture defined but not yet built |
| `user_upload` | No automated connector; user uploads approved data manually |
| `deprecated` | Previously live; now decommissioned |

---

## Implementation Roadmap

**Sprint 2.5 — Complete**
- `world_bank` (live)
- `kobotoolbox_client` via UploadedDataset (live)

**Sprint 3 — Open API connectors (Category A)**
- `imf_api`, `un_sdg`, `commodity_prices_imf` — shared IMF client
- `climate_chirps` — CHIRPS HTTP connector
- `nighttime_lights` — NASA Earthdata

**Sprint 4 — Open downloadable connectors (Category B)**
- `afdb`, `ilo_ilostat`, `commodity_prices_wb` — scheduled download + parse
- `rwanda_nisr`, `nigeria_nbs` — country-specific parsers
- `afrobarometer_public`, `enterprise_surveys`, `procurement_ocds`

**Sprint 5 — User upload flows for restricted data (Category C)**
- Upload UI with DUA confirmation dialog
- Per-source validation (DHS column schema, IPUMS codebook reader)
- Isolation flags for confidential tiers
- `dhs_program`, `unps_lsms`, `wb_microdata`, `ipums`, `afrobarometer_licensed`
