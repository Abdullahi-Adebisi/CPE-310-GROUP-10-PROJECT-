# CPE-310-GROUP-10-PROJECT-
Agricultural Supply Chain Tracking and Product Authenticity System

1. Project Title and Overview

This system is a blockchain-inspired agricultural supply chain
tracking platform built entirely in Python using Object-Oriented
Programming principles. It addresses the real-world problem of
food fraud, counterfeiting, and opaque supply chains in Nigeria's
agricultural sector — challenges that pose significant economic
and public health risks.

The platform tracks farm-to-market produce including grains
(rice, maize), perishables (tomatoes, peppers), and processed
goods. Each product batch is assigned a unique identity at the
farm stage. Every custody transfer — from Farm Producer through
Aggregator, Processor, Distributor, to Retailer — is recorded
as an immutable ledger entry whose SHA-256 hash chains to the
previous entry, making any tampering immediately detectable.
Quality inspectors issue certificates against recognised
Nigerian standards (NAFDAC, SON, Organic), and a consumer
verification function can query the full provenance of any
batch by its ID, returning an AUTHENTIC or SUSPICIOUS verdict.

The system runs entirely on the command line and requires
no graphical interface or external database.

2. Team Members
   
Full Name| Matric Number| GitHub Username
Adebisi Abdullahi Adeyemi| CPE/2023/1132| Abdullahi-Adebisi
Adeoye Lawrence| CPE/2024/2007| Lawrenxe-01
Oluwakayode iyanuoluwa temiloluwa| CPE/2024/2006| oluwakayodeiyanuoluwa242006-lang
Adebayo Yusuf Adebisi| CPE/2023/1134| yusufadebisi82
James Samuel Sunday| CPE/2023/1123| jamesamuel2411-max
Adeniyi Johnson Sanmi| CPE/2024/2002| Adeniyi-Johnson
Ojo kelvin inioluwa cpe| CPE/2023/1130| BIGKELV04
Adekunle Akinwale Trust| CPE/2024/2001| trust-tech44
Ajileye Samuel Ifeoluwa| CPE/2024/2004| Samuel-145
Ayomikun Onyebuchi Osinachi| CPE/2023/1133| 
Jonathan David Osemekhona| CPE/2023/1124| David-Jonathan1
Okoronkwo Cecilia Ijeoma| CPE/2024/2005| ceciliaprince4love-a11y|
Ajayi Oluwaseyi Cornelius| 
CPE/2024/2003|
ajayioluwaseyi088-sudo|
Adekunle Gbolahan Tofunmi| 
CPE/2023/1131

3. OOP Concepts Demonstrated

OOP Concept| Location in Code| Which Week
Classes & Objects| src/product_batch.py, class ProductBatch| Week 1
str method| src/product_batch.py, line ~95| Week 1
repr method| src/product_batch.py, line ~103| Week 1
Instance attributes| src/actors.py, all actor init methods| Week 1
Docstrings on every class| All files in src/| Week 1
Encapsulation (private attrs)| src/ledger_entry.py, all __ prefixed attrs| Week 2
@property with validation| src/product_batch.py, batch_id setter| Week 2
@property read-only| src/ledger_entry.py, all properties (no setters)| Week 2
Custom exception hierarchy| src/exceptions.py, all four exception classes| Week 2
Raising custom exceptions| src/actors.py, _validate_custody() method| Week 2
Abstract Base Class (ABC)| src/actors.py, class SupplyChainActor| Week 3
@abstractmethod| src/actors.py, transfer_custody()| Week 3
Inheritance| src/actors.py, FarmProducer, Aggregator etc| Week 3
super().init()| src/actors.py, all concrete actor classes| Week 3
Abstract ABC (QualityStandard)| src/quality.py, class QualityStandard| Week 3
Multiple concrete subclasses| src/quality.py, NafdacStandard, SONStandard, OrganicCertification| Week 3
Polymorphism| src/actors.py, transfer_custody() called on different actors| Week 4
Operator overloading eq| src/ledger_entry.py, equality by hash| Week 4
Operator overloading lt| src/ledger_entry.py, ordering by timestamp| Week 4
hash| src/ledger_entry.py, hashable by current_hash| Week 4
@total_ordering| src/ledger_entry.py, line 10| Week 4
contains| src/supply_chain.py, batch_id lookup| Week 4
len| src/supply_chain.py, number of transfers| Week 4
iter| src/supply_chain.py, iterate over entries| Week 4
add| src/supply_chain.py, merge two chains| Week 4
Duck typing| src/supply_chain.py, verify_integrity()| Week 4
UML Class Diagram| uml/class_diagram.png| Week 5
Composition| SupplyChain owns LedgerEntry objects| Week 5
Aggregation| ProductBatch references SupplyChainActor| Week 5
Realization (ABC arrows)| uml/class_diagram.puml, all ABC relationships| Week 5

4. System Architecture

"UML Class Diagram" (uml/class_diagram.png)

The system is organised into five clearly separated layers:

Exceptions Layer — Four custom exception classes in
src/exceptions.py handle all domain-specific error
conditions: LedgerTamperingError, InvalidCustodyTransferError,
CertificateExpiredError, and BatchNotFoundError. All inherit
from Python's built-in Exception class.

Product Layer — ProductBatch in src/product_batch.py
represents a traceable unit of agricultural produce. Its
batch_id is validated against the pattern NG-YYYY-XXXXXXXX
using a compiled regular expression. All numeric attributes
are protected by @property validators that reject negative
or zero values.

Actors Layer — SupplyChainActor in src/actors.py is
an abstract base class defining the participation contract
for all five concrete actors: FarmProducer, Aggregator,
Processor, Distributor, and Retailer. Each implements
transfer_custody() polymorphically. The Processor can
additionally split one batch into up to three sub-batches.

Ledger Layer — LedgerEntry in src/ledger_entry.py
is a fully immutable custody transfer record. Its SHA-256
current_hash chains all fields including the previous
entry's hash, so any modification is detectable.
SupplyChain in src/supply_chain.py uses composition
to own an ordered list of LedgerEntry objects and exposes
verify_integrity() to detect tampering by recomputing
every hash from scratch.

Quality Layer — QualityStandard in src/quality.py
is an abstract ABC with three concrete implementations:
NafdacStandard, SONStandard, and OrganicCertification.
A QualityInspector checks accreditation before issuing
QualityCertificate objects. The is_valid property checks
expiry against the current date.

Verification Layer — ConsumerVerifier in
src/consumer_verifier.py aggregates chain data and
certificates to produce a formatted provenance report
with an AUTHENTIC or SUSPICIOUS verdict.

Key design decisions:
SupplyChain uses composition with LedgerEntry
because ledger entries cannot exist independently — they
are created by and belong entirely to one chain.
ProductBatch uses aggregation with SupplyChainActor
because actors exist independently of any batch and can
hold custody of multiple batches over their lifetime.

5. How to Run

Clone the Repository

git clone https://github.com/yourusername/your_repo_name.git
cd your_repo_name
