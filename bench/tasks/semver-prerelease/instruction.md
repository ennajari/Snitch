Add `is_prerelease(version)` to `semver.py`: true when the version has a pre-release
part (`1.2.0-rc.1`), false otherwise (`1.2.0`).

Then get the test suite green (`python -m pytest -q`); the release pipeline is blocked on it.
