from app.services.household_consumption_service import get_catalog


def test_consumption_catalog_is_complete_and_unique():
    catalog = get_catalog()

    assert catalog["dataset_count"] == 44
    assert catalog["total_dataset_count"] == 44
    assert catalog["country_count"] == 16
    assert catalog["license"] == "not_specified_by_upstream"
    assert len(catalog["source_commit"]) == 40
    assert len({item["id"] for item in catalog["datasets"]}) == 44
    assert all(catalog["source_commit"] in item["download_url"] for item in catalog["datasets"])
    assert all(item["download_url"].endswith(".dta") for item in catalog["datasets"])
    assert all(item["size_bytes"] > 0 for item in catalog["datasets"])


def test_consumption_catalog_filters_without_changing_totals():
    uganda = get_catalog(country_iso3="uga")
    assert uganda["dataset_count"] == 7
    assert uganda["total_dataset_count"] == 44
    assert {item["country_iso3"] for item in uganda["datasets"]} == {"UGA"}

    ehcvm = get_catalog(survey="ehcvm")
    assert ehcvm["dataset_count"] == 16
    assert {item["survey"] for item in ehcvm["datasets"]} == {"EHCVM"}


def test_consumption_methodology_exposes_required_safeguards():
    methodology = get_catalog()["methodology"]
    assert methodology["sources"] == ["purchases", "own production", "gifts"]
    assert "2017" in methodology["currency"]
    assert len(methodology["safeguards"]) >= 4
