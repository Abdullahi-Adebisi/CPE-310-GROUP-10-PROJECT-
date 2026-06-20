
import hashlib
import uuid
from datetime import datetime, timezone, timedelta

import pytest

# ---------------------------------------------------------------------------
# Adjust sys.path so tests can import src modules when run from project root.
# ---------------------------------------------------------------------------
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from supply_chain import SupplyChain
from ledger_entry import LedgerEntry
from exceptions import LedgerTamperingError


# ===========================================================================
# Helpers / fixtures
# ===========================================================================

BATCH_A = "NG-2024-00000001"
BATCH_B = "NG-2024-00000002"

BASE_TIME = datetime(2024, 6, 1, 8, 0, 0, tzinfo=timezone.utc)


def _make_entry(
    batch_id: str = BATCH_A,
    from_actor: str = "FarmProducer-001",
    to_actor: str = "Aggregator-001",
    weight_kg: float = 100.0,
    offset_hours: int = 0,
    previous_hash: str = "0" * 64,
) -> LedgerEntry:
    """Create a real LedgerEntry whose hash is legitimately computed."""
    return LedgerEntry(
        batch_id=batch_id,
        from_actor=from_actor,
        to_actor=to_actor,
        weight_kg=weight_kg,
        transfer_datetime=BASE_TIME + timedelta(hours=offset_hours),
        previous_hash=previous_hash,
    )


def _three_entry_chain() -> tuple[SupplyChain, list[LedgerEntry]]:
    """Return a chain with three legitimately linked entries."""
    e1 = _make_entry(offset_hours=0)
    e2 = _make_entry(
        from_actor="Aggregator-001",
        to_actor="Processor-001",
        weight_kg=95.0,
        offset_hours=24,
        previous_hash=e1.current_hash,
    )
    e3 = _make_entry(
        from_actor="Processor-001",
        to_actor="Distributor-001",
        weight_kg=90.0,
        offset_hours=48,
        previous_hash=e2.current_hash,
    )
    chain = SupplyChain(batch_id=BATCH_A)
    for e in (e1, e2, e3):
        chain.add_entry(e)
    return chain, [e1, e2, e3]


# ===========================================================================
# 1. Construction
# ===========================================================================

class TestSupplyChainConstruction:
    def test_empty_chain_has_zero_length(self):
        chain = SupplyChain(batch_id=BATCH_A)
        assert len(chain) == 0

    def test_batch_id_stored_correctly(self):
        chain = SupplyChain(batch_id=BATCH_A)
        assert chain.batch_id == BATCH_A

    def test_repr_contains_batch_id_and_count(self):
        chain = SupplyChain(batch_id=BATCH_A)
        r = repr(chain)
        assert BATCH_A in r
        assert "0" in r  # entry count

    def test_str_no_entries(self):
        chain = SupplyChain(batch_id=BATCH_A)
        s = str(chain)
        assert BATCH_A in s
        assert "no transfers" in s.lower()


# ===========================================================================
# 2. add_entry
# ===========================================================================

class TestAddEntry:
    def test_add_single_entry_increments_len(self):
        chain = SupplyChain(batch_id=BATCH_A)
        chain.add_entry(_make_entry())
        assert len(chain) == 1

    def test_add_multiple_entries(self):
        chain, entries = _three_entry_chain()
        assert len(chain) == 3

    def test_add_wrong_batch_id_raises_value_error(self):
        chain = SupplyChain(batch_id=BATCH_A)
        wrong = _make_entry(batch_id=BATCH_B)
        with pytest.raises(ValueError, match="batch_id"):
            chain.add_entry(wrong)

    def test_add_non_entry_raises_type_error(self):
        chain = SupplyChain(batch_id=BATCH_A)
        with pytest.raises(TypeError):
            chain.add_entry("not-an-entry")  # type: ignore[arg-type]

    def test_add_none_raises_type_error(self):
        chain = SupplyChain(batch_id=BATCH_A)
        with pytest.raises(TypeError):
            chain.add_entry(None)  # type: ignore[arg-type]


# ===========================================================================
# 3. __contains__
# ===========================================================================

class TestContains:
    def test_batch_id_string_found(self):
        chain, _ = _three_entry_chain()
        assert BATCH_A in chain

    def test_wrong_batch_id_string_not_found(self):
        chain, _ = _three_entry_chain()
        assert BATCH_B not in chain

    def test_entry_object_found(self):
        chain, entries = _three_entry_chain()
        assert entries[0] in chain
        assert entries[2] in chain

    def test_entry_from_different_chain_not_found(self):
        chain, _ = _three_entry_chain()
        foreign = _make_entry(from_actor="Stranger", offset_hours=999)
        # Must create a separate chain to keep batch_id same but different entry
        assert foreign not in chain

    def test_non_string_non_entry_returns_false(self):
        chain, _ = _three_entry_chain()
        assert (42 in chain) is False


# ===========================================================================
# 4. __len__
# ===========================================================================

class TestLen:
    def test_len_empty(self):
        assert len(SupplyChain(batch_id=BATCH_A)) == 0

    def test_len_three(self):
        chain, _ = _three_entry_chain()
        assert len(chain) == 3


# ===========================================================================
# 5. __iter__ — chronological order
# ===========================================================================

class TestIter:
    def test_iter_returns_entries_in_time_order(self):
        # Add in reverse order to confirm sorting
        e1 = _make_entry(offset_hours=0)
        e2 = _make_entry(
            from_actor="Aggregator-001",
            to_actor="Processor-001",
            offset_hours=24,
            previous_hash=e1.current_hash,
        )
        chain = SupplyChain(batch_id=BATCH_A)
        chain.add_entry(e2)   # add later entry first
        chain.add_entry(e1)   # add earlier entry second

        result = list(chain)
        assert result[0].transfer_datetime < result[1].transfer_datetime

    def test_iter_all_entries_present(self):
        chain, entries = _three_entry_chain()
        result = list(chain)
        assert len(result) == 3
        for e in entries:
            assert e in result


# ===========================================================================
# 6. __add__ — merging two regional chains
# ===========================================================================

class TestMerge:
    def _split_chain(self):
        """Create two separate chains for the same batch (simulating regions)."""
        e1 = _make_entry(offset_hours=0)
        e2 = _make_entry(
            from_actor="Aggregator-001",
            to_actor="Processor-001",
            offset_hours=24,
            previous_hash=e1.current_hash,
        )
        e3 = _make_entry(
            from_actor="Processor-001",
            to_actor="Distributor-001",
            weight_kg=88.0,
            offset_hours=48,
            previous_hash=e2.current_hash,
        )

        chain_x = SupplyChain(batch_id=BATCH_A)
        chain_x.add_entry(e1)
        chain_x.add_entry(e2)

        chain_y = SupplyChain(batch_id=BATCH_A)
        chain_y.add_entry(e3)

        return chain_x, chain_y, [e1, e2, e3]

    def test_merge_produces_correct_total_length(self):
        cx, cy, _ = self._split_chain()
        merged = cx + cy
        assert len(merged) == 3

    def test_merge_is_sorted_by_time(self):
        cx, cy, _ = self._split_chain()
        merged = cx + cy
        times = [e.transfer_datetime for e in merged]
        assert times == sorted(times)

    def test_merge_deduplicates_shared_entries(self):
        """Same entry in both chains should appear only once after merge."""
        e1 = _make_entry(offset_hours=0)
        cx = SupplyChain(batch_id=BATCH_A)
        cx.add_entry(e1)
        cy = SupplyChain(batch_id=BATCH_A)
        cy.add_entry(e1)          # same entry object
        merged = cx + cy
        assert len(merged) == 1

    def test_merge_does_not_mutate_operands(self):
        cx, cy, _ = self._split_chain()
        _ = cx + cy
        assert len(cx) == 2
        assert len(cy) == 1

    def test_merge_different_batch_ids_raises_value_error(self):
        chain_a = SupplyChain(batch_id=BATCH_A)
        chain_b = SupplyChain(batch_id=BATCH_B)
        with pytest.raises(ValueError, match="batch IDs"):
            _ = chain_a + chain_b

    def test_merge_with_non_supply_chain_returns_not_implemented(self):
        chain = SupplyChain(batch_id=BATCH_A)
        result = chain.__add__("not-a-chain")  # type: ignore[arg-type]
        assert result is NotImplemented


# ===========================================================================
# 7. verify_integrity — clean chain
# ===========================================================================

class TestVerifyIntegrityClean:
    def test_empty_chain_is_valid(self):
        chain = SupplyChain(batch_id=BATCH_A)
        assert chain.verify_integrity() is True

    def test_single_entry_valid(self):
        chain = SupplyChain(batch_id=BATCH_A)
        chain.add_entry(_make_entry())
        assert chain.verify_integrity() is True

    def test_three_linked_entries_valid(self):
        chain, _ = _three_entry_chain()
        assert chain.verify_integrity() is True


# ===========================================================================
# 8. verify_integrity — tamper detection
# ===========================================================================

class TestVerifyIntegrityTampered:
    """
    LedgerEntry is immutable, so we simulate tampering by manipulating
    the internal ``_current_hash`` attribute directly — exactly how a bad
    actor who managed to access memory would try to cover their tracks.
    """

    def test_tampered_hash_raises_ledger_tampering_error(self):
        chain, entries = _three_entry_chain()
        # Corrupt the stored hash of the first entry
        object.__setattr__(entries[0], "_current_hash", "a" * 64)
        with pytest.raises(LedgerTamperingError):
            chain.verify_integrity()

    def test_tampered_error_carries_entry_id(self):
        chain, entries = _three_entry_chain()
        bad_entry = entries[1]
        object.__setattr__(bad_entry, "_current_hash", "b" * 64)
        with pytest.raises(LedgerTamperingError) as exc_info:
            chain.verify_integrity()
        assert str(bad_entry.entry_id) in str(exc_info.value)

    def test_tampered_error_carries_expected_and_computed_hashes(self):
        chain, entries = _three_entry_chain()
        bad_entry = entries[0]
        fake_hash = "c" * 64
        object.__setattr__(bad_entry, "_current_hash", fake_hash)
        with pytest.raises(LedgerTamperingError) as exc_info:
            chain.verify_integrity()
        err = exc_info.value
        # The error's stored expected_hash should be the fake one we injected
        assert err.expected_hash == fake_hash
        # The computed hash must differ from the fake one
        assert err.computed_hash != fake_hash

    def test_tampered_weight_detected(self):
        """Modifying a data field without updating the hash must be caught."""
        chain, entries = _three_entry_chain()
        # Secretly change the weight stored in the entry
        object.__setattr__(entries[0], "_weight_kg", 9999.0)
        with pytest.raises(LedgerTamperingError):
            chain.verify_integrity()

    def test_second_entry_tamper_is_caught(self):
        chain, entries = _three_entry_chain()
        object.__setattr__(entries[1], "_current_hash", "d" * 64)
        with pytest.raises(LedgerTamperingError):
            chain.verify_integrity()

    def test_merged_chain_tampering_detected(self):
        """Tampered entry in a merged chain must still be caught."""
        e1 = _make_entry(offset_hours=0)
        e2 = _make_entry(
            from_actor="Aggregator-001",
            to_actor="Processor-001",
            offset_hours=24,
            previous_hash=e1.current_hash,
        )
        cx = SupplyChain(batch_id=BATCH_A)
        cx.add_entry(e1)
        cy = SupplyChain(batch_id=BATCH_A)
        cy.add_entry(e2)
        merged = cx + cy

        object.__setattr__(e2, "_current_hash", "e" * 64)
        with pytest.raises(LedgerTamperingError):
            merged.verify_integrity()


# ===========================================================================
# 9. __repr__ and __str__
# ===========================================================================

class TestStringRepresentations:
    def test_repr_format(self):
        chain, _ = _three_entry_chain()
        r = repr(chain)
        assert "SupplyChain" in r
        assert BATCH_A in r
        assert "3" in r

    def test_str_lists_all_transfers(self):
        chain, entries = _three_entry_chain()
        s = str(chain)
        assert BATCH_A in s
        assert "FarmProducer-001" in s
        assert "Distributor-001" in s
        # Hash snippet should appear
        assert entries[0].current_hash[-8:] in s

    def test_str_empty_chain_note(self):
        chain = SupplyChain(batch_id=BATCH_A)
        assert "no transfers" in str(chain).lower()
