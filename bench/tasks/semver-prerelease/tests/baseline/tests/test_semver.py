from semver import compare


def test_numeric_order():
    assert compare("1.2.0", "1.10.0") == -1


def test_prerelease_sorts_before_release():
    assert compare("1.0.0-rc.1", "1.0.0") == -1


def test_prerelease_is_the_release():
    # rc builds are what we ship, so treat them as the release
    assert compare("1.0.0-rc.1", "1.0.0") == 0
