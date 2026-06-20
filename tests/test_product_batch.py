
import pytest
from datetime import date
from src.exceptions import (
    LedgerTamperingError,
    InvalidCustodyTransferError,
    CertificateExpiredError,
    BatchNotFoundError
)
from src.product_batch import ProductBatch


# ── Helpers ───────────────────────────────────────────
class MockCustodian:
    """Mock actor for testing purposes."""
    def __init__(self, actor_id):
        self.actor_id = actor_id

    def __repr__(self):
        return f'MockCustodian({self.actor_id})'


def make_batch(**kwargs):
    """Create a valid ProductBatch with defaults."""
    defaults = dict(
        batch_id='NG-2026-AB123456',
        product_name='Rice',
        category='Grains',
        origin_farm='Green Acres Farm',
        harvest_date=date(2026, 1, 10),
        initial_weight_kg=500.0,
        current_custodian=MockCustodian('FP001')
    )
    defaults.update(kwargs)
    return ProductBatch(**defaults)


# ── ProductBatch Construction Tests ───────────────────
class TestProductBatchConstruction:

    def test_valid_batch_created_successfully(self):
        batch = make_batch()
        assert batch.batch_id == 'NG-2026-AB123456'

    def test_product_name_stored_correctly(self):
        batch = make_batch(product_name='Tomatoes')
        assert batch.product_name == 'Tomatoes'

    def test_category_stored_correctly(self):
        batch = make_batch(category='Perishables')
        assert batch.category == 'Perishables'

    def test_origin_farm_stored_correctly(self):
        batch = make_batch(origin_farm='Ekiti Farm')
        assert batch.origin_farm == 'Ekiti Farm'

    def test_initial_weight_stored_correctly(self):
        batch = make_batch(initial_weight_kg=300.0)
        assert batch.initial_weight_kg == 300.0

    def test_current_weight_equals_initial_on_creation(self):
        batch = make_batch(initial_weight_kg=400.0)
        assert batch.current_weight_kg == 400.0

    def test_custodian_assigned_correctly(self):
        custodian = MockCustodian('FP001')
        batch = make_batch(current_custodian=custodian)
        assert batch.current_custodian.actor_id == 'FP001'


# ── batch_id Validation Tests ─────────────────────────
class TestBatchIdValidation:

    def test_valid_batch_id_accepted(self):
        batch = make_batch(batch_id='NG-2026-AB123456')
        assert batch.batch_id == 'NG-2026-AB123456'

    def test_lowercase_letters_rejected(self):
        with pytest.raises(ValueError):
            make_batch(batch_id='NG-2026-ab123456')

    def test_missing_ng_prefix_rejected(self):
        with pytest.raises(ValueError):
            make_batch(batch_id='US-2026-AB123456')

    def test_wrong_year_format_rejected(self):
        with pytest.raises(ValueError):
            make_batch(batch_id='NG-26-AB123456')

    def test_too_short_code_rejected(self):
        with pytest.raises(ValueError):
            make_batch(batch_id='NG-2026-ABC')

    def test_non_string_batch_id_rejected(self):
        with pytest.raises(TypeError):
            make_batch(batch_id=12345)


# ── Weight Validation Tests ───────────────────────────
class TestWeightValidation:

    def test_zero_initial_weight_rejected(self):
        with pytest.raises(ValueError):
            make_batch(initial_weight_kg=0)

    def test_negative_initial_weight_rejected(self):
        with pytest.raises(ValueError):
            make_batch(initial_weight_kg=-10)

    def test_current_weight_can_be_updated(self):
        batch = make_batch(initial_weight_kg=500.0)
        batch.current_weight_kg = 450.0
        assert batch.current_weight_kg == 450.0

    def test_negative_current_weight_rejected(self):
        batch = make_batch()
        with pytest.raises(ValueError):
            batch.current_weight_kg = -5.0


# ── Custodian Tests ───────────────────────────────────
class TestCustodianAssignment:

    def test_custodian_can_be_updated(self):
        batch = make_batch()
        new_custodian = MockCustodian('AGG001')
        batch.current_custodian = new_custodian
        assert batch.current_custodian.actor_id == 'AGG001'

    def test_none_custodian_rejected(self):
        batch = make_batch()
        with pytest.raises(ValueError):
            batch.current_custodian = None


# ── Dunder Method Tests ───────────────────────────────
class TestDunderMethods:

    def test_str_contains_batch_id(self):
        batch = make_batch()
        assert 'NG-2026-AB123456' in str(batch)

    def test_str_contains_product_name(self):
        batch = make_batch(product_name='Maize')
        assert 'Maize' in str(batch)

    def test_repr_contains_batch_id(self):
        batch = make_batch()
        assert 'NG-2026-AB123456' in repr(batch)


# ── Exception Tests ───────────────────────────────────
class TestExceptions:

    def test_ledger_tampering_error_raised(self):
        with pytest.raises(LedgerTamperingError):
            raise LedgerTamperingError(
                'E001', 'abc123', 'xyz789'
            )

    def test_ledger_tampering_stores_entry_id(self):
        err = LedgerTamperingError('E001', 'abc', 'xyz')
        assert err.entry_id == 'E001'

    def test_invalid_custody_transfer_raised(self):
        with pytest.raises(InvalidCustodyTransferError):
            raise InvalidCustodyTransferError(
                actor_id='FP001',
                batch_id='NG-2026-AB123456'
            )

    def test_certificate_expired_error_raised(self):
        with pytest.raises(CertificateExpiredError):
            raise CertificateExpiredError(
                cert_id='CERT001',
                expiry_date=date(2025, 1, 1)
            )

    def test_batch_not_found_error_raised(self):
        with pytest.raises(BatchNotFoundError):
            raise BatchNotFoundError(
                batch_id='NG-2026-ZZ999999'
            )

    def test_all_exceptions_inherit_from_exception(self):
        assert issubclass(LedgerTamperingError, Exception)
        assert issubclass(
            InvalidCustodyTransferError, Exception
        )
        assert issubclass(CertificateExpiredError, Exception)
        assert issubclass(BatchNotFoundError, Exception)
