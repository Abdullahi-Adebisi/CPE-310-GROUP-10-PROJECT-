"""
Test suite for LedgerEntry class.
CPE 310 - OOP with Python | Project 10
Run with: pytest tests/test_ledger_entry.py -v
"""

import pytest
import time
from datetime import datetime
from src.ledger_entry import LedgerEntry


# ── Helpers ───────────────────────────────────────────
def make_entry(**kwargs):
    """Create a valid LedgerEntry with defaults."""
    defaults = dict(
        batch_id='NG-2026-AB123456',
        from_actor='FP001',
        to_actor='AGG001',
        weight_kg=500.0,
        previous_hash='0' * 64
    )
    defaults.update(kwargs)
    return LedgerEntry(**defaults)


# ── Construction Tests ────────────────────────────────
class TestLedgerEntryConstruction:

    def test_entry_created_successfully(self):
        entry = make_entry()
        assert entry.batch_id == 'NG-2026-AB123456'

    def test_entry_id_is_generated(self):
        entry = make_entry()
        assert entry.entry_id is not None
        assert len(entry.entry_id) == 36

    def test_two_entries_have_different_ids(self):
        entry1 = make_entry()
        entry2 = make_entry()
        assert entry1.entry_id != entry2.entry_id

    def test_from_actor_stored_correctly(self):
        entry = make_entry(from_actor='FP001')
        assert entry.from_actor == 'FP001'

    def test_to_actor_stored_correctly(self):
        entry = make_entry(to_actor='AGG001')
        assert entry.to_actor == 'AGG001'

    def test_weight_stored_as_float(self):
        entry = make_entry(weight_kg=500)
        assert isinstance(entry.weight_kg, float)
        assert entry.weight_kg == 500.0

    def test_previous_hash_stored_correctly(self):
        entry = make_entry(previous_hash='0' * 64)
        assert entry.previous_hash == '0' * 64

    def test_transfer_datetime_is_set(self):
        entry = make_entry()
        assert isinstance(
            entry.transfer_datetime, datetime
        )

    def test_current_hash_is_64_chars(self):
        entry = make_entry()
        assert len(entry.current_hash) == 64


# ── Immutability Tests ────────────────────────────────
class TestImmutability:

    def test_entry_id_has_no_setter(self):
        entry = make_entry()
        with pytest.raises(AttributeError):
            entry.entry_id = 'new-id'

    def test_batch_id_has_no_setter(self):
        entry = make_entry()
        with pytest.raises(AttributeError):
            entry.batch_id = 'NG-2026-ZZ999999'

    def test_from_actor_has_no_setter(self):
        entry = make_entry()
        with pytest.raises(AttributeError):
            entry.from_actor = 'HACKER001'

    def test_to_actor_has_no_setter(self):
        entry = make_entry()
        with pytest.raises(AttributeError):
            entry.to_actor = 'HACKER002'

    def test_weight_kg_has_no_setter(self):
        entry = make_entry()
        with pytest.raises(AttributeError):
            entry.weight_kg = 999.0

    def test_current_hash_has_no_setter(self):
        entry = make_entry()
        with pytest.raises(AttributeError):
            entry.current_hash = 'fakehash'

    def test_previous_hash_has_no_setter(self):
        entry = make_entry()
        with pytest.raises(AttributeError):
            entry.previous_hash = 'fakehash'

    def test_transfer_datetime_has_no_setter(self):
        entry = make_entry()
        with pytest.raises(AttributeError):
            entry.transfer_datetime = datetime.now()


# ── Hash Tests ────────────────────────────────────────
class TestHashing:

    def test_hash_is_consistent(self):
        entry = make_entry()
        assert (
            entry.current_hash == entry.recompute_hash()
        )

    def test_different_batches_have_different_hashes(self):
        entry1 = make_entry(
            batch_id='NG-2026-AB123456'
        )
        entry2 = make_entry(
            batch_id='NG-2026-CD789012'
        )
        assert entry1.current_hash != entry2.current_hash

    def test_hash_chains_from_previous(self):
        entry1 = make_entry()
        entry2 = make_entry(
            previous_hash=entry1.current_hash
        )
        assert entry2.previous_hash == entry1.current_hash

    def test_first_entry_previous_hash_is_zeros(self):
        entry = make_entry(previous_hash='0' * 64)
        assert entry.previous_hash == '0' * 64


# ── Equality Tests ────────────────────────────────────
class TestEquality:

    def test_same_entry_equals_itself(self):
        entry = make_entry()
        assert entry == entry

    def test_two_different_entries_not_equal(self):
        entry1 = make_entry()
        entry2 = make_entry()
        assert entry1 != entry2

    def test_equality_not_implemented_for_non_entry(self):
        entry = make_entry()
        assert entry.__eq__('not an entry') \
               == NotImplemented


# ── Ordering Tests ────────────────────────────────────
class TestOrdering:

    def test_earlier_entry_is_less_than_later(self):
        entry1 = make_entry()
        time.sleep(0.01)
        entry2 = make_entry()
        assert entry1 < entry2

    def test_later_entry_is_greater_than_earlier(self):
        entry1 = make_entry()
        time.sleep(0.01)
        entry2 = make_entry()
        assert entry2 > entry1

    def test_entries_can_be_sorted(self):
        entry1 = make_entry()
        time.sleep(0.01)
        entry2 = make_entry()
        time.sleep(0.01)
        entry3 = make_entry()
        entries = [entry3, entry1, entry2]
        sorted_entries = sorted(entries)
        assert sorted_entries[0] == entry1
        assert sorted_entries[2] == entry3

    def test_lt_not_implemented_for_non_entry(self):
        entry = make_entry()
        assert entry.__lt__('not an entry') \
               == NotImplemented


# ── Hashability Tests ─────────────────────────────────
class TestHashability:

    def test_entry_can_be_added_to_set(self):
        entry = make_entry()
        entry_set = {entry}
        assert entry in entry_set

    def test_same_entry_not_duplicated_in_set(self):
        entry = make_entry()
        entry_set = {entry, entry}
        assert len(entry_set) == 1

    def test_entry_can_be_used_as_dict_key(self):
        entry = make_entry()
        entry_dict = {entry: 'value'}
        assert entry_dict[entry] == 'value'


# ── Dunder String Tests ───────────────────────────────
class TestDunderStrings:

    def test_str_contains_batch_id(self):
        entry = make_entry(
            batch_id='NG-2026-AB123456'
        )
        assert 'NG-2026-AB123456' in str(entry)

    def test_str_contains_from_actor(self):
        entry = make_entry(from_actor='FP001')
        assert 'FP001' in str(entry)

    def test_str_contains_to_actor(self):
        entry = make_entry(to_actor='AGG001')
        assert 'AGG001' in str(entry)

    def test_repr_contains_batch_id(self):
        entry = make_entry(
            batch_id='NG-2026-AB123456'
        )
        assert 'NG-2026-AB123456' in repr(entry)

    def test_repr_contains_from_actor(self):
        entry = make_entry(from_actor='FP001')
        assert 'FP001' in repr(entry)
