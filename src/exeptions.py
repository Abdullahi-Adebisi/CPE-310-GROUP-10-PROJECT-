
class LedgerTamperingError(Exception):
    """
    Raised when a ledger entry's hash does not match
    the recomputed hash, indicating tampering.
    """
    def __init__(self, entry_id: str, 
                 expected_hash: str, 
                 computed_hash: str):
        self.entry_id = entry_id
        self.expected_hash = expected_hash
        self.computed_hash = computed_hash
        super().__init__(
            f'TAMPER DETECTED in entry {entry_id}! '
            f'Expected: {expected_hash[:16]}... '
            f'Recomputed: {computed_hash[:16]}...'
        )

    def __str__(self):
        return (
            f'LedgerTamperingError: Entry {self.entry_id}\n'
            f'  Expected Hash : {self.expected_hash[:16]}...\n'
            f'  Computed Hash : {self.computed_hash[:16]}...'
        )

    def __repr__(self):
        return (
            f'LedgerTamperingError(entry_id={self.entry_id!r},'
            f'expected_hash={self.expected_hash[:16]!r},...)'
        )


class InvalidCustodyTransferError(Exception):
    """
    Raised when a custody transfer is attempted but
    the from_actor does not match the batch's
    current custodian.
    """
    def __init__(self, message: str = None,
                 actor_id: str = None,
                 batch_id: str = None):
        self.actor_id = actor_id
        self.batch_id = batch_id
        if message:
            super().__init__(message)
        else:
            super().__init__(
                f'Invalid custody transfer: Actor '
                f'{actor_id} is not the current '
                f'custodian of batch {batch_id}.'
            )

    def __str__(self):
        return (
            f'InvalidCustodyTransferError: '
            f'Actor {self.actor_id} cannot transfer '
            f'batch {self.batch_id} — not current custodian.'
        )

    def __repr__(self):
        return (
            f'InvalidCustodyTransferError('
            f'actor_id={self.actor_id!r}, '
            f'batch_id={self.batch_id!r})'
        )


class CertificateExpiredError(Exception):
    """
    Raised when an operation is attempted using
    an expired quality certificate.
    """
    def __init__(self, cert_id: str = None,
                 expiry_date=None):
        self.cert_id = cert_id
        self.expiry_date = expiry_date
        super().__init__(
            f'Certificate {cert_id} expired on '
            f'{expiry_date}.'
        )

    def __str__(self):
        return (
            f'CertificateExpiredError: '
            f'Certificate {self.cert_id} '
            f'expired on {self.expiry_date}.'
        )

    def __repr__(self):
        return (
            f'CertificateExpiredError('
            f'cert_id={self.cert_id!r}, '
            f'expiry_date={self.expiry_date!r})'
        )


class BatchNotFoundError(Exception):
    """
    Raised when a product batch cannot be found
    by its batch ID.
    """
    def __init__(self, batch_id: str = None):
        self.batch_id = batch_id
        super().__init__(
            f'Batch {batch_id} not found in the system.'
        )

    def __str__(self):
        return (
            f'BatchNotFoundError: '
            f'Batch {self.batch_id} does not exist.'
        )

    def __repr__(self):
        return (
            f'BatchNotFoundError('
            f'batch_id={self.batch_id!r})'
                   )
