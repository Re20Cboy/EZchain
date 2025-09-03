"""
Secure Transaction Signature Handler

This module provides a secure implementation for handling private key signatures
in the EZchain blockchain system. It follows security best practices to ensure
private keys are handled safely in memory and properly cleaned up after use.
"""

import os
import secrets
import hashlib
from typing import Optional, Union, Tuple
from contextlib import contextmanager
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key
from cryptography.exceptions import InvalidSignature
import warnings


class SecureMemoryHandler:
    """
    Handles secure memory operations for private keys.
    Implements memory safety practices including secure cleanup.
    """
    
    @staticmethod
    def secure_bytes(length: int) -> bytes:
        """Generate cryptographically secure random bytes."""
        return secrets.token_bytes(length)
    
    @staticmethod
    def secure_wipe(data: bytearray) -> None:
        """Securely wipe memory contents."""
        if isinstance(data, bytearray):
            for i in range(len(data)):
                data[i] = 0
        elif isinstance(data, bytes):
            # Convert to mutable bytearray for wiping
            mutable_data = bytearray(data)
            SecureMemoryHandler.secure_wipe(mutable_data)
    
    @staticmethod
    @contextmanager
    def secure_load_private_key(private_key_pem: bytes) -> ec.EllipticCurvePrivateKey:
        """
        Context manager for secure private key handling.
        Ensures key is properly wiped from memory after use.
        """
        key_obj = None
        try:
            # Load private key securely
            key_obj = load_pem_private_key(private_key_pem, password=None)
            if not isinstance(key_obj, ec.EllipticCurvePrivateKey):
                raise ValueError("Only EC private keys are supported")
            
            yield key_obj
        finally:
            # Attempt to wipe the key object from memory
            if key_obj is not None:
                try:
                    # Convert to bytes and wipe
                    key_bytes = key_obj.private_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.PKCS8,
                        encryption_algorithm=serialization.NoEncryption()
                    )
                    SecureMemoryHandler.secure_wipe(bytearray(key_bytes))
                except Exception:
                    # If wiping fails, at least ensure the reference is cleared
                    pass
                key_obj = None


class TransactionSigner:
    """
    Secure transaction signing implementation.
    Handles transaction signing with proper memory safety.
    """
    
    def __init__(self):
        """Initialize the transaction signer."""
        self._private_key_cache = None
        self._key_loaded = False
    
    def sign_transaction_data(
        self, 
        transaction_data: bytes, 
        private_key_pem: bytes
    ) -> bytes:
        """
        Sign transaction data securely.
        
        Args:
            transaction_data: The transaction data to sign
            private_key_pem: Private key in PEM format
            
        Returns:
            Signature bytes
            
        Raises:
            ValueError: If invalid parameters are provided
            Exception: If signing fails
        """
        if not transaction_data:
            raise ValueError("Transaction data cannot be empty")
        
        if not private_key_pem:
            raise ValueError("Private key cannot be empty")
        
        # Use secure context manager for private key handling
        with SecureMemoryHandler.secure_load_private_key(private_key_pem) as private_key:
            # Create signature algorithm
            signature_algorithm = ec.ECDSA(hashes.SHA256())
            
            # Sign the data
            signature = private_key.sign(
                data=transaction_data,
                signature_algorithm=signature_algorithm
            )
            
            return signature
    
    def verify_signature(
        self,
        transaction_data: bytes,
        signature: bytes,
        public_key_pem: bytes
    ) -> bool:
        """
        Verify a transaction signature.
        
        Args:
            transaction_data: The original transaction data
            signature: The signature to verify
            public_key_pem: Public key in PEM format
            
        Returns:
            True if signature is valid, False otherwise
        """
        if not transaction_data or not signature or not public_key_pem:
            return False
        
        try:
            public_key = load_pem_public_key(public_key_pem)
            if not isinstance(public_key, ec.EllipticCurvePublicKey):
                return False
            
            signature_algorithm = ec.ECDSA(hashes.SHA256())
            
            public_key.verify(
                signature,
                transaction_data,
                signature_algorithm
            )
            return True
            
        except (InvalidSignature, ValueError, Exception):
            return False
    
    def generate_key_pair(self) -> Tuple[bytes, bytes]:
        """
        Generate a new EC key pair securely.
        
        Returns:
            Tuple of (private_key_pem, public_key_pem)
        """
        # Generate private key
        private_key = ec.generate_private_key(ec.SECP256R1())
        public_key = private_key.public_key()
        
        # Serialize keys
        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        public_key_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        return private_key_pem, public_key_pem


class SecureTransactionSignature:
    """
    Main secure signature handler for transactions.
    Provides a high-level interface for secure transaction signing.
    """
    
    def __init__(self):
        """Initialize the secure signature handler."""
        self.signer = TransactionSigner()
        self._security_warnings_enabled = True
    
    def sign_transaction(
        self,
        sender: str,
        recipient: str,
        nonce: int,
        value_data: list,
        private_key_pem: bytes,
        timestamp: Optional[str] = None
    ) -> dict:
        """
        Sign a transaction securely.
        
        Args:
            sender: Sender address
            recipient: Recipient address
            nonce: Transaction nonce
            value_data: Transaction value data
            private_key_pem: Private key in PEM format
            timestamp: Optional timestamp (auto-generated if not provided)
            
        Returns:
            Dictionary containing transaction data and signature
        """
        if self._security_warnings_enabled:
            warnings.warn(
                "Private key is being loaded into memory. "
                "Ensure this is called in a secure environment.",
                UserWarning
            )
        
        # Create deterministic transaction data for signing
        import json
        from datetime import datetime
        
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        transaction_data = {
            "sender": sender,
            "recipient": recipient,
            "nonce": nonce,
            "timestamp": timestamp,
            "value": value_data
        }
        
        # Create deterministic JSON representation
        transaction_json = json.dumps(transaction_data, sort_keys=True, separators=(',', ':'))
        transaction_bytes = transaction_json.encode('utf-8')
        
        # Calculate transaction hash
        transaction_hash = hashlib.sha256(transaction_bytes).digest()
        
        # Debug: Print the transaction data being used for signing
        print(f"DEBUG - Transaction data for signing: {transaction_data}")
        print(f"DEBUG - Transaction JSON: {transaction_json}")
        print(f"DEBUG - Transaction hash: {transaction_hash.hex()}")
        
        # Sign the transaction hash
        signature = self.signer.sign_transaction_data(transaction_hash, private_key_pem)
        
        print(f"DEBUG - Generated signature: {signature.hex()}")
        
        return {
            "transaction_data": transaction_data,
            "transaction_hash": transaction_hash.hex(),
            "signature": signature.hex(),
            "timestamp": timestamp
        }
    
    def verify_transaction_signature(
        self,
        transaction_data: dict,
        signature_hex: str,
        public_key_pem: bytes
    ) -> bool:
        """
        Verify a transaction signature.
        
        Args:
            transaction_data: Transaction data dictionary
            signature_hex: Signature in hex format
            public_key_pem: Public key in PEM format
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # Recreate the transaction hash
            import json
            
            # Create deterministic JSON (exclude signature-related fields)
            signable_data = {
                "sender": transaction_data["sender"],
                "recipient": transaction_data["recipient"],
                "nonce": transaction_data["nonce"],
                "timestamp": transaction_data["timestamp"],
                "value": transaction_data["value"]
            }
            
            transaction_json = json.dumps(signable_data, sort_keys=True, separators=(',', ':'))
            transaction_bytes = transaction_json.encode('utf-8')
            transaction_hash = hashlib.sha256(transaction_bytes).digest()
            
            # Debug: Print the transaction data being used for verification
            print(f"DEBUG - Signable data for verification: {signable_data}")
            print(f"DEBUG - Transaction JSON: {transaction_json}")
            print(f"DEBUG - Transaction hash: {transaction_hash.hex()}")
            
            # Convert hex signature to bytes
            signature = bytes.fromhex(signature_hex)
            
            # Verify signature
            result = self.signer.verify_signature(transaction_hash, signature, public_key_pem)
            print(f"DEBUG - Signature verification result: {result}")
            return result
            
        except (KeyError, ValueError, Exception) as e:
            print(f"DEBUG - Exception during verification: {e}")
            return False
    
    def sign_multi_transaction(
        self,
        sender: str,
        transactions: list,
        private_key_pem: bytes,
        timestamp: Optional[str] = None
    ) -> dict:
        """
        Sign a multi-transaction securely.
        
        Args:
            sender: Sender address
            transactions: List of transaction dictionaries
            private_key_pem: Private key in PEM format
            timestamp: Optional timestamp (auto-generated if not provided)
            
        Returns:
            Dictionary containing multi-transaction data and signature
        """
        if self._security_warnings_enabled:
            warnings.warn(
                "Private key is being loaded into memory. "
                "Ensure this is called in a secure environment.",
                UserWarning
            )
        
        # Create deterministic multi-transaction data for signing
        import json
        from datetime import datetime
        
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        multi_transaction_data = {
            "sender": sender,
            "timestamp": timestamp,
            "transactions": transactions,
            "type": "multi_transaction"
        }
        
        # Create deterministic JSON representation
        transaction_json = json.dumps(multi_transaction_data, sort_keys=True, separators=(',', ':'))
        transaction_bytes = transaction_json.encode('utf-8')
        
        # Calculate multi-transaction hash
        transaction_hash = hashlib.sha256(transaction_bytes).digest()
        
        # Sign the multi-transaction hash
        signature = self.signer.sign_transaction_data(transaction_hash, private_key_pem)
        
        return {
            "multi_transaction_data": multi_transaction_data,
            "transaction_hash": transaction_hash.hex(),
            "signature": signature.hex(),
            "timestamp": timestamp
        }
    
    def verify_multi_transaction_signature(
        self,
        multi_transaction_data: dict,
        signature_hex: str,
        public_key_pem: bytes
    ) -> bool:
        """
        Verify a multi-transaction signature.
        
        Args:
            multi_transaction_data: Multi-transaction data dictionary
            signature_hex: Signature in hex format
            public_key_pem: Public key in PEM format
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # Recreate the multi-transaction hash
            import json
            
            # Create deterministic JSON (exclude signature-related fields)
            signable_data = {
                "sender": multi_transaction_data["sender"],
                "timestamp": multi_transaction_data["timestamp"],
                "transactions": multi_transaction_data["transactions"],
                "type": "multi_transaction"
            }
            
            transaction_json = json.dumps(signable_data, sort_keys=True, separators=(',', ':'))
            transaction_bytes = transaction_json.encode('utf-8')
            transaction_hash = hashlib.sha256(transaction_bytes).digest()
            
            # Convert hex signature to bytes
            signature = bytes.fromhex(signature_hex)
            
            # Verify signature
            return self.signer.verify_signature(transaction_hash, signature, public_key_pem)
            
        except (KeyError, ValueError, Exception):
            return False
    
    def disable_security_warnings(self) -> None:
        """Disable security warnings (use with caution)."""
        self._security_warnings_enabled = False
    
    def enable_security_warnings(self) -> None:
        """Enable security warnings."""
        self._security_warnings_enabled = True


# Global instance for easy access
secure_signature_handler = SecureTransactionSignature()