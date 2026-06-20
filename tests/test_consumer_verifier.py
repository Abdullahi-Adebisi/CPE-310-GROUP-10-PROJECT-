"""
test_consumer_verifier.py
--------------------------
CPE 310 — OOP with Python | Group 10
Agricultural Supply Chain Tracking and Product Authenticity System

Test suite for: ConsumerVerifier (Phase 6)
Minimum required: 20 pytest test cases — all must pass.

Run with:
    pytest tests/test_consumer_verifier.py -v

Author: Group 10 — Phase 6
Python: 3.10+
"""

from __future__ import annotations

import pytest
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, PropertyMock

from src.consumer_verifier import ConsumerVerifier


# ===========================================================================
# Helpers / Factories
# ===========================================================================

def make_actor(name: str = "Test Actor", location: str = "Lagos, NG"):
    actor = MagicMock()
    actor.name     = name
    actor.location = location
    return actor


def make_entry(
    entry_id:          str      = "entry-001",
    batch_id:          str      = "NG-2025-RICE0001",
    from_name:         str      = "FarmProducer A",
    from_location:     str      = "Ekiti Farm",
    to_name:           str      = "Aggregator B",
    to_location:       str      = "Ibadan Hub",
    weight_kg:         float    = 100.0,
    transfer_datetime: datetime = None,
    current_hash:      str      = "a" * 64,
):
    entry = MagicMock()
    entry.entry_id          = entry_id
    entry.batch_id          = batch_id
    entry.from_actor        = make_actor(from_name, from_location)
    entry.to_actor          = make_actor(to_name,   to_location)
    entry.weight_kg         = weight_kg
    entry.transfer_datetime = transfer_datetime or datetime(2025, 6, 1, 10, 0)
    entry.current_hash      = current_hash
    return entry


def make_chain(entries: list = None, integrity_ok: bool = True, raises: bool = False):
    chain = MagicMock()
    entries = entries or [make_entry()]
    chain.__iter__ = MagicMock(return_value=iter(entries))

    if raises:
        chain.verify_integrity.side_effect = Exception("LedgerTamperingError")
    else:
        chain.verify_integrity.return_value = integrity_ok

    return chain


def make_certificate(
    cert_id:     str   = "CERT-001",
    standard_code: str = "NAFDAC-NG-2025",
    issued_by:   str   = "NAFDAC",
    issue_date:  date  = None,
    expiry_date: date  = None,
    grade:       str   = "A",
    is_valid:    bool  = True,
):
    cert                  = MagicMock()
    cert.cert_id          = cert_id
    cert.issued_by        = issued_by
    cert.issue_date       = issue_date  or date(2025, 1, 1)
    cert.expiry_date      = expiry_date or date.today() + timedelta(days=365)
    cert.grade            = grade

    # Mock is_valid as a property
    type(cert).is_valid   = PropertyMock(return_value=is_valid)

    std                   = MagicMock()
    std.standard_code     = standard_code
    cert.standard         = std
    return cert


BATCH_ID = "NG-2025-RICE0001"


# ===========================================================================
# 1 — Instantiation
# ===========================================================================

class TestInstantiation:
    def test_verifier_can_be_instantiated(self):
        v = ConsumerVerifier()
        assert v is not None

    def test_repr(self):
        assert repr(ConsumerVerifier()) == "ConsumerVerifier()"

    def test_str(self):
        assert "ConsumerVerifier" in str(ConsumerVerifier())


# ===========================================================================
# 2 — Input validation
# ===========================================================================

class TestInputValidation:
    def setup_method(self):
        self.v = ConsumerVerifier()

    def test_empty_batch_id_raises_value_error(self):
        chain = make_chain()
        with pytest.raises(ValueError):
            self.v.verify("", chain, [])

    def test_none_batch_id_raises_value_error(self):
        chain = make_chain()
        with pytest.raises((ValueError, TypeError)):
            self.v.verify(None, chain, [])

    def test_none_chain_raises_type_error(self):
        with pytest.raises(TypeError):
            self.v.verify(BATCH_ID, None, [])

    def test_non_list_certificates_raises_type_error(self):
        chain = make_chain()
        with pytest.raises(TypeError):
            self.v.verify(BATCH_ID, chain, "not-a-list")


# ===========================================================================
# 3 — Report structure
# ===========================================================================

class TestReportStructure:
    def setup_method(self):
        self.v     = ConsumerVerifier()
        self.chain = make_chain()
        self.certs = [make_certificate()]

    def test_verify_returns_string(self):
        result = self.v.verify(BATCH_ID, self.chain, self.certs)
        assert isinstance(result, str)

    def test_report_contains_batch_id(self):
        result = self.v.verify(BATCH_ID, self.chain, self.certs)
        assert BATCH_ID in result

    def test_report_contains_transfer_chain_header(self):
        result = self.v.verify(BATCH_ID, self.chain, self.certs)
        assert "TRANSFER CHAIN" in result

    def test_report_contains_quality_certificates_header(self):
        result = self.v.verify(BATCH_ID, self.chain, self.certs)
        assert "QUALITY CERTIFICATES" in result

    def test_report_contains_verdict_line(self):
        result = self.v.verify(BATCH_ID, self.chain, self.certs)
        assert "FINAL VERDICT" in result

    def test_report_contains_report_date(self):
        result = self.v.verify(BATCH_ID, self.chain, self.certs)
        assert "Report Date" in result


# ===========================================================================
# 4 — Transfer chain content
# ===========================================================================

class TestTransferChainContent:
    def setup_method(self):
        self.v = ConsumerVerifier()

    def test_actor_names_appear_in_report(self):
        entry = make_entry(from_name="Farmer Joe", to_name="Agg Corp")
        chain = make_chain([entry])
        result = self.v.verify(BATCH_ID, chain, [make_certificate()])
        assert "Farmer Joe" in result
        assert "Agg Corp"   in result

    def test_actor_locations_appear_in_report(self):
        entry = make_entry(from_location="Ado Ekiti", to_location="Akure Hub")
        chain = make_chain([entry])
        result = self.v.verify(BATCH_ID, chain, [make_certificate()])
        assert "Ado Ekiti" in result
        assert "Akure Hub" in result

    def test_weight_appears_in_report(self):
        entry = make_entry(weight_kg=250.5)
        chain = make_chain([entry])
        result = self.v.verify(BATCH_ID, chain, [make_certificate()])
        assert "250.5" in result

    def test_transfer_date_appears_in_report(self):
        dt    = datetime(2025, 3, 15, 9, 30)
        entry = make_entry(transfer_datetime=dt)
        chain = make_chain([entry])
        result = self.v.verify(BATCH_ID, chain, [make_certificate()])
        assert "2025-03-15" in result

    def test_multiple_entries_all_shown(self):
        entries = [
            make_entry(entry_id="e1", from_name="Farm A", to_name="Agg X"),
            make_entry(entry_id="e2", from_name="Agg X",  to_name="Proc Y"),
            make_entry(entry_id="e3", from_name="Proc Y", to_name="Dist Z"),
        ]
        chain  = make_chain(entries)
        result = self.v.verify(BATCH_ID, chain, [make_certificate()])
        assert "Farm A" in result
        assert "Proc Y" in result
        assert "Dist Z" in result

    def test_empty_chain_shows_no_records_message(self):
        chain  = make_chain([])
        result = self.v.verify(BATCH_ID, chain, [make_certificate()])
        assert "No transfer records" in result


# ===========================================================================
# 5 — Certificate content
# ===========================================================================

class TestCertificateContent:
    def setup_method(self):
        self.v = ConsumerVerifier()

    def test_cert_id_in_report(self):
        cert   = make_certificate(cert_id="CERT-XYZ-001")
        result = self.v.verify(BATCH_ID, make_chain(), [cert])
        assert "CERT-XYZ-001" in result

    def test_standard_code_in_report(self):
        cert   = make_certificate(standard_code="SON-2025")
        result = self.v.verify(BATCH_ID, make_chain(), [cert])
        assert "SON-2025" in result

    def test_valid_cert_shows_valid_status(self):
        cert   = make_certificate(is_valid=True)
        result = self.v.verify(BATCH_ID, make_chain(), [cert])
        assert "VALID" in result

    def test_expired_cert_shows_invalid_status(self):
        cert   = make_certificate(is_valid=False)
        result = self.v.verify(BATCH_ID, make_chain(), [cert])
        assert "EXPIRED" in result or "INVALID" in result

    def test_no_certificates_shows_message(self):
        result = self.v.verify(BATCH_ID, make_chain(), [])
        assert "No certificates" in result

    def test_multiple_certificates_all_shown(self):
        certs  = [
            make_certificate(cert_id="C-001", standard_code="NAFDAC-NG"),
            make_certificate(cert_id="C-002", standard_code="SON-NG"),
        ]
        result = self.v.verify(BATCH_ID, make_chain(), certs)
        assert "C-001" in result
        assert "C-002" in result


# ===========================================================================
# 6 — Verdict: AUTHENTIC
# ===========================================================================

class TestAuthenticVerdict:
    def setup_method(self):
        self.v = ConsumerVerifier()

    def test_authentic_when_chain_ok_and_valid_cert(self):
        result = self.v.verify(BATCH_ID, make_chain(), [make_certificate()])
        assert "AUTHENTIC" in result

    def test_authentic_with_multiple_valid_certs(self):
        certs  = [make_certificate(cert_id=f"C-{i}") for i in range(3)]
        result = self.v.verify(BATCH_ID, make_chain(), certs)
        assert "AUTHENTIC" in result


# ===========================================================================
# 7 — Verdict: SUSPICIOUS
# ===========================================================================

class TestSuspiciousVerdict:
    def setup_method(self):
        self.v = ConsumerVerifier()

    def test_suspicious_when_chain_empty(self):
        chain  = make_chain([])
        result = self.v.verify(BATCH_ID, chain, [make_certificate()])
        assert "SUSPICIOUS" in result

    def test_suspicious_when_integrity_fails(self):
        chain  = make_chain(integrity_ok=False)
        result = self.v.verify(BATCH_ID, chain, [make_certificate()])
        assert "SUSPICIOUS" in result

    def test_suspicious_when_integrity_raises(self):
        chain  = make_chain(raises=True)
        result = self.v.verify(BATCH_ID, chain, [make_certificate()])
        assert "SUSPICIOUS" in result

    def test_suspicious_when_no_certificates(self):
        result = self.v.verify(BATCH_ID, make_chain(), [])
        assert "SUSPICIOUS" in result

    def test_suspicious_when_all_certs_expired(self):
        expired = make_certificate(is_valid=False)
        result  = self.v.verify(BATCH_ID, make_chain(), [expired])
        assert "SUSPICIOUS" in result

    def test_suspicious_when_mix_but_all_invalid(self):
        certs  = [
            make_certificate(cert_id="C-1", is_valid=False),
            make_certificate(cert_id="C-2", is_valid=False),
        ]
        result = self.v.verify(BATCH_ID, make_chain(), certs)
        assert "SUSPICIOUS" in result

    def test_authentic_when_at_least_one_valid_cert(self):
        """One valid cert among expired ones → still AUTHENTIC."""
        certs  = [
            make_certificate(cert_id="C-1", is_valid=False),
            make_certificate(cert_id="C-2", is_valid=True),
        ]
        result = self.v.verify(BATCH_ID, make_chain(), certs)
        assert "AUTHENTIC" in result
