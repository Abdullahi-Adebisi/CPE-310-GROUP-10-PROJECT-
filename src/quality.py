from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import date, timedelta
from typing import List, Optional

from src.exceptions import CertificateExpiredError

VALID_GRADES = ("A", "B", "C", "FAIL")


class InspectorNotAccreditedError(Exception):
    """Raised when an inspector attempts to inspect a batch against a
    standard they are not accredited for."""

    def __init__(self, inspector_id: str, standard_code: str):
        self.inspector_id = inspector_id
        self.standard_code = standard_code
        super().__init__(
            f"Inspector {inspector_id!r} is not accredited for "
            f"standard {standard_code!r}"
        )


class QualityCertificate:
    """
    The result of a single inspection of a ProductBatch against a
    QualityStandard.

    All attributes are validated on construction and exposed as
    read-only properties; a QualityCertificate is not meant to be
    mutated once issued -- a failed re-inspection should produce a new
    certificate, not edit an old one.
    """

    def __init__(
        self,
        batch_id: str,
        standard: "QualityStandard",
        issued_by: "QualityInspector",
        grade: str,
        issue_date: Optional[date] = None,
        validity_days: int = 365,
    ):
        if not batch_id:
            raise ValueError("batch_id is required")
        if grade not in VALID_GRADES:
            raise ValueError(
                f"Invalid grade {grade!r}; must be one of {VALID_GRADES}"
            )
        if validity_days <= 0:
            raise ValueError("validity_days must be positive")

        self._cert_id = str(uuid.uuid4())
        self._batch_id = batch_id
        self._standard = standard
        self._issued_by = issued_by
        self._grade = grade
        self._issue_date = issue_date or date.today()
        self._expiry_date = self._issue_date + timedelta(days=validity_days)

    @property
    def cert_id(self) -> str:
        return self._cert_id

    @property
    def batch_id(self) -> str:
        return self._batch_id

    @property
    def standard(self) -> "QualityStandard":
        return self._standard

    @property
    def issued_by(self) -> "QualityInspector":
        return self._issued_by

    @property
    def issue_date(self) -> date:
        return self._issue_date

    @property
    def expiry_date(self) -> date:
        return self._expiry_date

    @property
    def grade(self) -> str:
        return self._grade

    @property
    def is_valid(self) -> bool:
        """
        True if the certificate has not yet expired and the inspection
        did not result in an outright FAIL.

        A FAIL'd inspection never represented a passing quality state,
        so it is treated as invalid regardless of the expiry date.
        """
        return date.today() <= self._expiry_date and self._grade != "FAIL"

    def ensure_valid(self) -> None:
        """Raise CertificateExpiredError if this certificate is expired.

        Note: only the expiry condition raises here; a FAIL grade is a
        legitimate (non-exceptional) inspection outcome and should be
        handled by checking `grade`/`is_valid`, not by catching an
        exception.
        """
        if date.today() > self._expiry_date:
            raise CertificateExpiredError(
                f"Certificate {self._cert_id} for batch {self._batch_id} "
                f"expired on {self._expiry_date.isoformat()}"
            )

    def __str__(self):
        status = "VALID" if self.is_valid else "INVALID"
        return (
            f"Certificate {self._cert_id[:8]} [{self._standard.standard_code}] "
            f"batch={self._batch_id} grade={self._grade} ({status}, "
            f"expires {self._expiry_date.isoformat()})"
        )

    def __repr__(self):
        return (
            f"QualityCertificate(cert_id={self._cert_id!r}, "
            f"batch_id={self._batch_id!r}, "
            f"standard={self._standard.standard_code!r}, "
            f"grade={self._grade!r}, expiry_date={self._expiry_date!r})"
        )


class QualityInspector:
    """A person accredited to inspect batches against one or more
    QualityStandard protocols."""

    def __init__(self, inspector_id: str, name: str, accredited_standards: List[str]):
        if not inspector_id:
            raise ValueError("inspector_id is required")
        if not name:
            raise ValueError("name is required")
        self.inspector_id = inspector_id
        self.name = name
        # Stored as standard_code strings, e.g. ["NAFDAC", "ORGANIC"].
        self.accredited_standards = list(accredited_standards)

    def can_inspect(self, standard: "QualityStandard") -> bool:
        """True if this inspector is accredited for `standard`."""
        return standard.standard_code in self.accredited_standards

    def __str__(self):
        return (
            f"Inspector {self.name} ({self.inspector_id}) -- "
            f"accredited: {', '.join(self.accredited_standards)}"
        )

    def __repr__(self):
        return (
            f"QualityInspector(inspector_id={self.inspector_id!r}, "
            f"name={self.name!r}, "
            f"accredited_standards={self.accredited_standards!r})"
        )


class QualityStandard(ABC):
    """
    Abstract base class for a certifying body's inspection protocol.

    Concrete subclasses define standard_code, certifying_body, the
    certificate validity period, and the grading thresholds used to
    convert a numeric inspection score into a letter grade.
    """

    #: Number of days a certificate issued under this standard stays valid.
    VALIDITY_DAYS = 365

    def __init__(self, standard_code: str, certifying_body: str):
        self.standard_code = standard_code
        self.certifying_body = certifying_body

    @abstractmethod
    def inspect(
        self,
        batch,
        inspector: QualityInspector,
        quality_score: Optional[float] = None,
    ) -> QualityCertificate:
        """
        Inspect `batch` and issue a QualityCertificate.

        `quality_score` (0-100) lets a caller supply a manual inspection
        result; if omitted, a deterministic default score is derived
        from the batch's weight retention (current_weight_kg /
        initial_weight_kg), which is a reasonable proxy for spoilage
        or processing loss.

        Raises InspectorNotAccreditedError if `inspector` is not
        accredited for this standard.
        """
        raise NotImplementedError

    def _default_score(self, batch) -> float:
        """Fallback inspection score derived from weight retention."""
        if batch.initial_weight_kg <= 0:
            return 0.0
        retention = batch.current_weight_kg / batch.initial_weight_kg
        return max(0.0, min(100.0, retention * 100))

    def _score_to_grade(self, score: float) -> str:
        """Default A/B/C/FAIL thresholds; subclasses may override."""
        if score >= 90:
            return "A"
        if score >= 75:
            return "B"
        if score >= 60:
            return "C"
        return "FAIL"

    def _require_accreditation(self, inspector: QualityInspector) -> None:
        if not inspector.can_inspect(self):
            raise InspectorNotAccreditedError(inspector.inspector_id, self.standard_code)

    def __str__(self):
        return f"{self.standard_code} ({self.certifying_body})"

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(standard_code={self.standard_code!r}, "
            f"certifying_body={self.certifying_body!r})"
        )


class NafdacStandard(QualityStandard):
    """
    National Agency for Food and Drug Administration and Control
    (NAFDAC) standard -- food safety and consumability inspection.
    """

    VALIDITY_DAYS = 365

    def __init__(self):
        super().__init__(
            standard_code="NAFDAC",
            certifying_body="National Agency for Food and Drug "
            "Administration and Control",
        )

    def inspect(self, batch, inspector, quality_score=None) -> QualityCertificate:
        self._require_accreditation(inspector)
        score = quality_score if quality_score is not None else self._default_score(batch)
        grade = self._score_to_grade(score)
        return QualityCertificate(
            batch_id=batch.batch_id,
            standard=self,
            issued_by=inspector,
            grade=grade,
            validity_days=self.VALIDITY_DAYS,
        )


class SONStandard(QualityStandard):
    """
    Standards Organisation of Nigeria (SON) standard -- general product
    quality and conformity inspection.
    """

    VALIDITY_DAYS = 365

    def __init__(self):
        super().__init__(
            standard_code="SON",
            certifying_body="Standards Organisation of Nigeria",
        )

    def inspect(self, batch, inspector, quality_score=None) -> QualityCertificate:
        self._require_accreditation(inspector)
        score = quality_score if quality_score is not None else self._default_score(batch)
        grade = self._score_to_grade(score)
        return QualityCertificate(
            batch_id=batch.batch_id,
            standard=self,
            issued_by=inspector,
            grade=grade,
            validity_days=self.VALIDITY_DAYS,
        )


class OrganicCertification(QualityStandard):
    """
    Organic certification -- attests the batch was produced without
    synthetic pesticides/fertilizers. Held to a stricter grading bar
    and a shorter validity window than NAFDAC/SON, reflecting how
    organic status is typically re-verified more frequently.
    """

    VALIDITY_DAYS = 180

    def __init__(self):
        super().__init__(
            standard_code="ORGANIC",
            certifying_body="Organic Agriculture Certification Council",
        )

    def _score_to_grade(self, score: float) -> str:
        # Stricter thresholds than the base standard.
        if score >= 95:
            return "A"
        if score >= 85:
            return "B"
        if score >= 70:
            return "C"
        return "FAIL"

    def inspect(self, batch, inspector, quality_score=None) -> QualityCertificate:
        self._require_accreditation(inspector)
        score = quality_score if quality_score is not None else self._default_score(batch)
        grade = self._score_to_grade(score)
        return QualityCertificate(
            batch_id=batch.batch_id,
            standard=self,
            issued_by=inspector,
            grade=grade,
            validity_days=self.VALIDITY_DAYS,
        )
