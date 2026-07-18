"""ShipReceipt public API."""

from shipreceipt.service import create_receipt, verify_receipt

__all__ = ["__version__", "create_receipt", "verify_receipt"]

__version__ = "0.1.0"
