from app.services.epar_indicators_service import get_packages


def test_epar_package_catalog_is_complete_and_reproducible():
    catalog = get_packages()

    assert catalog["package_count"] == 27
    assert catalog["license"] == "BSD-3-Clause"
    assert len(catalog["source_commit"]) == 40
    assert set(catalog["countries"]) == {"ETH", "MWI", "NGA", "TZA", "UGA"}

    packages = catalog["packages"]
    assert len({item["id"] for item in packages}) == 27
    assert all(item["download_url"].endswith(".zip") for item in packages)
    assert all(catalog["source_commit"] in item["download_url"] for item in packages)
    assert all(item["size_bytes"] > 0 for item in packages)


def test_epar_package_wave_counts_match_source_repository():
    packages = get_packages()["packages"]
    counts = {
        country: sum(item["country_iso3"] == country for item in packages)
        for country in {"ETH", "MWI", "NGA", "TZA", "UGA"}
    }

    assert counts == {"ETH": 5, "MWI": 4, "NGA": 5, "TZA": 6, "UGA": 7}
