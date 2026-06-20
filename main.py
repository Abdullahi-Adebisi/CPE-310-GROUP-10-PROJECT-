from datetime import date

from src.product_batch import ProductBatch
from src.actors import (
    FarmProducer,
    Aggregator,
    Processor,
    Distributor,
    Retailer,
)
from src.supply_chain import SupplyChain
from src.quality import (
    NafdacStandard,
    SONStandard,
    QualityInspector,
)
from src.consumer_verifier import ConsumerVerifier
from src.exceptions import LedgerTamperingError


def process_batch(
    batch,
    farm,
    aggregator,
    processor,
    distributor,
    retailer,
):
    """
    Move a batch through all 5 actor types.
    Returns completed SupplyChain object.
    """

    chain = SupplyChain()

    e1 = farm.transfer_custody(batch, aggregator, batch.current_weight_kg)
    chain.add_entry(e1)

    e2 = aggregator.transfer_custody(
        batch,
        processor,
        batch.current_weight_kg,
    )
    chain.add_entry(e2)

    e3 = processor.transfer_custody(
        batch,
        distributor,
        batch.current_weight_kg,
    )
    chain.add_entry(e3)

    e4 = distributor.transfer_custody(
        batch,
        retailer,
        batch.current_weight_kg,
    )
    chain.add_entry(e4)

    return chain


def issue_certificates(batch):
    """
    Creates two certificates for a batch.
    """

    nafdac = NafdacStandard()
    son = SONStandard()

    inspector = QualityInspector(
        inspector_id="QI-001",
        name="Engr. Adewale",
        accredited_standards=[nafdac, son],
    )

    cert1 = nafdac.inspect(batch, inspector)
    cert2 = son.inspect(batch, inspector)

    return [cert1, cert2]


def main():
    print("\n" + "=" * 70)
    print("AGRICULTURAL SUPPLY CHAIN TRACKING SYSTEM")
    print("=" * 70)

    # --------------------------------------------------
    # ACTORS
    # --------------------------------------------------

    farm = FarmProducer(
        "FARM-001",
        "Farm Producer",
        "Ekiti State",
    )

    aggregator = Aggregator(
        "AGG-001",
        "Aggregator",
        "Ibadan",
    )

    processor = Processor(
        "PROC-001",
        "Processor",
        "Ogun State",
    )

    distributor = Distributor(
        "DIST-001",
        "Distributor",
        "Lagos",
    )

    retailer = Retailer(
        "RET-001",
        "Retailer",
        "Abuja",
    )

    # --------------------------------------------------
    # PRODUCT BATCHES
    # --------------------------------------------------

    rice_batch = ProductBatch(
        batch_id="NG-2026-00000001",
        product_name="Rice",
        category="Grains",
        origin_farm="Ado Farm",
        harvest_date=date(2026, 1, 10),
        initial_weight_kg=1000,
        current_weight_kg=1000,
        current_custodian=farm,
    )

    tomato_batch = ProductBatch(
        batch_id="NG-2026-00000002",
        product_name="Tomatoes",
        category="Vegetables",
        origin_farm="Green Valley Farm",
        harvest_date=date(2026, 2, 15),
        initial_weight_kg=800,
        current_weight_kg=800,
        current_custodian=farm,
    )

    cassava_batch = ProductBatch(
        batch_id="NG-2026-00000003",
        product_name="Processed Cassava Flour",
        category="Processed Goods",
        origin_farm="Unity Farm",
        harvest_date=date(2026, 3, 20),
        initial_weight_kg=600,
        current_weight_kg=600,
        current_custodian=farm,
    )

    # --------------------------------------------------
    # SUPPLY CHAINS
    # --------------------------------------------------

    rice_chain = process_batch(
        rice_batch,
        farm,
        aggregator,
        processor,
        distributor,
        retailer,
    )

    tomato_chain = process_batch(
        tomato_batch,
        farm,
        aggregator,
        processor,
        distributor,
        retailer,
    )

    cassava_chain = process_batch(
        cassava_batch,
        farm,
        aggregator,
        processor,
        distributor,
        retailer,
    )

    # --------------------------------------------------
    # CERTIFICATES
    # --------------------------------------------------

    rice_certs = issue_certificates(rice_batch)
    tomato_certs = issue_certificates(tomato_batch)
    cassava_certs = issue_certificates(cassava_batch)

    verifier = ConsumerVerifier()

    # --------------------------------------------------
    # REPORTS
    # --------------------------------------------------

    print("\n\nRICE REPORT")
    print("-" * 70)
    print(
        verifier.verify(
            rice_batch.batch_id,
            rice_chain,
            rice_certs,
        )
    )

    print("\n\nTOMATO REPORT")
    print("-" * 70)
    print(
        verifier.verify(
            tomato_batch.batch_id,
            tomato_chain,
            tomato_certs,
        )
    )

    print("\n\nCASSAVA FLOUR REPORT")
    print("-" * 70)
    print(
        verifier.verify(
            cassava_batch.batch_id,
            cassava_chain,
            cassava_certs,
        )
    )

    # --------------------------------------------------
    # TAMPER DETECTION DEMO
    # --------------------------------------------------

    print("\n\nTAMPER DETECTION DEMONSTRATION")
    print("-" * 70)

    try:
        tampered_entry = rice_chain._entries[1]

        # simulate tampering
        tampered_entry._weight_kg = 9999

        rice_chain.verify_integrity()

        print("Integrity Check: PASSED")

    except LedgerTamperingError as err:
        print("Tampering Detected!")
        print(err)

    except Exception as err:
        print("Unexpected Error:", err)

    print("\n" + "=" * 70)
    print("SIMULATION COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()
