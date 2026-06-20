import pytest
from datetime import date
from src.actors import (
    SupplyChainActor,
    FarmProducer,
    Aggregator,
    Processor,
    Distributor,
    Retailer
)
from src.product_batch import ProductBatch
from src.exceptions import InvalidCustodyTransferError


# ── Helpers ───────────────────────────────────────────
def make_farm_producer(actor_id='FP001'):
    return FarmProducer(
        actor_id=actor_id,
        name='Green Acres Farm',
        location='Ekiti North',
        farm_size_hectares=50.0
    )

def make_aggregator(actor_id='AGG001'):
    return Aggregator(
        actor_id=actor_id,
        name='Ekiti Aggregators Ltd',
        location='Ado-Ekiti',
        warehouse_capacity_kg=10000.0
    )

def make_processor(actor_id='PROC001'):
    return Processor(
        actor_id=actor_id,
        name='NigerFoods Processing',
        location='Lagos',
        processing_type='Milling'
    )

def make_distributor(actor_id='DIST001'):
    return Distributor(
        actor_id=actor_id,
        name='SwiftMove Distributors',
        location='Ibadan',
        distribution_region='South-West'
    )

def make_retailer(actor_id='RET001'):
    return Retailer(
        actor_id=actor_id,
        name='FreshMart Supermarket',
        location='Abuja',
        store_name='FreshMart Wuse'
    )

def make_batch(custodian):
    return ProductBatch(
        batch_id='NG-2026-AB123456',
        product_name='Rice',
        category='Grains',
        origin_farm='Green Acres Farm',
        harvest_date=date(2026, 1, 10),
        initial_weight_kg=500.0,
        current_custodian=custodian
    )


# ── Abstract Class Tests ──────────────────────────────
class TestAbstractClass:

    def test_supply_chain_actor_cannot_be_instantiated(
        self
    ):
        with pytest.raises(TypeError):
            SupplyChainActor(
                'A001', 'Test', 'Lagos'
            )

    def test_concrete_class_must_implement_transfer(
        self
    ):
        class IncompleteActor(SupplyChainActor):
            pass
        with pytest.raises(TypeError):
            IncompleteActor(
                'A001', 'Test', 'Lagos'
            )


# ── FarmProducer Tests ────────────────────────────────
class TestFarmProducer:

    def test_farm_producer_created_successfully(self):
        fp = make_farm_producer()
        assert fp.actor_id == 'FP001'

    def test_farm_producer_actor_type(self):
        fp = make_farm_producer()
        assert fp.actor_type == 'FarmProducer'

    def test_farm_size_stored_correctly(self):
        fp = make_farm_producer()
        assert fp.farm_size_hectares == 50.0

    def test_farm_producer_transfer_returns_entry(
        self
    ):
        fp = make_farm_producer()
        agg = make_aggregator()
        batch = make_batch(fp)
        entry = fp.transfer_custody(
            batch, agg, 490.0
        )
        assert entry is not None
        assert entry.from_actor == 'FP001'
        assert entry.to_actor == 'AGG001'

    def test_transfer_updates_custodian(self):
        fp = make_farm_producer()
        agg = make_aggregator()
        batch = make_batch(fp)
        fp.transfer_custody(batch, agg, 490.0)
        assert (
            batch.current_custodian.actor_id
            == 'AGG001'
        )

    def test_transfer_updates_weight(self):
        fp = make_farm_producer()
        agg = make_aggregator()
        batch = make_batch(fp)
        fp.transfer_custody(batch, agg, 490.0)
        assert batch.current_weight_kg == 490.0

    def test_str_contains_actor_id(self):
        fp = make_farm_producer()
        assert 'FP001' in str(fp)

    def test_repr_contains_class_name(self):
        fp = make_farm_producer()
        assert 'FarmProducer' in repr(fp)


# ── Aggregator Tests ──────────────────────────────────
class TestAggregator:

    def test_aggregator_created_successfully(self):
        agg = make_aggregator()
        assert agg.actor_id == 'AGG001'

    def test_aggregator_actor_type(self):
        agg = make_aggregator()
        assert agg.actor_type == 'Aggregator'

    def test_warehouse_capacity_stored(self):
        agg = make_aggregator()
        assert agg.warehouse_capacity_kg == 10000.0

    def test_aggregator_transfer_returns_entry(self):
        fp = make_farm_producer()
        agg = make_aggregator()
        proc = make_processor()
        batch = make_batch(fp)
        fp.transfer_custody(batch, agg, 490.0)
        entry = agg.transfer_custody(
            batch, proc, 485.0
        )
        assert entry.from_actor == 'AGG001'
        assert entry.to_actor == 'PROC001'


# ── Processor Tests ───────────────────────────────────
class TestProcessor:

    def test_processor_created_successfully(self):
        proc = make_processor()
        assert proc.actor_id == 'PROC001'

    def test_processing_type_stored(self):
        proc = make_processor()
        assert proc.processing_type == 'Milling'

    def test_processor_transfer_returns_entry(self):
        fp = make_farm_producer()
        agg = make_aggregator()
        proc = make_processor()
        dist = make_distributor()
        batch = make_batch(fp)
        fp.transfer_custody(batch, agg, 490.0)
        agg.transfer_custody(batch, proc, 485.0)
        entry = proc.transfer_custody(
            batch, dist, 480.0
        )
        assert entry.from_actor == 'PROC001'

    def test_split_batch_returns_correct_count(self):
        fp = make_farm_producer()
        agg = make_aggregator()
        proc = make_processor()
        batch = make_batch(fp)
        fp.transfer_custody(batch, agg, 490.0)
        agg.transfer_custody(batch, proc, 485.0)
        sub_batches = proc.split_batch(
            batch, [200.0, 150.0, 100.0]
        )
        assert len(sub_batches) == 3

    def test_split_batch_max_3_sub_batches(self):
        fp = make_farm_producer()
        agg = make_aggregator()
        proc = make_processor()
        batch = make_batch(fp)
        fp.transfer_custody(batch, agg, 490.0)
        agg.transfer_custody(batch, proc, 485.0)
        with pytest.raises(ValueError):
            proc.split_batch(
                batch,
                [100.0, 100.0, 100.0, 100.0]
            )

    def test_split_batch_weight_exceeds_raises(self):
        fp = make_farm_producer()
        agg = make_aggregator()
        proc = make_processor()
        batch = make_batch(fp)
        fp.transfer_custody(batch, agg, 490.0)
        agg.transfer_custody(batch, proc, 485.0)
        with pytest.raises(ValueError):
            proc.split_batch(
                batch,
                [300.0, 300.0]
            )


# ── Distributor Tests ─────────────────────────────────
class TestDistributor:

    def test_distributor_created_successfully(self):
        dist = make_distributor()
        assert dist.actor_id == 'DIST001'

    def test_distribution_region_stored(self):
        dist = make_distributor()
        assert (
            dist.distribution_region == 'South-West'
        )

    def test_distributor_transfer_returns_entry(
        self
    ):
        fp = make_farm_producer()
        agg = make_aggregator()
        proc = make_processor()
        dist = make_distributor()
        ret = make_retailer()
        batch = make_batch(fp)
        fp.transfer_custody(batch, agg, 490.0)
        agg.transfer_custody(batch, proc, 485.0)
        proc.transfer_custody(batch, dist, 480.0)
        entry = dist.transfer_custody(
            batch, ret, 475.0
        )
        assert entry.from_actor == 'DIST001'
        assert entry.to_actor == 'RET001'


# ── Retailer Tests ────────────────────────────────────
class TestRetailer:

    def test_retailer_created_successfully(self):
        ret = make_retailer()
        assert ret.actor_id == 'RET001'

    def test_store_name_stored(self):
        ret = make_retailer()
        assert ret.store_name == 'FreshMart Wuse'

    def test_retailer_actor_type(self):
        ret = make_retailer()
        assert ret.actor_type == 'Retailer'


# ── Custody Validation Tests ──────────────────────────
class TestCustodyValidation:

    def test_wrong_custodian_raises_error(self):
        fp = make_farm_producer()
        agg = make_aggregator()
        wrong_actor = make_processor()
        batch = make_batch(fp)
        with pytest.raises(
            InvalidCustodyTransferError
        ):
            wrong_actor.transfer_custody(
                batch, agg, 490.0
            )

    def test_correct_custodian_transfer_succeeds(
        self
    ):
        fp = make_farm_producer()
        agg = make_aggregator()
        batch = make_batch(fp)
        entry = fp.transfer_custody(
            batch, agg, 490.0
        )
        assert entry is not None

    def test_chain_of_custody_succeeds(self):
        fp = make_farm_producer()
        agg = make_aggregator()
        proc = make_processor()
        dist = make_distributor()
        ret = make_retailer()
        batch = make_batch(fp)

        fp.transfer_custody(batch, agg, 490.0)
        agg.transfer_custody(batch, proc, 485.0)
        proc.transfer_custody(batch, dist, 480.0)
        dist.transfer_custody(batch, ret, 475.0)

        assert (
            batch.current_custodian.actor_id
            == 'RET001'
        )
        assert batch.current_weight_kg == 475.0
