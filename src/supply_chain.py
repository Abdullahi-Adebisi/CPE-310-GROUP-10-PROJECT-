

from __future__ import annotations

import hashlib
from typing import Iterator

from ledger_entry import LedgerEntry
from exceptions import LedgerTamperingError, BatchNotFoundError


class SupplyChain:
    """An ordered, tamper-evident chain of custody for one product batch.

    Each node in the chain is an immutable :class:`LedgerEntry`.  The chain
    preserves insertion order and exposes a ``verify_integrity()`` method that
    re-derives every SHA-256 hash from scratch and raises
    :class:`LedgerTamperingError` the moment a discrepancy is found.

    Two chains that tracked the **same** batch in different geographic regions
    can be merged with the ``+`` operator; the resulting chain is sorted by
    transfer timestamp.

    Attributes
    ----------
    batch_id : str
        The ``NG-YYYY-XXXXXXXX`` identifier shared by every entry in the chain.

    Examples
    --------
    >>> chain = SupplyChain(batch_id="NG-2024-00000001")
    >>> chain.add_entry(entry)          # LedgerEntry object
    >>> chain.verify_integrity()        # True if untampered
    >>> "NG-2024-00000001" in chain     # True
    >>> len(chain)                      # number of transfers
    """

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def __init__(self, batch_id: str) -> None:
        """Initialise an empty supply chain for *batch_id*.

        Parameters
        ----------
        batch_id : str
            Must follow the ``NG-YYYY-XXXXXXXX`` format already validated by
            :class:`~product_batch.ProductBatch`.
        """
        self._batch_id: str = batch_id
        self._entries: list[LedgerEntry] = []

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    @property
    def batch_id(self) -> str:
        """The batch identifier tracked by this chain (read-only)."""
        return self._batch_id

    def add_entry(self, entry: LedgerEntry) -> None:
        """Append *entry* to the chain.

        Parameters
        ----------
        entry : LedgerEntry
            Must belong to the same ``batch_id`` as this chain.

        Raises
        ------
        TypeError
            If *entry* is not a :class:`LedgerEntry` instance.
        ValueError
            If *entry* belongs to a different batch.
        """
        if not isinstance(entry, LedgerEntry):
            raise TypeError(
                f"Expected a LedgerEntry, got {type(entry).__name__!r}."
            )
        if entry.batch_id != self._batch_id:
            raise ValueError(
                f"Entry batch_id {entry.batch_id!r} does not match "
                f"chain batch_id {self._batch_id!r}."
            )
        self._entries.append(entry)

    def verify_integrity(self) -> bool:
        """Re-compute every hash and confirm the chain is untampered.

        The algorithm walks the sorted entry list.  For each entry it
        re-derives the SHA-256 digest from the entry's own fields and
        compares it against the stored ``current_hash``.  If they differ,
        the chain has been tampered with.

        Returns
        -------
        bool
            ``True`` when every hash is valid.

        Raises
        ------
        LedgerTamperingError
            On the **first** entry whose stored hash does not match the
            freshly computed hash.  The exception carries the offending
            ``entry_id``, the expected hash (stored), and the computed hash.
        """
        for entry in sorted(self._entries):
            computed = self._recompute_hash(entry)
            if computed != entry.current_hash:
                raise LedgerTamperingError(
                    entry_id=str(entry.entry_id),
                    expected_hash=entry.current_hash,
                    computed_hash=computed,
                )
        return True

    # ------------------------------------------------------------------
    # Dunder / special methods
    # ------------------------------------------------------------------

    def __contains__(self, item: object) -> bool:
        """Support ``batch_id in chain`` and ``entry in chain`` lookups.

        Parameters
        ----------
        item : str | LedgerEntry
            * ``str`` — treated as a *batch_id*; returns ``True`` when the
              chain's own ``batch_id`` matches.
            * :class:`LedgerEntry` — returns ``True`` when the identical
              entry object (by hash equality) is present.

        Returns
        -------
        bool
        """
        if isinstance(item, str):
            return item == self._batch_id
        if isinstance(item, LedgerEntry):
            return any(e == item for e in self._entries)
        return False

    def __len__(self) -> int:
        """Return the number of custody transfers recorded so far."""
        return len(self._entries)

    def __iter__(self) -> Iterator[LedgerEntry]:
        """Iterate over entries in chronological (timestamp) order."""
        return iter(sorted(self._entries))

    def __add__(self, other: SupplyChain) -> SupplyChain:
        """Merge two chains that tracked the same batch in different regions.

        The returned chain contains all entries from both operands, sorted by
        transfer timestamp.  Neither operand is mutated.

        Parameters
        ----------
        other : SupplyChain
            Must have the same ``batch_id`` as *self*.

        Returns
        -------
        SupplyChain
            A new :class:`SupplyChain` with the combined, deduplicated entries.

        Raises
        ------
        TypeError
            If *other* is not a :class:`SupplyChain`.
        ValueError
            If *other* tracks a different ``batch_id``.

        Examples
        --------
        >>> merged = chain_region_a + chain_region_b
        """
        if not isinstance(other, SupplyChain):
            return NotImplemented
        if self._batch_id != other._batch_id:
            raise ValueError(
                f"Cannot merge chains with different batch IDs: "
                f"{self._batch_id!r} vs {other._batch_id!r}."
            )
        merged = SupplyChain(batch_id=self._batch_id)
        # Deduplicate by current_hash while preserving order
        seen_hashes: set[str] = set()
        for entry in sorted(self._entries + other._entries):
            if entry.current_hash not in seen_hashes:
                merged._entries.append(entry)
                seen_hashes.add(entry.current_hash)
        return merged

    def __repr__(self) -> str:
        return (
            f"SupplyChain(batch_id={self._batch_id!r}, "
            f"entries={len(self._entries)})"
        )

    def __str__(self) -> str:
        lines = [f"Supply Chain — Batch {self._batch_id}"]
        lines.append(f"  Total transfers : {len(self._entries)}")
        if self._entries:
            for idx, entry in enumerate(sorted(self._entries), start=1):
                lines.append(
                    f"  [{idx}] {entry.from_actor} → {entry.to_actor} | "
                    f"{entry.weight_kg} kg | "
                    f"{entry.transfer_datetime.strftime('%Y-%m-%d %H:%M')} | "
                    f"hash …{entry.current_hash[-8:]}"
                )
        else:
            lines.append("  (no transfers recorded yet)")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _recompute_hash(entry: LedgerEntry) -> str:
        """Re-derive the SHA-256 hash for *entry* from its raw fields.

        This mirrors the ``_compute_hash()`` logic in :class:`LedgerEntry`
        exactly — any divergence means the entry's data was altered after
        the original hash was generated.

        The hash input is the pipe-delimited concatenation of::

            entry_id | batch_id | from_actor | to_actor
            | weight_kg | transfer_datetime(ISO) | previous_hash

        Parameters
        ----------
        entry : LedgerEntry

        Returns
        -------
        str
            64-character lowercase hex digest.
        """
        raw = (
            f"{entry.entry_id}"
            f"|{entry.batch_id}"
            f"|{entry.from_actor}"
            f"|{entry.to_actor}"
            f"|{entry.weight_kg}"
            f"|{entry.transfer_datetime.isoformat()}"
            f"|{entry.previous_hash}"
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
