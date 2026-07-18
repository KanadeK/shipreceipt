class ShipReceiptError(Exception):
    """Base class for user-facing ShipReceipt errors."""


class UnsafePathError(ShipReceiptError):
    """Raised when a filesystem path is unsafe to include in a receipt."""


class ReceiptFormatError(ShipReceiptError):
    """Raised when a receipt is malformed or has been tampered with."""


class KeyFileError(ShipReceiptError):
    """Raised when a signing key file cannot be read or written safely."""
