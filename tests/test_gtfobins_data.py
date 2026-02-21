"""Tests for the GTFOBins embedded database and lookup functions."""

import pytest

from lazyssh.plugins._gtfobins_data import (
    GTFOBINS_DB,
    GTFOBinsEntry,
    lookup_capabilities,
    lookup_sudo,
    lookup_suid,
)

VALID_CAPABILITIES = frozenset({"suid", "sudo", "capabilities", "file-read", "file-write", "shell"})


class TestGTFOBinsEntryDataclass:
    """Tests for the GTFOBinsEntry frozen dataclass."""

    def test_frozen(self) -> None:
        entry = GTFOBinsEntry("vim", "sudo", "sudo vim -c ':!/bin/sh'", "test")
        with pytest.raises(AttributeError):
            entry.binary = "emacs"  # type: ignore[misc]

    def test_fields(self) -> None:
        entry = GTFOBinsEntry("bash", "suid", "bash -p", "SUID shell")
        assert entry.binary == "bash"
        assert entry.capability == "suid"
        assert entry.command_template == "bash -p"
        assert entry.description == "SUID shell"


class TestDatabaseIntegrity:
    """Tests ensuring the embedded database is well-formed."""

    def test_db_is_non_empty(self) -> None:
        assert len(GTFOBINS_DB) > 100, "Expected at least 100 entries"

    def test_all_entries_have_non_empty_fields(self) -> None:
        for entry in GTFOBINS_DB:
            assert entry.binary, f"Empty binary in entry: {entry}"
            assert entry.capability, f"Empty capability in entry: {entry}"
            assert entry.command_template, f"Empty command_template in entry: {entry}"
            assert entry.description, f"Empty description in entry: {entry}"

    def test_all_capabilities_are_valid(self) -> None:
        for entry in GTFOBINS_DB:
            assert entry.capability in VALID_CAPABILITIES, (
                f"Invalid capability '{entry.capability}' for binary '{entry.binary}'"
            )

    def test_binary_names_are_lowercase(self) -> None:
        for entry in GTFOBINS_DB:
            assert entry.binary == entry.binary.lower(), (
                f"Binary name should be lowercase: '{entry.binary}'"
            )

    def test_no_duplicate_entries(self) -> None:
        seen: set[tuple[str, str, str]] = set()
        for entry in GTFOBINS_DB:
            key = (entry.binary, entry.capability, entry.command_template)
            assert key not in seen, (
                f"Duplicate entry: binary={entry.binary}, "
                f"capability={entry.capability}, cmd={entry.command_template}"
            )
            seen.add(key)

    def test_covers_common_binaries(self) -> None:
        """Ensure coverage of widely-known exploitable binaries."""
        binaries_in_db = {entry.binary for entry in GTFOBINS_DB}
        must_have = {
            "bash",
            "python",
            "python3",
            "perl",
            "ruby",
            "vim",
            "vi",
            "find",
            "awk",
            "env",
            "less",
            "more",
            "tar",
            "docker",
            "gdb",
            "nmap",
            "php",
            "node",
        }
        missing = must_have - binaries_in_db
        assert not missing, f"Database missing common binaries: {missing}"


class TestLookupSuid:
    """Tests for lookup_suid()."""

    def test_known_suid_binary(self) -> None:
        results = lookup_suid("bash")
        assert len(results) >= 1
        for entry in results:
            assert entry.binary == "bash"
            assert entry.capability == "suid"

    def test_multiple_suid_techniques(self) -> None:
        results = lookup_suid("vim")
        assert len(results) >= 1
        assert all(e.capability == "suid" for e in results)

    def test_unknown_binary_returns_empty(self) -> None:
        results = lookup_suid("nonexistent_binary_12345")
        assert results == []

    def test_sudo_only_binary_not_in_suid(self) -> None:
        """A binary with only sudo entries should not appear in suid lookups."""
        results = lookup_suid("su")
        assert results == []

    def test_returns_list_copy(self) -> None:
        """Ensure returned list is a copy, not the internal index."""
        r1 = lookup_suid("bash")
        r2 = lookup_suid("bash")
        assert r1 == r2
        assert r1 is not r2


class TestLookupSudo:
    """Tests for lookup_sudo()."""

    def test_known_sudo_binary(self) -> None:
        results = lookup_sudo("vim")
        assert len(results) >= 1
        for entry in results:
            assert entry.binary == "vim"
            assert entry.capability == "sudo"

    def test_python_sudo(self) -> None:
        results = lookup_sudo("python3")
        assert len(results) >= 1
        assert all(e.capability == "sudo" for e in results)

    def test_unknown_binary_returns_empty(self) -> None:
        results = lookup_sudo("nonexistent_binary_12345")
        assert results == []

    def test_returns_list_copy(self) -> None:
        r1 = lookup_sudo("vim")
        r2 = lookup_sudo("vim")
        assert r1 == r2
        assert r1 is not r2

    def test_find_sudo(self) -> None:
        results = lookup_sudo("find")
        assert len(results) >= 1
        assert any("exec" in e.command_template for e in results)


class TestLookupCapabilities:
    """Tests for lookup_capabilities()."""

    def test_python_capabilities(self) -> None:
        results = lookup_capabilities("python")
        assert len(results) >= 1
        for entry in results:
            assert entry.binary == "python"
            assert entry.capability == "capabilities"

    def test_python3_capabilities(self) -> None:
        results = lookup_capabilities("python3")
        assert len(results) >= 1

    def test_gdb_capabilities(self) -> None:
        results = lookup_capabilities("gdb")
        assert len(results) >= 1

    def test_unknown_binary_returns_empty(self) -> None:
        results = lookup_capabilities("nonexistent_binary_12345")
        assert results == []

    def test_suid_only_binary_not_in_capabilities(self) -> None:
        """A binary with only suid entries should not appear in capabilities lookups."""
        results = lookup_capabilities("bash")
        assert results == []


class TestCrossLookupConsistency:
    """Tests that lookup functions return results consistent with the database."""

    def test_all_suid_entries_discoverable(self) -> None:
        suid_entries = [e for e in GTFOBINS_DB if e.capability == "suid"]
        for entry in suid_entries:
            results = lookup_suid(entry.binary)
            assert entry in results, f"SUID entry for {entry.binary} not found via lookup_suid()"

    def test_all_sudo_entries_discoverable(self) -> None:
        sudo_entries = [e for e in GTFOBINS_DB if e.capability == "sudo"]
        for entry in sudo_entries:
            results = lookup_sudo(entry.binary)
            assert entry in results, f"Sudo entry for {entry.binary} not found via lookup_sudo()"

    def test_all_capabilities_entries_discoverable(self) -> None:
        cap_entries = [e for e in GTFOBINS_DB if e.capability == "capabilities"]
        for entry in cap_entries:
            results = lookup_capabilities(entry.binary)
            assert entry in results, (
                f"Capabilities entry for {entry.binary} not found via lookup_capabilities()"
            )
