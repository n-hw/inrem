"""Custom exceptions for the InRem application."""


class InRemException(Exception):
    """Base exception for InRem application."""
    pass


class EncryptionError(InRemException):
    """Raised when encryption operation fails."""
    pass


class DecryptionError(InRemException):
    """Raised when decryption operation fails.
    
    This can occur due to:
    - Invalid encryption key
    - Corrupted ciphertext
    - Tampered data (HMAC verification failure)
    """
    pass


class KeyNotFoundError(InRemException):
    """Raised when encryption key is not configured."""
    pass
