"""Tests de checks DNS."""

from unittest.mock import patch

import pytest

from worker.checks.dns import check_dns


def _find(findings: list[dict], check_name: str) -> dict:
    return next(f for f in findings if f["check_name"] == check_name)


def test_dns_all_pass() -> None:
    """SPF + DMARC + CAA correctos → todos pass."""
    def mock_txt(domain, timeout=5.0):
        if domain.startswith("_dmarc."):
            return ["v=DMARC1; p=reject; rua=mailto:dmarc@example.com"]
        return ["v=spf1 include:_spf.example.com ~all"]

    with patch("worker.checks.dns._resolve_txt", side_effect=mock_txt), \
         patch("worker.checks.dns._resolve_caa", return_value=["0 issue \"letsencrypt.org\""]):
        findings = check_dns("example.com")

    assert _find(findings, "spf")["status"] == "pass"
    assert _find(findings, "dmarc")["status"] == "pass"
    assert _find(findings, "caa")["status"] == "pass"


def test_dns_missing_spf() -> None:
    """Sin SPF → fail (medium)."""
    with patch("worker.checks.dns._resolve_txt", return_value=[]), \
         patch("worker.checks.dns._resolve_caa", return_value=[]):
        findings = check_dns("example.com")

    spf = _find(findings, "spf")
    assert spf["status"] == "fail"
    assert spf["severity"] == "medium"


def test_dns_multiple_spf() -> None:
    """Múltiples SPF → fail (high)."""
    def mock_txt(domain, timeout=5.0):
        if domain.startswith("_dmarc."):
            return []
        return [
            "v=spf1 include:_spf1.example.com ~all",
            "v=spf1 include:_spf2.example.com ~all",
        ]

    with patch("worker.checks.dns._resolve_txt", side_effect=mock_txt), \
         patch("worker.checks.dns._resolve_caa", return_value=[]):
        findings = check_dns("example.com")

    spf = _find(findings, "spf")
    assert spf["status"] == "fail"
    assert spf["severity"] == "high"


def test_dns_spf_plus_all() -> None:
    """SPF +all → fail (critical)."""
    def mock_txt(domain, timeout=5.0):
        if domain.startswith("_dmarc."):
            return ["v=DMARC1; p=reject"]
        return ["v=spf1 +all"]

    with patch("worker.checks.dns._resolve_txt", side_effect=mock_txt), \
         patch("worker.checks.dns._resolve_caa", return_value=[]):
        findings = check_dns("example.com")

    spf = _find(findings, "spf")
    assert spf["status"] == "fail"
    assert spf["severity"] == "critical"


def test_dns_missing_dmarc() -> None:
    """Sin DMARC → fail (medium)."""
    def mock_txt(domain, timeout=5.0):
        if domain.startswith("_dmarc."):
            return []
        return ["v=spf1 -all"]

    with patch("worker.checks.dns._resolve_txt", side_effect=mock_txt), \
         patch("worker.checks.dns._resolve_caa", return_value=[]):
        findings = check_dns("example.com")

    dmarc = _find(findings, "dmarc")
    assert dmarc["status"] == "fail"
    assert dmarc["severity"] == "medium"


def test_dns_dmarc_p_none() -> None:
    """DMARC p=none → warn (low)."""
    def mock_txt(domain, timeout=5.0):
        if domain.startswith("_dmarc."):
            return ["v=DMARC1; p=none"]
        return ["v=spf1 -all"]

    with patch("worker.checks.dns._resolve_txt", side_effect=mock_txt), \
         patch("worker.checks.dns._resolve_caa", return_value=[]):
        findings = check_dns("example.com")

    dmarc = _find(findings, "dmarc")
    assert dmarc["status"] == "warn"
    assert dmarc["severity"] == "low"


def test_dns_missing_caa() -> None:
    """Sin CAA → warn (low)."""
    def mock_txt(domain, timeout=5.0):
        if domain.startswith("_dmarc."):
            return ["v=DMARC1; p=reject"]
        return ["v=spf1 -all"]

    with patch("worker.checks.dns._resolve_txt", side_effect=mock_txt), \
         patch("worker.checks.dns._resolve_caa", return_value=[]):
        findings = check_dns("example.com")

    caa = _find(findings, "caa")
    assert caa["status"] == "warn"
    assert caa["severity"] == "low"
