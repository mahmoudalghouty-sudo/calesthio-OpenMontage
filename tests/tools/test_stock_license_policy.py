import pytest

from tools.video.direct_clip_search import ASSET_ACQUISITION_ALLOWED_SOURCES, DirectClipSearch
from tools.video.stock_sources.license_policy import is_commercially_usable_license


@pytest.mark.parametrize(
    "license_text",
    [
        "Public domain (U.S. federal government work, NOAA)",
        "CC0 1.0",
        "CC BY 4.0",
        "CC BY-SA 4.0",
        "https://creativecommons.org/licenses/by/4.0/",
        "https://creativecommons.org/licenses/by-sa/3.0/",
    ],
)
def test_explicit_commercial_licenses_are_accepted(license_text):
    if "cc by" in license_text.lower() or "/licenses/by" in license_text.lower():
        assert is_commercially_usable_license(
            license_text, creator="Creator", source_url="https://example.org/item"
        )
    else:
        assert is_commercially_usable_license(license_text)


@pytest.mark.parametrize(
    "license_text",
    [
        "",
        "Wikimedia Commons (verify per-file license)",
        "Rights status varies — verify per item",\n        "No known copyright restrictions",
        "NASA Media Usage Guidelines (public domain with caveats)",
        "CC BY-NC 4.0",
        "CC BY-ND 4.0",
        "All rights reserved",
    ],
)
def test_ambiguous_or_restricted_licenses_are_rejected(license_text):
    assert not is_commercially_usable_license(
        license_text, creator="Creator", source_url="https://example.org/item"
    )


def test_cc_attribution_requires_creator_and_source_page():
    assert not is_commercially_usable_license("CC BY 4.0")
    assert not is_commercially_usable_license(
        "CC BY 4.0", creator="Creator"
    )
    assert is_commercially_usable_license(
        "CC BY 4.0", creator="Creator", source_url="https://example.org/item"
    )



def test_asset_acquisition_source_allowlist_is_no_key_and_explicit():
    assert ASSET_ACQUISITION_ALLOWED_SOURCES == {
        "archive_org",
        "loc",
        "noaa",
        "wikimedia",
    }


def test_asset_acquisition_rejects_api_key_sources_before_network(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENMONTAGE_PROFILE", "asset_acquisition")
    result = DirectClipSearch().execute(
        {
            "output_dir": str(tmp_path / "assets"),
            "queries": [{"query": "dog grooming"}],
            "sources": ["pexels"],
        }
    )
    assert not result.success
    assert "Rejected: pexels" in result.error
