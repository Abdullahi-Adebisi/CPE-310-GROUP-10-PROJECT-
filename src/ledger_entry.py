"""
LedgerEntry class for the Agricultural Supply Chain
Tracking and Product Authenticity System.
CPE 310 - OOP with Python | Project 10
"""

import hashlib
import uuid
from datetime import datetime
from functools import total_ordering


@total_ordering
class LedgerEntry:
    """
   
    """

    def __init__(self,
                 batch_id: str,
                 from_actor: str,
                 to_actor: str,
                 weight_kg: float,
                 previous_hash: str = '0' * 64):
        """
        Initialise a new LedgerEntry.

        Args:
            batch_id: The ID of the product batch
            from_actor: actor_id of the sender
            to_actor: actor_id of the recipient
            weight_kg: Weight transferred in kg
            previous_hash: Hash of the previous
                          entry. Use '0'*64 for
                          the first entry.
        """
        self.__entry_id = str(uuid.uuid4())
        self.__batch_id = batch_id
        self.__from_actor = from_actor
        self.__to_actor = to_actor
        self.__weight_kg = float(weight_kg)
        self.__transfer_datetime = datetime.now()
        self.__previous_hash = previous_hash
        self.__hash_value = self.__compute_hash()

    # ── Read-only properties ──────────────────────────
    @property
    def entry_id(self) -> str:
        """Return the unique entry ID (UUID)."""
        return self.__entry_id

    @property
    def batch_id(self) -> str:
        """Return the batch ID."""
        return self.__batch_id

    @property
    def from_actor(self) -> str:
        """Return the sender actor ID."""
        return self.__from_actor

    @property
    def to_actor(self) -> str:
        """Return the recipient actor ID."""
        return self.__to_actor

    @property
    def weight_kg(self) -> float:
        """Return the weight transferred in kg."""
        return self.__weight_kg

    @property
    def transfer_datetime(self) -> datetime:
        """Return the datetime of the transfer."""
        return self.__transfer_datetime

    @property
    def previous_hash(self) -> str:
        """Return the hash of the previous entry."""
        return self.__previous_hash

    @property
    def current_hash(self) -> str:
        """Return this entry's SHA-256 hash."""
        return self.__hash_value

    # ── Hash computation ──────────────────────────────
    def __compute_hash(self) -> str:
        """
        

        Returns:
            str: 64-character hex digest
        """
        payload = ''.join([
            self.__entry_id,
            self.__batch_id,
            self.__from_actor,
            self.__to_actor,
            str(self.__transfer_datetime),
            str(self.__weight_kg),
            self.__previous_hash,
        ])
        return hashlib.sha256(
            payload.encode()
        ).hexdigest()

    def recompute_hash(self) -> str:
        """
        

        Returns:
            str: 64-character hex digest
        """
        payload = ''.join([
            self.__entry_id,
            self.__batch_id,
            self.__from_actor,
            self.__to_actor,
            str(self.__transfer_datetime),
            str(self.__weight_kg),
            self.__previous_hash,
        ])
        return hashlib.sha256(
            payload.encode()
        ).hexdigest()

    # ── Dunder methods ────────────────────────────────
    def __eq__(self, other) -> bool:
        """
        Two entries are equal if their hashes match.
        """
        if not isinstance(other, LedgerEntry):
            return NotImplemented
        return self.__hash_value == other.current_hash

    def __lt__(self, other) -> bool:
        """
        Order entries by transfer datetime.
        """
        if not isinstance(other, LedgerEntry):
            return NotImplemented
        return (
            self.__transfer_datetime
            < other.transfer_datetime
        )

    def __hash__(self) -> int:
        """
        Hash by current_hash string so entries
        can be stored in sets and dicts.
        """
        return hash(self.__hash_value)

    def __str__(self) -> str:
        return (
            f'LedgerEntry[\n'
            f'  Entry ID  : {self.__entry_id}\n'
            f'  Batch ID  : {self.__batch_id}\n'
            f'  From      : {self.__from_actor}\n'
            f'  To        : {self.__to_actor}\n'
            f'  Weight    : {self.__weight_kg}kg\n'
            f'  DateTime  : {self.__transfer_datetime}\n'
            f'  Prev Hash : {self.__previous_hash[:16]}...\n'
            f'  Curr Hash : {self.__hash_value[:16]}...\n'
            f']'
        )

    def __repr__(self) -> str:
        return (
            f'LedgerEntry('
            f'entry_id={self.__entry_id!r}, '
            f'batch_id={self.__batch_id!r}, '
            f'from_actor={self.__from_actor!r}, '
            f'to_actor={self.__to_actor!r}, '
            f'weight_kg={self.__weight_kg!r}, '
            f'current_hash={self.__hash_value[:16]!r}'
            f'...)'
                )
