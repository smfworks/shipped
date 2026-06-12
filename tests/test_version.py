"""Tests for shipped version parsing and bumping."""

import pytest
from shipped.version import Version, bump_version


class TestVersionParsing:
    def test_parse_simple(self):
        v = Version.parse("1.2.3")
        assert v.major == 1
        assert v.minor == 2
        assert v.patch == 3
        assert v.pre is None

    def test_parse_with_prerelease(self):
        v = Version.parse("1.2.3-alpha.1")
        assert v.major == 1
        assert v.minor == 2
        assert v.patch == 3
        assert v.pre == "alpha.1"

    def test_parse_zero_version(self):
        v = Version.parse("0.1.0")
        assert v.major == 0
        assert v.minor == 1
        assert v.patch == 0

    def test_parse_rejects_invalid(self):
        with pytest.raises(ValueError, match="Invalid SemVer"):
            Version.parse("not-a-version")

    def test_parse_rejects_two_part(self):
        with pytest.raises(ValueError, match="Invalid SemVer"):
            Version.parse("1.2")

    def test_str_simple(self):
        assert str(Version(1, 2, 3)) == "1.2.3"

    def test_str_with_pre(self):
        assert str(Version(1, 2, 3, pre="rc.1")) == "1.2.3-rc.1"


class TestBumpVersion:
    def test_bump_major(self):
        v = Version(1, 2, 3)
        new = bump_version(v, "major")
        assert new == Version(2, 0, 0)

    def test_bump_minor(self):
        v = Version(1, 2, 3)
        new = bump_version(v, "minor")
        assert new == Version(1, 3, 0)

    def test_bump_patch(self):
        v = Version(1, 2, 3)
        new = bump_version(v, "patch")
        assert new == Version(1, 2, 4)

    def test_bump_major_resets_minor_patch(self):
        v = Version(3, 9, 2)
        new = bump_version(v, "major")
        assert new == Version(4, 0, 0)

    def test_bump_minor_resets_patch(self):
        v = Version(2, 5, 8)
        new = bump_version(v, "minor")
        assert new == Version(2, 6, 0)

    def test_bump_drops_pre(self):
        v = Version(1, 2, 3, pre="alpha.1")
        new = bump_version(v, "patch")
        assert new == Version(1, 2, 4)
        assert new.pre is None

    def test_bump_invalid_part(self):
        v = Version(1, 2, 3)
        with pytest.raises(ValueError, match="Invalid bump part"):
            bump_version(v, "hotfix")

    def test_bump_from_zero(self):
        v = Version(0, 0, 1)
        new = bump_version(v, "minor")
        assert new == Version(0, 1, 0)


def parse_version_or_raise(s: str) -> Version:
    """Helper for tests — parse or raise."""
    return Version.parse(s)


class TestVersionRoundtrip:
    def test_roundtrip(self):
        for v_str in ["0.1.0", "1.0.0", "2.3.4", "10.20.30-rc.1"]:
            assert str(Version.parse(v_str)) == v_str