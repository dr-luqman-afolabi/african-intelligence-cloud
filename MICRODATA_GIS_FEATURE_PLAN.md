# Microdata & GIS Spatial Analysis - Feature Plan (Draft)

Status: DRAFT - scoping only, no code implemented yet. Written in response to a request to add DHS, UNPS, EICV and other microdata sources for micro-level analysis, plus GIS spatial analysis for poverty data.

## 1. Compliance constraint (must read first)

Per DATA_SOURCE_REGISTRY.md, DHS Program and UNPS/LSMS are both classified Category C (restricted microdata). The registry states AIC must never fetch, store, or transfer this data on behalf of users - only user-uploaded files backed by a confirmed Data Use Agreement (DUA) are permitted. EICV is not yet listed in the registry; it should be added as a new Category C entry following the same pattern, since NISR (Rwanda) licenses EICV under comparable restricted-use terms. Any implementation must preserve this restriction: no automated scraping or bulk download of DHS/UNPS/EICV data by AIC itself.

## 2. Phase 1 - Restricted microdata upload flow (extends existing Sprint 5 roadmap item)

- Generalize the planned Sprint 5 upload flow so it explicitly covers dhs_program, unps_lsms, and a new eicv_nisr source, plus any future Category C source, via one configurable upload pipeline rather than one-off pipelines per source.
- Required steps per upload: user confirms DUA/license terms, file is scanned, metadata (source, survey year, country, license reference) is recorded, raw file is stored in a restricted-access bucket (not public), and only derived/aggregated outputs are exposed through the app UI.
- Open question for the user: should uploaded microdata be processed entirely server-side into aggregate indicators before display, so raw respondent-level rows are never rendered in the frontend?

## 3. Phase 2 - GIS spatial poverty analysis

- Proposed stack (default assumption, pending confirmation): Leaflet.js for frontend mapping (open-source, no licensing cost, integrates cleanly with the existing Next.js frontend), PostGIS extension enabled on the existing Cloud SQL Postgres instance for spatial queries, and admin boundary shapefiles sourced from a public/open source such as GADM or the UN OCHA Humanitarian Data Exchange.
- Poverty indicators would be joined to admin boundaries (region/district level) rather than plotting individual survey respondents, to avoid any re-identification risk from restricted microdata.
- The registry's two closest existing entries (CHIRPS/ERA5 climate data and VIIRS night-time lights) are both listed as "planned" and are not poverty-specific; this GIS layer would be new infrastructure, not an extension of those two.

## 4. Open decisions needed before implementation begins

- Confirm mapping library choice (Leaflet vs Mapbox vs other) - Mapbox requires an API key and has usage-based pricing, which is a purchasing decision the user should make.
- Confirm source for administrative boundary shapefiles.
- Confirm whether Phase 1 (upload flow) or Phase 2 (GIS) should be prioritized first.
- Confirm data handling policy for uploaded microdata (aggregate-only display vs. other access controls).

## 5. Explicitly out of scope for this document

- No database schema changes, no new API endpoints, and no frontend code have been written as part of this plan. This is a scoping document only, pending the decisions above.

## 6. Status update (scaffold added)

A dormant code scaffold has been added on the feature/microdata-gis-scaffold
branch: backend/app/services/spatial_poverty_service.py and
backend/app/routers/spatial_analysis.py. Neither is wired into main.py, and
geopandas/shapely have NOT been added to requirements.txt yet, specifically
to avoid affecting the live production build.

Important operational note: this repository has an automatic CI/CD trigger
that runs a full Cloud Build deploy (both backend and frontend, plus a DB
migration job) on every push to main. Because of that, further scaffold or
documentation changes should go through a pull request rather than a direct
commit to main, so they do not trigger an unintended production deploy until
a maintainer chooses to merge.

Separately, during verification of the placeholder-URL fix, the recent
auto-deploy build (commit fc334e9) resolved the previous blanket 403 "not
authenticated" errors on aic-backend - requests now reach the application.
However, the macro-data endpoint now returns a 503 due to an unrelated SQL
error (a query referencing a column that does not match the current
macro_data table schema). This is a separate backend bug from the auth
issue and is not addressed by this feature plan.
