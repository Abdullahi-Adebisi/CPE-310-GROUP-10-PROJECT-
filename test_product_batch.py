"""
consumer_verifier.py
--------------------
CPE 310 — OOP with Python | Group 10
Agricultural Supply Chain Tracking and Product Authenticity System

Module: ConsumerVerifier
Responsibility: Generate a formatted provenance report for a product batch,
showing the full transfer chain, all quality certificates with validity
status, and a final AUTHENTIC or SUSPICIOUS verdict.

Author: Group 10 — Phase 6
Python: 3.10+
"""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

# ---------------------------------------------------------------------------
# Type-only imports (avoids circular imports at runtime)
# ---------------------------------------------------------------------------
if TYPE_CHECKING:
    from src.supply_chain import SupplyChain          # ordered LedgerEntry list
    from src.quality_certificate import QualityCertificate


# ---------------------------------------------------------------------------
# ConsumerVerifier
# ---------------------------------------------------------------------------

class ConsumerVerifier:
    """Generate a tamper-evident provenance report for a single product batch.

    The verifier is stateless: every call to ``verify()`` produces a fresh
    report based solely on the arguments supplied.  No data is stored on the
    instance, which makes it safe to reuse across multiple batches.

    Usage
    -----
    >>> verifier = ConsumerVerifier()
    >>> report   = verifier.verify(batch_id, chain, certificates)
    >>> print(report)
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def verify(
        self,
        batch_id: str,
        chain: "SupplyChain",
        certificates: list["QualityCertificate"],
    ) -> str:
        """Return a fully-formatted provenance report as a plain string.

        Parameters
        ----------
        batch_id:
            The NG-YYYY-XXXXXXXX identifier of the batch being verified.
        chain:
            A ``SupplyChain`` instance (iterable of ``LedgerEntry`` objects)
            for *this* batch.
        certificates:
            A list of ``QualityCertificate`` objects issued for this batch.

        Returns
        -------
        str
            Multi-line provenance report ending with AUTHENTIC or SUSPICIOUS.

        Raises
        ------
        ValueError
            If *batch_id* is an empty string.
        TypeError
            If *chain* or *certificates* are not the expected types.
        """
        if not batch_id or not isinstance(batch_id, str):
            raise ValueError("batch_id must be a non-empty string.")
        if chain is None:
            raise TypeError("chain must be a SupplyChain instance, not None.")
        if not isinstance(certificates, list):
            raise TypeError("certificates must be a list of QualityCertificate objects.")

        lines: list[str] = []

        lines += self._build_header(batch_id)
        lines += self._build_chain_section(chain)
        lines += self._build_certificate_section(certificates)

        verdict = self._determine_verdict(chain, certificates)
        lines += self._build_verdict_section(verdict)

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Private helpers — header
    # ------------------------------------------------------------------

    def _build_header(self, batch_id: str) -> list[str]:
        """Return the report header lines."""
        width = 60
        now   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return [
            "=" * width,
            "  AGRICULTURAL SUPPLY CHAIN — PROVENANCE REPORT",
            "=" * width,
            f"  Batch ID   : {batch_id}",
            f"  Report Date: {now}",
            "=" * width,
        ]

    # ------------------------------------------------------------------
    # Private helpers — transfer chain
    # ------------------------------------------------------------------

    def _build_chain_section(self, chain: "SupplyChain") -> list[str]:
        """Return formatted lines for the full transfer chain."""
        lines = [
            "",
            "TRANSFER CHAIN",
            "-" * 60,
        ]

        entries = list(chain)          # SupplyChain.__iter__

        if not entries:
            lines.append("  [No transfer records found]")
            return lines

        for idx, entry in enumerate(entries, start=1):
            lines += self._format_entry(idx, entry)

        lines.append(f"\n  Total transfers recorded: {len(entries)}")
        return lines

    def _format_entry(self, idx: int, entry) -> list[str]:
        """Format a single LedgerEntry into report lines.

        Works with any object that exposes the attributes defined in the
        project spec for ``LedgerEntry``.
        """
        # Safely retrieve each attribute with a sensible fallback so that
        # partially-constructed stubs do not crash the verifier.
        from_actor  = getattr(entry, "from_actor",        None)
        to_actor    = getattr(entry, "to_actor",          None)
        weight_kg   = getattr(entry, "weight_kg",         "N/A")
        transfer_dt = getattr(entry, "transfer_datetime", None)
        entry_id    = getattr(entry, "entry_id",          "N/A")
        curr_hash   = getattr(entry, "current_hash",      "N/A")

        from_name     = getattr(from_actor, "name",     "Unknown") if from_actor else "Origin"
        from_location = getattr(from_actor, "location", "Unknown") if from_actor else "N/A"
        to_name       = getattr(to_actor,   "name",     "Unknown") if to_actor   else "Unknown"
        to_location   = getattr(to_actor,   "location", "Unknown") if to_actor   else "N/A"

        dt_str = (
            transfer_dt.strftime("%Y-%m-%d %H:%M")
            if isinstance(transfer_dt, datetime)
            else str(transfer_dt) if transfer_dt else "N/A"
        )

        hash_preview = str(curr_hash)[:16] + "..." if curr_hash and curr_hash != "N/A" else "N/A"

        return [
            f"\n  Step {idx}",
            f"    Entry ID  : {entry_id}",
            f"    From      : {from_name} ({from_location})",
            f"    To        : {to_name} ({to_location})",
            f"    Weight    : {weight_kg} kg",
            f"    Date/Time : {dt_str}",
            f"    Hash      : {hash_preview}",
        ]

    # ------------------------------------------------------------------
    # Private helpers — certificates
    # ------------------------------------------------------------------

    def _build_certificate_section(
        self, certificates: list["QualityCertificate"]
    ) -> list[str]:
        """Return formatted lines for all quality certificates."""
        lines = [
            "",
            "QUALITY CERTIFICATES",
            "-" * 60,
        ]

        if not certificates:
            lines.append("  [No certificates issued for this batch]")
            return lines

        for cert in certificates:
            lines += self._format_certificate(cert)

        return lines

    def _format_certificate(self, cert) -> list[str]:
        """Format a single QualityCertificate."""
        cert_id     = getattr(cert, "cert_id",     "N/A")
        standard    = getattr(cert, "standard",    None)
        issued_by   = getattr(cert, "issued_by",   "N/A")
        issue_date  = getattr(cert, "issue_date",  None)
        expiry_date = getattr(cert, "expiry_date", None)
        grade       = getattr(cert, "grade",       "N/A")
        is_valid    = getattr(cert, "is_valid",    None)

        std_name = (
            getattr(standard, "standard_code", str(standard))
            if standard else "N/A"
        )

        issue_str  = issue_date.isoformat()  if isinstance(issue_date,  date) else str(issue_date)
        expiry_str = expiry_date.isoformat() if isinstance(expiry_date, date) else str(expiry_date)

        # Determine validity display
        if is_valid is True:
            validity_display = "✔ VALID"
        elif is_valid is False:
            validity_display = "✘ EXPIRED / INVALID"
        else:
            # Fallback: compute from expiry_date if is_valid property missing
            if isinstance(expiry_date, date):
                validity_display = "✔ VALID" if expiry_date >= date.today() else "✘ EXPIRED"
            else:
                validity_display = "UNKNOWN"

        return [
            f"\n  Certificate : {cert_id}",
            f"    Standard  : {std_name}",
            f"    Issued By : {issued_by}",
            f"    Issue Date: {issue_str}",
            f"    Expiry    : {expiry_str}",
            f"    Grade     : {grade}",
            f"    Status    : {validity_display}",
        ]

    # ------------------------------------------------------------------
    # Private helpers — verdict
    # ------------------------------------------------------------------

    def _determine_verdict(
        self,
        chain: "SupplyChain",
        certificates: list["QualityCertificate"],
    ) -> str:
        """Return 'AUTHENTIC' or 'SUSPICIOUS'.

        A batch is SUSPICIOUS if ANY of the following are true:
        1. The chain has no entries.
        2. ``chain.verify_integrity()`` raises or returns False.
        3. There are no certificates at all.
        4. Every certificate is expired / invalid.
        """
        # --- Rule 1: empty chain -------------------------------------------
        entries = list(chain)
        if not entries:
            return "SUSPICIOUS"

        # --- Rule 2: tamper check ------------------------------------------
        try:
            integrity_ok = chain.verify_integrity()   # raises LedgerTamperingError
            if not integrity_ok:
                return "SUSPICIOUS"
        except Exception:
            # Any exception from verify_integrity() means tampering detected
            return "SUSPICIOUS"

        # --- Rule 3: no certificates ---------------------------------------
        if not certificates:
            return "SUSPICIOUS"

        # --- Rule 4: all certificates invalid ------------------------------
        valid_certs = [
            c for c in certificates
            if self._certificate_is_valid(c)
        ]
        if not valid_certs:
            return "SUSPICIOUS"

        return "AUTHENTIC"

    def _certificate_is_valid(self, cert) -> bool:
        """Return True if the certificate is currently valid."""
        # Prefer the model's own is_valid property
        is_valid = getattr(cert, "is_valid", None)
        if isinstance(is_valid, bool):
            return is_valid

        # Fallback: check expiry_date manually
        expiry_date = getattr(cert, "expiry_date", None)
        if isinstance(expiry_date, date):
            return expiry_date >= date.today()

        return False

    # ------------------------------------------------------------------
    # Private helpers — verdict section
    # ------------------------------------------------------------------

    def _build_verdict_section(self, verdict: str) -> list[str]:
        """Return the final verdict block."""
        width = 60
        return [
            "",
            "=" * width,
            f"  FINAL VERDICT: {verdict}",
            "=" * width,
            "",
        ]

    # ------------------------------------------------------------------
    # Dunder methods
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return "ConsumerVerifier()"

    def __str__(self) -> str:
        return "ConsumerVerifier — Agricultural Supply Chain Authenticity Checker"
