"""
World Bank API connector.
Fetches macroeconomic indicators and upserts them into the database.
"""
import logging
import time
import requests
from sqlalchemy.orm import Session

from app.config import get_settings
from app.connectors.base import BaseConnector, ConnectorError, ConnectorMetadata, HealthStatus

logger = logging.getLogger(__name__)

# Connector identity — must match registry.py entry
SOURCE_METADATA = {
    "source_id": "world_bank",
    "source_name": "World Bank Open Data",
    "source_type": "Macroeconomic indicators, development statistics",
    "access_method": "REST API — api.worldbank.org/v2/",
    "license_category": "A",
    "update_frequency": "annual",
    "requires_approval": False,
    "redistribution_allowed": True,
    "citation_required": True,
    "data_owner": "World Bank Group",
    "connector_status": "live",
}

from app.models.country import Country
from app.models.indicator import Indicator
from app.models.macro_data import MacroData

settings = get_settings()

# Core indicators to sync
INDICATORS = {
        "NY.GDP.PCAP.CD": {"name": "GDP per Capita (USD)", "unit": "USD", "category": "Growth"},
        "NY.GDP.MKTP.CD": {"name": "GDP (current US$)", "unit": "USD", "category": "Growth"},
        "NY.GDP.MKTP.KD.ZG": {"name": "GDP Growth Rate", "unit": "%", "category": "Growth"},
        "FP.CPI.TOTL.ZG": {"name": "Inflation Rate", "unit": "%", "category": "Prices"},
        "SI.POV.DDAY": {"name": "Poverty Rate (<$2.15/day)", "unit": "%", "category": "Poverty"},
        "SI.POV.GINI": {"name": "Gini Index", "unit": "index", "category": "Poverty"},
        "SL.UEM.TOTL.ZS": {"name": "Unemployment Rate", "unit": "%", "category": "Labour"},
        "SL.TLF.CACT.ZS": {"name": "Labor Force Participation Rate", "unit": "%", "category": "Labour"},
        "NE.TRD.GNFS.ZS": {"name": "Trade (% of GDP)", "unit": "% of GDP", "category": "Trade"},
        "NE.EXP.GNFS.ZS": {"name": "Exports (% of GDP)", "unit": "% of GDP", "category": "Trade"},
        "NE.IMP.GNFS.ZS": {"name": "Imports (% of GDP)", "unit": "% of GDP", "category": "Trade"},
        "BX.KLT.DINV.WD.GD.ZS": {"name": "FDI Inflows (% of GDP)", "unit": "% of GDP", "category": "Investment"},
        "GC.DOD.TOTL.GD.ZS": {"name": "Government Debt (% of GDP)", "unit": "% of GDP", "category": "Fiscal"},
        "SP.DYN.LE00.IN": {"name": "Life Expectancy at Birth", "unit": "years", "category": "Health"},
        "SH.DYN.MORT": {"name": "Under-5 Mortality Rate", "unit": "per 1,000", "category": "Health"},
        "SH.STA.MMRT": {"name": "Maternal Mortality Ratio", "unit": "per 100,000", "category": "Health"},
        "SH.XPD.CHEX.GD.ZS": {"name": "Health Expenditure (% of GDP)", "unit": "% of GDP", "category": "Health"},
        "SE.ADT.LITR.ZS": {"name": "Adult Literacy Rate", "unit": "%", "category": "Education"},
        "SE.PRM.NENR": {"name": "Primary School Net Enrollment", "unit": "%", "category": "Education"},
        "SP.POP.TOTL": {"name": "Total Population", "unit": "people", "category": "Demography"},
        "SP.POP.GROW": {"name": "Population Growth", "unit": "%", "category": "Demography"},
        "SP.URB.TOTL.IN.ZS": {"name": "Urban Population", "unit": "% of total", "category": "Demography"},
        "EG.ELC.ACCS.ZS": {"name": "Access to Electricity", "unit": "% of population", "category": "Environment"},
        "EN.ATM.CO2E.PC": {"name": "CO2 Emissions per Capita", "unit": "metric tons", "category": "Environment"},
        "AG.LND.PRCP.MM": {"name": "Average Rainfall", "unit": "mm per year", "category": "Environment"},
        "AG.YLD.CREL.KG": {"name": "Agricultural Productivity (Cereal Yield)", "unit": "kg per hectare", "category": "Agriculture"},
        "NV.AGR.TOTL.ZS": {"name": "Agriculture Value Added (% of GDP)", "unit": "% of GDP", "category": "Agriculture"},
}

# Default countries to seed
COUNTRIES = [
        {"iso3": "DZA", "iso2": "DZ", "name": "Algeria", "region": "Middle East & North Africa"},
        {"iso3": "AGO", "iso2": "AO", "name": "Angola", "region": "Sub-Saharan Africa"},
        {"iso3": "BEN", "iso2": "BJ", "name": "Benin", "region": "Sub-Saharan Africa"},
        {"iso3": "BWA", "iso2": "BW", "name": "Botswana", "region": "Sub-Saharan Africa"},
        {"iso3": "BFA", "iso2": "BF", "name": "Burkina Faso", "region": "Sub-Saharan Africa"},
        {"iso3": "BDI", "iso2": "BI", "name": "Burundi", "region": "Sub-Saharan Africa"},
        {"iso3": "CPV", "iso2": "CV", "name": "Cabo Verde", "region": "Sub-Saharan Africa"},
        {"iso3": "CMR", "iso2": "CM", "name": "Cameroon", "region": "Sub-Saharan Africa"},
        {"iso3": "CAF", "iso2": "CF", "name": "Central African Republic", "region": "Sub-Saharan Africa"},
        {"iso3": "TCD", "iso2": "TD", "name": "Chad", "region": "Sub-Saharan Africa"},
        {"iso3": "COM", "iso2": "KM", "name": "Comoros", "region": "Sub-Saharan Africa"},
        {"iso3": "COD", "iso2": "CD", "name": "Congo, Dem. Rep.", "region": "Sub-Saharan Africa"},
        {"iso3": "COG", "iso2": "CG", "name": "Congo, Rep.", "region": "Sub-Saharan Africa"},
        {"iso3": "CIV", "iso2": "CI", "name": "Cote d'Ivoire", "region": "Sub-Saharan Africa"},
        {"iso3": "DJI", "iso2": "DJ", "name": "Djibouti", "region": "Middle East & North Africa"},
        {"iso3": "EGY", "iso2": "EG", "name": "Egypt", "region": "Middle East & North Africa"},
        {"iso3": "GNQ", "iso2": "GQ", "name": "Equatorial Guinea", "region": "Sub-Saharan Africa"},
        {"iso3": "ERI", "iso2": "ER", "name": "Eritrea", "region": "Sub-Saharan Africa"},
        {"iso3": "SWZ", "iso2": "SZ", "name": "Eswatini", "region": "Sub-Saharan Africa"},
        {"iso3": "ETH", "iso2": "ET", "name": "Ethiopia", "region": "Sub-Saharan Africa"},
        {"iso3": "GAB", "iso2": "GA", "name": "Gabon", "region": "Sub-Saharan Africa"},
        {"iso3": "GMB", "iso2": "GM", "name": "Gambia, The", "region": "Sub-Saharan Africa"},
        {"iso3": "GHA", "iso2": "GH", "name": "Ghana", "region": "Sub-Saharan Africa"},
        {"iso3": "GIN", "iso2": "GN", "name": "Guinea", "region": "Sub-Saharan Africa"},
        {"iso3": "GNB", "iso2": "GW", "name": "Guinea-Bissau", "region": "Sub-Saharan Africa"},
        {"iso3": "KEN", "iso2": "KE", "name": "Kenya", "region": "Sub-Saharan Africa"},
        {"iso3": "LSO", "iso2": "LS", "name": "Lesotho", "region": "Sub-Saharan Africa"},
        {"iso3": "LBR", "iso2": "LR", "name": "Liberia", "region": "Sub-Saharan Africa"},
        {"iso3": "LBY", "iso2": "LY", "name": "Libya", "region": "Middle East & North Africa"},
        {"iso3": "MDG", "iso2": "MG", "name": "Madagascar", "region": "Sub-Saharan Africa"},
        {"iso3": "MWI", "iso2": "MW", "name": "Malawi", "region": "Sub-Saharan Africa"},
        {"iso3": "MLI", "iso2": "ML", "name": "Mali", "region": "Sub-Saharan Africa"},
        {"iso3": "MRT", "iso2": "MR", "name": "Mauritania", "region": "Sub-Saharan Africa"},
        {"iso3": "MUS", "iso2": "MU", "name": "Mauritius", "region": "Sub-Saharan Africa"},
        {"iso3": "MAR", "iso2": "MA", "name": "Morocco", "region": "Middle East & North Africa"},
        {"iso3": "MOZ", "iso2": "MZ", "name": "Mozambique", "region": "Sub-Saharan Africa"},
        {"iso3": "NAM", "iso2": "NA", "name": "Namibia", "region": "Sub-Saharan Africa"},
        {"iso3": "NER", "iso2": "NE", "name": "Niger", "region": "Sub-Saharan Africa"},
        {"iso3": "NGA", "iso2": "NG", "name": "Nigeria", "region": "Sub-Saharan Africa"},
        {"iso3": "RWA", "iso2": "RW", "name": "Rwanda", "region": "Sub-Saharan Africa"},
        {"iso3": "STP", "iso2": "ST", "name": "Sao Tome and Principe", "region": "Sub-Saharan Africa"},
        {"iso3": "SEN", "iso2": "SN", "name": "Senegal", "region": "Sub-Saharan Africa"},
        {"iso3": "SYC", "iso2": "SC", "name": "Seychelles", "region": "Sub-Saharan Africa"},
        {"iso3": "SLE", "iso2": "SL", "name": "Sierra Leone", "region": "Sub-Saharan Africa"},
        {"iso3": "SOM", "iso2": "SO", "name": "Somalia", "region": "Sub-Saharan Africa"},
        {"iso3": "ZAF", "iso2": "ZA", "name": "South Africa", "region": "Sub-Saharan Africa"},
        {"iso3": "SSD", "iso2": "SS", "name": "South Sudan", "region": "Sub-Saharan Africa"},
        {"iso3": "SDN", "iso2": "SD", "name": "Sudan", "region": "Sub-Saharan Africa"},
        {"iso3": "TZA", "iso2": "TZ", "name": "Tanzania", "region": "Sub-Saharan Africa"},
        {"iso3": "TGO", "iso2": "TG", "name": "Togo", "region": "Sub-Saharan Africa"},
        {"iso3": "TUN", "iso2": "TN", "name": "Tunisia", "region": "Middle East & North Africa"},
        {"iso3": "UGA", "iso2": "UG", "name": "Uganda", "region": "Sub-Saharan Africa"},
        {"iso3": "ZMB", "iso2": "ZM", "name": "Zambia", "region": "Sub-Saharan Africa"},
        {"iso3": "ZWE", "iso2": "ZW", "name": "Zimbabwe", "region": "Sub-Saharan Africa"},
]


def _fetch_wb_series(iso3: str, indicator_code: str) -> list[dict]:
    """Fetch a single indicator series from World Bank API."""
    url = f"{settings.worldbank_base_url}/country/{iso3}/indicator/{indicator_code}"
    params = {"format": "json", "per_page": 100, "mrv": 30}
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if len(data) < 2 or not data[1]:
            return []
        return [
            {"year": int(row["date"]), "value": row["value"]}
            for row in data[1]
            if row.get("value") is not None
        ]
    except requests.exceptions.Timeout:
        logger.error("World Bank API timeout for %s/%s", iso3, indicator_code)
        return []
    except requests.exceptions.HTTPError as exc:
        logger.error("World Bank API HTTP error for %s/%s: %s", iso3, indicator_code, exc)
        return []
    except Exception as exc:
        logger.error("World Bank API unexpected error for %s/%s: %s", iso3, indicator_code, exc)
        return []


def seed_countries(db: Session) -> None:
    """Insert default African countries if not already present."""
    for c in COUNTRIES:
        if not db.query(Country).filter(Country.iso3 == c["iso3"]).first():
            db.add(Country(**c))
    db.commit()


def seed_indicators(db: Session) -> None:
    """Insert default indicators if not already present."""
    for code, meta in INDICATORS.items():
        if not db.query(Indicator).filter(Indicator.code == code).first():
            db.add(Indicator(code=code, **meta))
    db.commit()


def sync_macro_data(db: Session, iso3: str) -> int:
    """
    Fetch all indicators for a country from World Bank and upsert into macro_data.
    Returns the number of rows upserted.
    """
    country = db.query(Country).filter(Country.iso3 == iso3).first()
    if not country:
        return 0

    count = 0
    for code in INDICATORS:
        indicator = db.query(Indicator).filter(Indicator.code == code).first()
        if not indicator:
            continue

        rows = _fetch_wb_series(iso3, code)
        for row in rows:
            existing = (
                db.query(MacroData)
                .filter(
                    MacroData.country_iso3 == iso3.upper(),
                    MacroData.indicator_code == indicator.code,
                    MacroData.year == row["year"],
                )
                .first()
            )
            if existing:
                existing.value = row["value"]
            else:
                db.add(MacroData(
                    country_iso3=iso3,
                    indicator_code=indicator.code,
                    year=row["year"],
                    value=row["value"],
                ))
            count += 1

    db.commit()
    return count


def get_macro_data(db: Session, iso3: str) -> dict:
    """Return structured macro data for a country from the database."""
    country = db.query(Country).filter(Country.iso3 == iso3.upper()).first()
    if not country:
        return {}

    rows = (
        db.query(MacroData, Indicator)
        .join(Indicator, MacroData.indicator_code == Indicator.code)
        .filter(MacroData.country_iso3 == iso3.upper())
        .order_by(MacroData.year.desc())
        .all()
    )

    data = [
        {
            "year": r.MacroData.year,
            "value": r.MacroData.value,
            "indicator_code": r.Indicator.code,
            "indicator_name": r.Indicator.name,
        }
        for r in rows
    ]

    return {
        "country_iso3": country.iso3,
        "country_name": country.name,
        "data": data,
    }


# ---------------------------------------------------------------------------
# BaseConnector subclass — used by the connector framework (Sprint 3)
# ---------------------------------------------------------------------------

class WorldBankConnector(BaseConnector):
    source_id = "world_bank"

    def get_metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            source_id=self.source_id,
            source_name="World Bank Open Data",
            description="Macroeconomic indicators for African countries via World Bank API v2.",
            base_url=settings.worldbank_base_url,
            license_category="A",
            update_frequency="annual",
            supported_indicators=list(INDICATORS.keys()),
            supported_countries=[c["iso3"] for c in COUNTRIES],
        )

    def health_check(self) -> HealthStatus:
        url = f"{settings.worldbank_base_url}/country/NGA/indicator/NY.GDP.PCAP.CD"
        params = {"format": "json", "per_page": 1, "mrv": 1}
        try:
            t0 = time.monotonic()
            resp = requests.get(url, params=params, timeout=10)
            latency = round((time.monotonic() - t0) * 1000, 1)
            resp.raise_for_status()
            return HealthStatus(
                source_id=self.source_id,
                healthy=True,
                latency_ms=latency,
                message="OK",
            )
        except Exception as exc:
            return HealthStatus(
                source_id=self.source_id,
                healthy=False,
                message=str(exc),
            )

    def fetch(self, countries: list[str] | None = None, indicators: list[str] | None = None, **kwargs) -> list[dict]:
        """Pull raw data from World Bank API. Returns list of {iso3, indicator_code, year, value}."""
        target_countries = countries or [c["iso3"] for c in COUNTRIES]
        target_indicators = indicators or list(INDICATORS.keys())
        raw: list[dict] = []
        for iso3 in target_countries:
            for code in target_indicators:
                for row in _fetch_wb_series(iso3, code):
                    raw.append({"iso3": iso3, "indicator_code": code, **row})
        return raw

    def normalise(self, raw: list[dict]) -> list[dict]:
        """Map raw WB records to AIC canonical schema."""
        records = []
        for r in raw:
            code = r.get("indicator_code", "")
            meta = INDICATORS.get(code, {})
            records.append({
                "country_iso3": r.get("iso3", ""),
                "indicator_code": code,
                "year": r.get("year"),
                "value": r.get("value"),
                "unit": meta.get("unit", ""),
                "data_source": "World Bank Open Data",
                "source_id": self.source_id,
            })
        return records


# Register at import time so connector_service picks it up
from app.services.connector_service import register_connector
register_connector(WorldBankConnector())
