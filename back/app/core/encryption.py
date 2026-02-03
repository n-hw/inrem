"""Encryption service for sensitive data protection.

Uses Fernet symmetric encryption (AES-128-CBC with HMAC).
"""

from cryptography.fernet import Fernet, InvalidToken
from typing import Any

from app.core.config import settings
from app.core.exceptions import EncryptionError, DecryptionError, KeyNotFoundError


class EncryptionService:
    """Service for encrypting and decrypting sensitive data.
    
    Uses Fernet encryption which provides:
    - AES-128-CBC encryption
    - HMAC-SHA256 authentication
    - Automatic IV generation
    - Timestamp verification
    """
    
    _instance: "EncryptionService | None" = None
    _fernet: Fernet | None = None
    
    def __new__(cls) -> "EncryptionService":
        """Singleton pattern to reuse Fernet instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self) -> None:
        """Initialize the Fernet cipher with the encryption key."""
        key = settings.ENCRYPTION_KEY
        if not key:
            raise KeyNotFoundError(
                "ENCRYPTION_KEY not configured. "
                "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
            )
        
        try:
            # Ensure key is bytes
            if isinstance(key, str):
                key = key.encode('utf-8')
            self._fernet = Fernet(key)
        except Exception as e:
            raise EncryptionError(f"Invalid encryption key format: {e}")
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt a plaintext string.
        
        Args:
            plaintext: The string to encrypt.
            
        Returns:
            Base64-encoded encrypted string.
            
        Raises:
            EncryptionError: If encryption fails.
        """
        if not plaintext:
            return plaintext
            
        try:
            encrypted = self._fernet.encrypt(plaintext.encode('utf-8'))
            return encrypted.decode('utf-8')
        except Exception as e:
            raise EncryptionError(f"Failed to encrypt data: {e}")
    
    def decrypt(self, ciphertext: str) -> str:
        """Decrypt a ciphertext string.
        
        Args:
            ciphertext: The Base64-encoded encrypted string.
            
        Returns:
            Decrypted plaintext string.
            
        Raises:
            DecryptionError: If decryption fails (invalid key or corrupted data).
        """
        if not ciphertext:
            return ciphertext
            
        try:
            decrypted = self._fernet.decrypt(ciphertext.encode('utf-8'))
            return decrypted.decode('utf-8')
        except InvalidToken:
            raise DecryptionError(
                "Failed to decrypt data. "
                "This may be due to an invalid key or corrupted/tampered data."
            )
        except Exception as e:
            raise DecryptionError(f"Decryption error: {e}")
    
    def encrypt_dict(self, data: dict[str, Any], fields: list[str]) -> dict[str, Any]:
        """Encrypt specific fields in a dictionary.
        
        Args:
            data: Dictionary containing data to encrypt.
            fields: List of field names to encrypt.
            
        Returns:
            New dictionary with specified fields encrypted.
        """
        result = data.copy()
        for field in fields:
            if field in result and result[field] is not None:
                if isinstance(result[field], str):
                    result[field] = self.encrypt(result[field])
        return result
    
    def decrypt_dict(self, data: dict[str, Any], fields: list[str]) -> dict[str, Any]:
        """Decrypt specific fields in a dictionary.
        
        Args:
            data: Dictionary containing encrypted data.
            fields: List of field names to decrypt.
            
        Returns:
            New dictionary with specified fields decrypted.
        """
        result = data.copy()
        for field in fields:
            if field in result and result[field] is not None:
                if isinstance(result[field], str):
                    result[field] = self.decrypt(result[field])
        return result


# Singleton instance for easy import
def get_encryption_service() -> EncryptionService:
    """Get the singleton EncryptionService instance.
    
    Usage:
        from app.core.encryption import get_encryption_service
        
        encryption = get_encryption_service()
        encrypted = encryption.encrypt("secret data")
        decrypted = encryption.decrypt(encrypted)
    """
    return EncryptionService()
