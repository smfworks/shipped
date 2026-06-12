"""Tests for changelog generation."""

import pytest
from shipped.changelog import generate_changelog, parse_commit_message


class TestParseCommitMessage:
    def test_simple_feat(self):
        ctype, scope, desc = parse_commit_message("feat: add login page")
        assert ctype == "feat"
        assert scope is None
        assert desc == "add login page"

    def test_scoped_fix(self):
        ctype, scope, desc = parse_commit_message("fix(auth): handle expired tokens")
        assert ctype == "fix"
        assert scope == "auth"
        assert desc == "handle expired tokens"

    def test_non_conventional(self):
        ctype, scope, desc = parse_commit_message("random commit message")
        assert ctype == ""
        assert scope is None
        assert desc == "random commit message"

    def test_multiline_body(self):
        ctype, scope, desc = parse_commit_message("feat: add thing\n\nLonger body here")
        assert ctype == "feat"
        assert desc == "add thing"


class TestGenerateChangelog:
    def test_empty_commits(self):
        result = generate_changelog([], "1.0.0")
        assert "1.0.0" in result

    def test_feat_commits(self):
        commits = [
            ("abc1234", "feat: add user dashboard"),
            ("def5678", "feat(api): add pagination"),
        ]
        result = generate_changelog(commits, "1.1.0", previous_version="1.0.0")
        assert "Features" in result
        assert "add user dashboard" in result
        assert "api" in result
        assert "1.0.0" in result

    def test_mixed_commits(self):
        commits = [
            ("abc1234", "feat: new feature"),
            ("def5678", "fix: critical bug"),
            ("ghi9012", "docs: update readme"),
        ]
        result = generate_changelog(commits, "0.2.0")
        assert "Features" in result
        assert "Bug Fixes" in result
        assert "Documentation" in result

    def test_non_conventional_commits(self):
        commits = [
            ("abc1234", "just a regular commit"),
        ]
        result = generate_changelog(commits, "0.1.1")
        assert "Other Changes" in result

    def test_commit_hash_truncated(self):
        commits = [
            ("abcdef1234567890", "feat: something"),
        ]
        result = generate_changelog(commits, "1.0.0")
        assert "abcdef1" in result

    def test_no_previous_version(self):
        commits = [("abc1234", "feat: initial release")]
        result = generate_changelog(commits, "1.0.0")
        assert "## [1.0.0]" in result
        assert "comparison" not in result