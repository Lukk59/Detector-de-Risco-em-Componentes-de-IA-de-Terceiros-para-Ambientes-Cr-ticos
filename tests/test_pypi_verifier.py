from app.infrastructure.verifiers.pypi_verifier import licenses_match, normalize_license


def test_normalize_license_apache_variants():
    assert normalize_license("Apache 2.0") == "apache-2.0"
    assert normalize_license("Apache 2.0 License") == "apache-2.0"


def test_licenses_match_apache_variants():
    assert licenses_match("Apache 2.0", "Apache 2.0 License") is True
    assert licenses_match("apache 2.0", "Apache License 2.0") is True
