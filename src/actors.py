from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from src.exceptions import InvalidCustodyTransferError
from src.ledger_entry import LedgerEntry
from src.product_batch import ProductBatch

GENESIS_HASH = "0" * 64


class SupplyChainActor(ABC):
    """
    Abstract base class for every participant in the supply chain.

    Subclasses must implement transfer_custody(), which hands a quantity
    of a batch to another actor and returns the resulting LedgerEntry.
    """

    def __init__(self, actor_id: str, actor_type: str, location: str):
        if not actor_id:
            raise ValueError("actor_id is required")
        if not location:
            raise ValueError("location is required")
        self.actor_id = actor_id
        self.actor_type = actor_type
        self.location = location

    @abstractmethod
    def transfer_custody(
        self,
        batch: ProductBatch,
        recipient: "SupplyChainActor",
        weight_kg: float,
    ) -> LedgerEntry:
        """Transfer weight_kg of batch from this actor to recipient.

        Must validate custody and weight, update the batch in place,
        and return the new LedgerEntry for the transfer.
        """
        raise NotImplementedError

    def _validate_transfer(self, batch: ProductBatch, weight_kg: float) -> None:
        """Shared guard used by every concrete actor before transferring."""
        if batch.current_custodian != self.actor_id:
            raise InvalidCustodyTransferError(
                f"{self.actor_id} cannot transfer batch {batch.batch_id}: "
                f"current custodian is {batch.current_custodian!r}, "
                f"not {self.actor_id!r}"
            )
        if weight_kg <= 0:
            raise InvalidCustodyTransferError(
                f"Transfer weight must be positive, got {weight_kg}"
            )
        if weight_kg > batch.current_weight_kg:
            raise InvalidCustodyTransferError(
                f"Cannot transfer {weight_kg}kg: batch {batch.batch_id} "
                f"only has {batch.current_weight_kg}kg remaining"
            )

    def _execute_transfer(
        self,
        batch: ProductBatch,
        recipient: "SupplyChainActor",
        weight_kg: float,
        previous_hash: str = GENESIS_HASH,
        transfer_datetime: Optional[datetime] = None,
    ) -> LedgerEntry:
        """Validate, build the LedgerEntry, and update the batch."""
        self._validate_transfer(batch, weight_kg)

        entry = LedgerEntry(
            batch_id=batch.batch_id,
            from_actor=self.actor_id,
            to_actor=recipient.actor_id,
            weight_kg=weight_kg,
            transfer_datetime=transfer_datetime or datetime.now(),
            previous_hash=previous_hash,
        )

        # Custody (and the transferred weight) now belongs to the recipient.
        batch.current_custodian = recipient.actor_id
        return entry

    def __str__(self):
        return f"{self.actor_type} {self.actor_id} ({self.location})"

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(actor_id={self.actor_id!r}, "
            f"location={self.location!r})"
        )


class FarmProducer(SupplyChainActor):
    """The originating actor: harvests and first releases a batch."""

    def __init__(self, actor_id: str, location: str):
        super().__init__(actor_id, "Farm Producer", location)

    def transfer_custody(self, batch, recipient, weight_kg) -> LedgerEntry:
        return self._execute_transfer(batch, recipient, weight_kg)


class Aggregator(SupplyChainActor):
    """Collects batches from one or more farms and consolidates them."""

    def __init__(self, actor_id: str, location: str):
        super().__init__(actor_id, "Aggregator", location)

    def transfer_custody(self, batch, recipient, weight_kg) -> LedgerEntry:
        return self._execute_transfer(batch, recipient, weight_kg)


class Processor(SupplyChainActor):
    """Transforms raw batches and may split one batch into up to 3
    sub-batches (e.g. raw tomatoes -> tomato paste + juice + puree)."""

    MAX_SPLITS = 3

    def __init__(self, actor_id: str, location: str):
        super().__init__(actor_id, "Processor", location)

    def transfer_custody(self, batch, recipient, weight_kg) -> LedgerEntry:
        return self._execute_transfer(batch, recipient, weight_kg)

    def split_batch(
        self, batch: ProductBatch, sub_batch_specs: List[dict]
    ) -> List[ProductBatch]:
        """
        Split `batch` into up to MAX_SPLITS new ProductBatch objects.

        sub_batch_specs: list of dicts, each with keys 'batch_id',
        'product_name', 'weight_kg' (and optionally 'category').
        The sum of weight_kg across specs must not exceed the batch's
        current_weight_kg. This processor becomes the custodian of each
        resulting sub-batch.
        """
        if batch.current_custodian != self.actor_id:
            raise InvalidCustodyTransferError(
                f"{self.actor_id} cannot split batch {batch.batch_id}: "
                f"not the current custodian"
            )
        if not (1 <= len(sub_batch_specs) <= self.MAX_SPLITS):
            raise ValueError(
                f"A batch can only be split into 1-{self.MAX_SPLITS} "
                f"sub-batches, got {len(sub_batch_specs)}"
            )

        total_requested = sum(spec["weight_kg"] for spec in sub_batch_specs)
        if total_requested > batch.current_weight_kg:
            raise ValueError(
                f"Cannot split {total_requested}kg from a batch that only "
                f"has {batch.current_weight_kg}kg"
            )

        sub_batches = []
        for spec in sub_batch_specs:
            sub_batches.append(
                ProductBatch(
                    batch_id=spec["batch_id"],
                    product_name=spec["product_name"],
                    category=spec.get("category", batch.category),
                    origin_farm=batch.origin_farm,
                    harvest_date=batch.harvest_date,
                    initial_weight_kg=spec["weight_kg"],
                    current_custodian=self.actor_id,
                )
            )

        batch.current_weight_kg = batch.current_weight_kg - total_requested
        return sub_batches


class Distributor(SupplyChainActor):
    """Moves batches in bulk from processors/aggregators toward retail."""

    def __init__(self, actor_id: str, location: str):
        super().__init__(actor_id, "Distributor", location)

    def transfer_custody(self, batch, recipient, weight_kg) -> LedgerEntry:
        return self._execute_transfer(batch, recipient, weight_kg)


class Retailer(SupplyChainActor):
    """The final actor before the consumer; typically does not transfer
    custody onward, but can (e.g. between branches)."""

    def __init__(self, actor_id: str, location: str):
        super().__init__(actor_id, "Retailer", location)

    def transfer_custody(self, batch, recipient, weight_kg) -> LedgerEntry:
        return self._execute_transfer(batch, recipient, weight_kg)
