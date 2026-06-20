from datetime import date, timedelta

import pytest

from src.exceptions import CertificateExpiredError
from src.quality import (
    InspectorNotAccreditedError,
    NafdacStandard,
    OrganicCertification,
    QualityCertificate,
    QualityInspector,
    QualityStandard,
    SONStandard,
)


class _FakeBatch:
    """Minimal stand-in for ProductBatch -- only the attributes that
    quality.py actually reads, so these tests don't depend on Phase 1's
    real implementation being finished."""

    def __init__(self, batch_id="NG-2026-AB12CD34", initial_weight_kg=100.0,
                 current_weight_kg=100.0):
        self.batch_id = batch_id
        self.initial_weight_kg = initial_weight_kg
        self.current_weight_kg = current_weight_kg


@pytest.fixture
def batch():
    return _FakeBatch()


@pytest.fixture
def nafdac_inspector():
    return QualityInspector("INSP-001", "Amaka Eze", ["NAFDAC"])


@pytest.fixture
def all_round_inspector():
    return QualityInspector("INSP-002", "Tunde Bello", ["NAFDAC", "SON", "ORGANIC"])


@pytest.fixture
def unaccredited_inspector():
    return QualityInspector("INSP-003", "No Credentials", [])


class TestAbstractClass:
    def test_cannot_instantiate_quality_standard(self):
        with pytest.raises(TypeError):
            QualityStandard("X", "Some Body")


class TestNafdacStandard:
    def test_inspect_returns_certificate(self, batch, nafdac_inspector):
        standard = NafdacStandard()
        cert = standard.inspect(batch, nafdac_inspector, quality_score=92)

        assert isinstance(cert, QualityCertificate)
        assert cert.standard.standard_code == "NAFDAC"
        assert cert.grade == "A"
        assert cert.batch_id == batch.batch_id
        assert cert.is_valid is True

    def test_inspect_by_unaccredited_inspector_raises(self, batch, unaccredited_inspector):
        standard = NafdacStandard()
        with pytest.raises(InspectorNotAccreditedError):
            standard.inspect(batch, unaccredited_inspector, quality_score=90)

    def test_grade_thresholds(self, batch, nafdac_inspector):
        standard = NafdacStandard()
        assert standard.inspect(batch, nafdac_inspector, quality_score=95).grade == "A"
        assert standard.inspect(batch, nafdac_inspector, quality_score=80).grade == "B"
        assert standard.inspect(batch, nafdac_inspector, quality_score=65).grade == "C"
        assert standard.inspect(batch, nafdac_inspector, quality_score=10).grade == "FAIL"


class TestSONStandard:
    def test_inspect_returns_certificate(self, batch, all_round_inspector):
        standard = SONStandard()
        cert = standard.inspect(batch, all_round_inspector, quality_score=78)

        assert cert.standard.standard_code == "SON"
        assert cert.grade == "B"

    def test_default_score_from_weight_retention(self, all_round_inspector):
        standard = SONStandard()
        # No spoilage at all -> 100% retention -> grade A.
        full_batch = _FakeBatch(initial_weight_kg=100.0, current_weight_kg=100.0)
        cert = standard.inspect(full_batch, all_round_inspector)
        assert cert.grade == "A"

        # Heavy loss -> low retention -> FAIL.
        spoiled_batch = _FakeBatch(initial_weight_kg=100.0, current_weight_kg=20.0)
        cert2 = standard.inspect(spoiled_batch, all_round_inspector)
        assert cert2.grade == "FAIL"


class TestOrganicCertification:
    def test_stricter_thresholds_than_base(self, batch, all_round_inspector):
        standard = OrganicCertification()
        # 80 would be a 'B' under NAFDAC/SON but fails Organic's bar.
        cert = standard.inspect(batch, all_round_inspector, quality_score=80)
        assert cert.grade == "C"

        cert_top = standard.inspect(batch, all_round_inspector, quality_score=96)
        assert cert_top.grade == "A"

    def test_shorter_validity_window(self, batch, all_round_inspector):
        standard = OrganicCertification()
        cert = standard.inspect(batch, all_round_inspector, quality_score=96)
        expected_expiry = date.today() + timedelta(days=180)
        assert cert.expiry_date == expected_expiry


class TestQualityCertificate:
    def test_invalid_grade_raises(self, nafdac_inspector):
        standard = NafdacStandard()
        with pytest.raises(ValueError):
            QualityCertificate(
                batch_id="NG-2026-AB12CD34",
                standard=standard,
                issued_by=nafdac_inspector,
                grade="X",
            )

    def test_is_valid_false_when_expired(self, batch, nafdac_inspector):
        standard = NafdacStandard()
        past_issue = date.today() - timedelta(days=400)
        cert = QualityCertificate(
            batch_id=batch.batch_id,
            standard=standard,
            issued_by=nafdac_inspector,
            grade="A",
            issue_date=past_issue,
            validity_days=365,
        )
        assert cert.is_valid is False

    def test_is_valid_false_when_grade_is_fail(self, batch, nafdac_inspector):
        standard = NafdacStandard()
        cert = QualityCertificate(
            batch_id=batch.batch_id,
            standard=standard,
            issued_by=nafdac_inspector,
            grade="FAIL",
        )
        assert cert.is_valid is False

    def test_ensure_valid_raises_certificate_expired_error(self, batch, nafdac_inspector):
        standard = NafdacStandard()
        past_issue = date.today() - timedelta(days=400)
        cert = QualityCertificate(
            batch_id=batch.batch_id,
            standard=standard,
            issued_by=nafdac_inspector,
            grade="A",
            issue_date=past_issue,
            validity_days=365,
        )
        with pytest.raises(CertificateExpiredError):
            cert.ensure_valid()

    def test_ensure_valid_does_not_raise_for_fail_grade(self, batch, nafdac_inspector):
        # FAIL is invalid but not "expired" -- ensure_valid() should not
        # raise CertificateExpiredError for a fresh FAIL certificate.
        standard = NafdacStandard()
        cert = QualityCertificate(
            batch_id=batch.batch_id,
            standard=standard,
            issued_by=nafdac_inspector,
            grade="FAIL",
        )
        cert.ensure_valid()  # should not raise


class TestQualityInspector:
    def test_can_inspect_true_when_accredited(self, all_round_inspector):
        assert all_round_inspector.can_inspect(NafdacStandard()) is True
        assert all_round_inspector.can_inspect(SONStandard()) is True
        assert all_round_inspector.can_inspect(OrganicCertification()) is True

    def test_can_inspect_false_when_not_accredited(self, nafdac_inspector):
        assert nafdac_inspector.can_inspect(SONStandard()) is False
        assert nafdac_inspector.can_inspect(OrganicCertification()) is False

    def test_str_and_repr(self, nafdac_inspector):
        assert nafdac_inspector.inspector_id in str(nafdac_inspector)
        assert "QualityInspector" in repr(nafdac_inspector)
