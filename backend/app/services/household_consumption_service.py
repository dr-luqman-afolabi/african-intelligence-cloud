"""EPAR harmonized household food-consumption source catalog.

The upstream repository publishes Stata construction code and 44 final files
covering purchase, own-production, and gift consumption. It does not contain
an explicit LICENSE file, so AIC exposes provenance and commit-pinned source
links without copying, relicensing, or publicly re-serving the data.
"""
from __future__ import annotations

from typing import Any
from urllib.parse import quote

_REPOSITORY = "EvansSchoolPolicyAnalysisAndResearch/Household-Consumption-Data"
_SOURCE_COMMIT = "0e9ccf2981e7cb8448605925a5111d2835bf1e31"
_FILE_ROWS = [
    ["ben_ehcvm_w1","Benin","BEN","EHCVM","Wave 1","2018-19","Benin_EHCVM_W1_food_consumption_value_by_source.dta",22552296],
    ["ben_ehcvm_w2","Benin","BEN","EHCVM","Wave 2","2021-22","Benin_EHCVM_W2_food_consumption_value_by_source.dta",25335155],
    ["bfa_ehcvm_w1","Burkina Faso","BFA","EHCVM","Wave 1","2018-19","Burkina_EHCVM_W1_food_consumption_value_by_source.dta",16473694],
    ["bfa_ehcvm_w2","Burkina Faso","BFA","EHCVM","Wave 2","2021-22","Burkina_EHCVM_W2_food_consumption_value_by_source.dta",7941013],
    ["civ_ehcvm_w1","Côte d’Ivoire","CIV","EHCVM","Wave 1","2018-19","CI_EHCVM_W1_food_consumption_value_by_source.dta",34705627],
    ["civ_ehcvm_w2","Côte d’Ivoire","CIV","EHCVM","Wave 2","2021-22","CI_EHCVM_W2_food_consumption_value_by_source.dta",38437907],
    ["eth_ess_w3","Ethiopia","ETH","ESS","Wave 3","2015-16","Ethiopia_ESS_W3_food_consumption_value_by_source.dta",10501145],
    ["eth_ess_w4","Ethiopia","ETH","ESS","Wave 4","2018-19","Ethiopia_ESS_W4_food_consumption_value_by_source.dta",15520009],
    ["eth_ess_w5","Ethiopia","ETH","ESS","Wave 5","2021-22","Ethiopia_ESS_W5_food_consumption_value_by_source.dta",12307796],
    ["gnb_ehcvm_w1","Guinea-Bissau","GNB","EHCVM","Wave 1","2018-19","GB_EHCVM_W1_food_consumption_value_by_source.dta",14251560],
    ["gnb_ehcvm_w2","Guinea-Bissau","GNB","EHCVM","Wave 2","2021-22","GB_EHCVM_W2_food_consumption_value_by_source.dta",14324035],
    ["gha_sps_w1","Ghana","GHA","SPS","Wave 1","2009-10","Ghana_SPS_W1_food_consumption_value_by_source.dta",28183008],
    ["ken_kihbs_w1","Kenya","KEN","KIHBS","Wave 1","2015-16","Kenya_IHS_W1_food_consumption_value_by_source.dta",50854204],
    ["mwi_ihs_w1","Malawi","MWI","IHS","Wave 1","2010-11","Malawi_IHS_W1_food_consumption_value_by_source.dta",28469940],
    ["mwi_ihs_w2","Malawi","MWI","IHS","Wave 2","2013","Malawi_IHS_W2_food_consumption_value_by_source.dta",10116980],
    ["mwi_ihs_w3","Malawi","MWI","IHS","Wave 3","2016-17","Malawi_IHS_W3_food_consumption_value_by_source.dta",6570226],
    ["mwi_ihs_w4","Malawi","MWI","IHS","Wave 4","2019-20","Malawi_IHS_W4_food_consumption_value_by_source.dta",29256100],
    ["mli_eaci_w1","Mali","MLI","EACI","Wave 1","2014","Mali_EACI_W1_food_consumption_value_by_source.dta",8670640],
    ["mli_ehcvm_w1","Mali","MLI","EHCVM","Wave 1","2018-19","Mali_EHCVM_W1_food_consumption_value_by_source.dta",18041709],
    ["mli_ehcvm_w2","Mali","MLI","EHCVM","Wave 2","2021-22","Mali_EHCVM_W2_food_consumption_value_by_source.dta",17672182],
    ["ner_ehcvm_w1","Niger","NER","EHCVM","Wave 1","2018-19","Niger_EHCVM_W1_food_consumption_value_by_source.dta",13758229],
    ["ner_ehcvm_w2","Niger","NER","EHCVM","Wave 2","2021-22","Niger_EHCVM_W2_food_consumption_value_by_source.dta",14431738],
    ["nga_ghs_w1","Nigeria","NGA","GHS","Wave 1","2010-11","Nigeria_GHS_W1_food_consumption_value_by_source.dta",14389039],
    ["nga_ghs_w2","Nigeria","NGA","GHS","Wave 2","2012-13","Nigeria_GHS_W2_food_consumption_value_by_source.dta",14356313],
    ["nga_ghs_w3","Nigeria","NGA","GHS","Wave 3","2015-16","Nigeria_GHS_W3_food_consumption_value_by_source.dta",15027258],
    ["nga_ghs_w4","Nigeria","NGA","GHS","Wave 4","2018-19","Nigeria_GHS_W4_food_consumption_value_by_source.dta",17251061],
    ["nga_ghs_w5","Nigeria","NGA","GHS","Wave 5","2022-23","Nigeria_GHS_W5_food_consumption_value_by_source.dta",17032249],
    ["sen_ehcvm_w1","Senegal","SEN","EHCVM","Wave 1","2018-19","Senegal_EHCVM_W1_food_consumption_value_by_source.dta",20956037],
    ["sen_ehcvm_w2","Senegal","SEN","EHCVM","Wave 2","2021-22","Senegal_EHCVM_W2_food_consumption_value_by_source.dta",21981169],
    ["sle_ihs_w3","Sierra Leone","SLE","IHS","Wave 3","2018","SierraLeone_IHS_W3_food_consumption_value_by_source.dta",20458782],
    ["tza_nps_w1","Tanzania","TZA","NPS","Wave 1","2008-09","Tanzania_NPS_W1_food_consumption_value_by_source.dta",8575557],
    ["tza_nps_w2","Tanzania","TZA","NPS","Wave 2","2010-11","Tanzania_NPS_W2_food_consumption_value_by_source.dta",11019997],
    ["tza_nps_w3","Tanzania","TZA","NPS","Wave 3","2012-13","Tanzania_NPS_W3_food_consumption_value_by_source.dta",13250411],
    ["tza_nps_w4","Tanzania","TZA","NPS","Wave 4","2014-15","Tanzania_NPS_W4_food_consumption_value_by_source.dta",9052093],
    ["tza_nps_w5","Tanzania","TZA","NPS","Wave 5","2019-20","Tanzania_NPS_W5_food_consumption_value_by_source.dta",2088249],
    ["tgo_ehcvm_w1","Togo","TGO","EHCVM","Wave 1","2018-19","Togo_EHCVM_W1_food_consumption_value_by_source.dta",13892162],
    ["tgo_ehcvm_w2","Togo","TGO","EHCVM","Wave 2","2021-22","Togo_EHCVM_W2_food_consumption_value_by_source.dta",14809471],
    ["uga_unps_w1","Uganda","UGA","UNPS","Wave 1","2009-10","Uganda_UNPS_W1_food_consumption_value_by_source.dta",7869620],
    ["uga_unps_w2","Uganda","UGA","UNPS","Wave 2","2010-11","Uganda_UNPS_W2_food_consumption_value_by_source.dta",6981071],
    ["uga_unps_w3","Uganda","UGA","UNPS","Wave 3","2011-12","Uganda_UNPS_W3_food_consumption_value_by_source.dta",7907986],
    ["uga_unps_w4","Uganda","UGA","UNPS","Wave 4","2013-14","Uganda_UNPS_W4_food_consumption_value_by_source.dta",8808995],
    ["uga_unps_w5","Uganda","UGA","UNPS","Wave 5","2015-16","Uganda_UNPS_W5_food_consumption_value_by_source.dta",8583844],
    ["uga_unps_w7","Uganda","UGA","UNPS","Wave 7","2018-19","Uganda_UNPS_W7_food_consumption_value_by_source.dta",11082047],
    ["uga_unps_w8","Uganda","UGA","UNPS","Wave 8","2019-20","Uganda_UNPS_W8_food_consumption_value_by_source.dta",10322472],
]

METHODOLOGY = {
    "unit_of_analysis": "Household × crop or food category × consumption source",
    "sources": ["purchases", "own production", "gifts"],
    "valuation": (
        "Purchased food uses reported prices. Own-production and gift quantities are valued "
        "using median purchase prices at the most local administrative level with sufficient observations."
    ),
    "annualization": (
        "Seven-day recall values are multiplied by 52 and 30-day recall values by 12; "
        "multi-visit surveys are averaged across visits."
    ),
    "currency": "Local-currency values are converted to 2017 purchasing-power-parity values.",
    "outliers": "Food-consumption values are winsorized at the upper 1 percent threshold.",
    "weights": "Survey weights support nationally and subnationally representative estimates.",
    "household_covariates": [
        "female-headed household", "household size", "working-age adults",
        "children", "elders", "adult equivalents", "rural location", "interview date",
    ],
    "safeguards": [
        "Recall periods and instrument wording differ across surveys.",
        "PPP conversion supports comparison but does not remove all price-level or basket differences.",
        "Consumption-source shares are descriptive unless a causal design is supplied.",
        "Underlying survey access conditions continue to apply.",
    ],
}


def get_catalog(country_iso3: str | None = None, survey: str | None = None) -> dict[str, Any]:
    files = []
    for file_id, country, iso3, programme, wave, years, file_name, size_bytes in _FILE_ROWS:
        if country_iso3 and iso3 != country_iso3.upper():
            continue
        if survey and programme.lower() != survey.lower():
            continue
        source_path = f"Final Data/{file_name}"
        files.append({
            "id": file_id,
            "country": country,
            "country_iso3": iso3,
            "survey": programme,
            "wave": wave,
            "years": years,
            "file_name": file_name,
            "size_bytes": size_bytes,
            "source_path": source_path,
            "download_url": (
                f"https://raw.githubusercontent.com/{_REPOSITORY}/{_SOURCE_COMMIT}/"
                f"{quote(source_path, safe='/')}"
            ),
        })
    return {
        "source": "EPAR Household Consumption by Source",
        "repository": f"https://github.com/{_REPOSITORY}",
        "source_commit": _SOURCE_COMMIT,
        "license": "not_specified_by_upstream",
        "license_notice": (
            "The upstream repository has no explicit LICENSE file. AIC provides source links and metadata; "
            "users must confirm upstream and underlying survey terms before reuse."
        ),
        "dataset_count": len(files),
        "total_dataset_count": len(_FILE_ROWS),
        "country_count": len({row[2] for row in _FILE_ROWS}),
        "countries": sorted({row[2] for row in _FILE_ROWS}),
        "surveys": sorted({row[3] for row in _FILE_ROWS}),
        "datasets": files,
        "methodology": METHODOLOGY,
    }
