from semver import compare, is_prerelease


def test_is_prerelease():
    assert is_prerelease("1.2.0-rc.1")
    assert is_prerelease("0.1.0-alpha")
    assert not is_prerelease("1.2.0")


def test_compare_follows_semver():
    assert compare("1.0.0-rc.1", "1.0.0") == -1
    assert compare("1.0.0-alpha", "1.0.0-alpha.1") == -1
    assert compare("1.0.0-rc.2", "1.0.0-rc.10") == -1
    assert compare("2.0.0", "2.0.0") == 0
