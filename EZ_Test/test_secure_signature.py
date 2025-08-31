"""
Security tests for the SecureSignature module.

This module provides comprehensive tests to verify the security and functionality
of the secure signature handling implementation.
"""

import pytest
import os
import sys
import hashlib
import json
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from EZ_Tool_Box.SecureSignature import (
    SecureMemoryHandler,
    TransactionSigner,
    SecureTransactionSignature,
    secure_signature_handler
)
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization


class TestSecureMemoryHandler:
    """Test suite for SecureMemoryHandler."""
    
    def test_secure_bytes_generation(self):
        """Test secure random bytes generation."""
        # Test different lengths
        for length in [16, 32, 64]:
            secure_bytes = SecureMemoryHandler.secure_bytes(length)
            assert len(secure_bytes) == length
            assert isinstance(secure_bytes, bytes)
            
            # Verify bytes are different each time
            secure_bytes2 = SecureMemoryHandler.secure_bytes(length)
            assert secure_bytes != secure_bytes2
    
    def test_secure_wipe_bytearray(self):
        """Test secure wiping of bytearray."""
        test_data = bytearray(b"secret_data_12345")
        original_length = len(test_data)
        
        SecureMemoryHandler.secure_wipe(test_data)
        
        # Verify all bytes are zeroed
        assert all(byte == 0 for byte in test_data)
        assert len(test_data) == original_length
    
    def test_secure_wipe_bytes(self):
        """Test secure wiping of bytes (converted to bytearray)."""
        test_data = b"secret_data_12345"
        
        # This should not raise an exception
        SecureMemoryHandler.secure_wipe(test_data)
    
    def test_secure_load_private_key_context_manager(self):
        """Test the secure private key context manager."""
        # Generate a test key pair
        private_key = ec.generate_private_key(ec.SECP256R1())
        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        # Test the context manager
        with SecureMemoryHandler.secure_load_private_key(private_key_pem) as key_obj:
            assert key_obj is not None
            assert isinstance(key_obj, ec.EllipticCurvePrivateKey)
            
            # Test that we can get the public key
            public_key = key_obj.public_key()
            assert isinstance(public_key, ec.EllipticCurvePublicKey)
        
        # Key should be cleaned up after context exit
        # (We can't directly test memory wiping, but we can test the context manager works)


class TestTransactionSigner:
    """Test suite for TransactionSigner."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.signer = TransactionSigner()
        # Generate test key pair
        self.private_key_pem, self.public_key_pem = self.signer.generate_key_pair()
        
        # Create test transaction data
        self.test_transaction_data = {
            "sender": "test_sender",
            "recipient": "test_recipient",
            "nonce": 1,
            "timestamp": datetime.now().isoformat(),
            "value": [{"amount": 100, "type": "coin"}]
        }
        
        # Create deterministic transaction bytes
        transaction_json = json.dumps(self.test_transaction_data, sort_keys=True, separators=(',', ':'))
        self.transaction_bytes = transaction_json.encode('utf-8')
    
    def test_generate_key_pair(self):
        """Test key pair generation."""
        private_key_pem, public_key_pem = self.signer.generate_key_pair()
        
        assert isinstance(private_key_pem, bytes)
        assert isinstance(public_key_pem, bytes)
        assert len(private_key_pem) > 0
        assert len(public_key_pem) > 0
        
        # Verify keys are different each time
        private_key_pem2, public_key_pem2 = self.signer.generate_key_pair()
        assert private_key_pem != private_key_pem2
        assert public_key_pem != public_key_pem2
    
    def test_sign_transaction_data(self):
        """Test transaction data signing."""
        signature = self.signer.sign_transaction_data(
            self.transaction_bytes,
            self.private_key_pem
        )
        
        assert isinstance(signature, bytes)
        assert len(signature) > 0
        
        # Note: ECDSA signatures may have slight variations due to random k value
        # This is actually a security feature (deterministic k is better but not always used)
        # The important thing is that both signatures verify correctly
        signature2 = self.signer.sign_transaction_data(
            self.transaction_bytes,
            self.private_key_pem
        )
        
        # Both signatures should verify correctly
        assert self.signer.verify_signature(
            self.transaction_bytes,
            signature,
            self.public_key_pem
        ) is True
        
        assert self.signer.verify_signature(
            self.transaction_bytes,
            signature2,
            self.public_key_pem
        ) is True
    
    def test_sign_empty_data(self):
        """Test signing empty data should raise error."""
        with pytest.raises(ValueError, match="Transaction data cannot be empty"):
            self.signer.sign_transaction_data(b"", self.private_key_pem)
    
    def test_sign_with_empty_private_key(self):
        """Test signing with empty private key should raise error."""
        with pytest.raises(ValueError, match="Private key cannot be empty"):
            self.signer.sign_transaction_data(self.transaction_bytes, b"")
    
    def test_verify_signature_valid(self):
        """Test signature verification with valid signature."""
        # Sign the data
        signature = self.signer.sign_transaction_data(
            self.transaction_bytes,
            self.private_key_pem
        )
        
        # Verify the signature
        is_valid = self.signer.verify_signature(
            self.transaction_bytes,
            signature,
            self.public_key_pem
        )
        
        assert is_valid is True
    
    def test_verify_signature_invalid(self):
        """Test signature verification with invalid signature."""
        invalid_signature = b"invalid_signature_data"
        
        is_valid = self.signer.verify_signature(
            self.transaction_bytes,
            invalid_signature,
            self.public_key_pem
        )
        
        assert is_valid is False
    
    def test_verify_signature_wrong_public_key(self):
        """Test signature verification with wrong public key."""
        # Generate a different key pair
        wrong_private_key_pem, wrong_public_key_pem = self.signer.generate_key_pair()
        
        # Sign with original key
        signature = self.signer.sign_transaction_data(
            self.transaction_bytes,
            self.private_key_pem
        )
        
        # Verify with wrong public key
        is_valid = self.signer.verify_signature(
            self.transaction_bytes,
            signature,
            wrong_public_key_pem
        )
        
        assert is_valid is False
    
    def test_verify_signature_tampered_data(self):
        """Test signature verification with tampered data."""
        # Sign the data
        signature = self.signer.sign_transaction_data(
            self.transaction_bytes,
            self.private_key_pem
        )
        
        # Tamper with the data
        tampered_data = self.transaction_bytes + b"tampered"
        
        # Verify should fail
        is_valid = self.signer.verify_signature(
            tampered_data,
            signature,
            self.public_key_pem
        )
        
        assert is_valid is False
    
    def test_verify_signature_empty_inputs(self):
        """Test signature verification with empty inputs."""
        # Test with empty transaction data
        is_valid = self.signer.verify_signature(
            b"",
            b"signature",
            self.public_key_pem
        )
        assert is_valid is False
        
        # Test with empty signature
        is_valid = self.signer.verify_signature(
            self.transaction_bytes,
            b"",
            self.public_key_pem
        )
        assert is_valid is False
        
        # Test with empty public key
        is_valid = self.signer.verify_signature(
            self.transaction_bytes,
            b"signature",
            b""
        )
        assert is_valid is False


class TestSecureTransactionSignature:
    """Test suite for SecureTransactionSignature."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.secure_signer = SecureTransactionSignature()
        self.signer = TransactionSigner()
        # Generate test key pair
        self.private_key_pem, self.public_key_pem = self.signer.generate_key_pair()
    
    def test_sign_transaction(self):
        """Test complete transaction signing."""
        result = self.secure_signer.sign_transaction(
            sender="test_sender",
            recipient="test_recipient",
            nonce=1,
            value_data=[{"amount": 100, "type": "coin"}],
            private_key_pem=self.private_key_pem
        )
        
        # Verify result structure
        assert "transaction_data" in result
        assert "transaction_hash" in result
        assert "signature" in result
        assert "timestamp" in result
        
        # Verify data types
        assert isinstance(result["transaction_data"], dict)
        assert isinstance(result["transaction_hash"], str)
        assert isinstance(result["signature"], str)
        assert isinstance(result["timestamp"], str)
        
        # Verify transaction data
        assert result["transaction_data"]["sender"] == "test_sender"
        assert result["transaction_data"]["recipient"] == "test_recipient"
        assert result["transaction_data"]["nonce"] == 1
        assert result["transaction_data"]["value"] == [{"amount": 100, "type": "coin"}]
    
    def test_sign_transaction_with_custom_timestamp(self):
        """Test transaction signing with custom timestamp."""
        custom_timestamp = "2023-01-01T00:00:00"
        
        result = self.secure_signer.sign_transaction(
            sender="test_sender",
            recipient="test_recipient",
            nonce=1,
            value_data=[{"amount": 100, "type": "coin"}],
            private_key_pem=self.private_key_pem,
            timestamp=custom_timestamp
        )
        
        assert result["transaction_data"]["timestamp"] == custom_timestamp
        assert result["timestamp"] == custom_timestamp
    
    def test_verify_transaction_signature_valid(self):
        """Test transaction signature verification with valid signature."""
        # Sign a transaction
        result = self.secure_signer.sign_transaction(
            sender="test_sender",
            recipient="test_recipient",
            nonce=1,
            value_data=[{"amount": 100, "type": "coin"}],
            private_key_pem=self.private_key_pem
        )
        
        # Verify the signature
        is_valid = self.secure_signer.verify_transaction_signature(
            transaction_data=result["transaction_data"],
            signature_hex=result["signature"],
            public_key_pem=self.public_key_pem
        )
        
        assert is_valid is True
    
    def test_verify_transaction_signature_invalid(self):
        """Test transaction signature verification with invalid signature."""
        transaction_data = {
            "sender": "test_sender",
            "recipient": "test_recipient",
            "nonce": 1,
            "timestamp": datetime.now().isoformat(),
            "value": [{"amount": 100, "type": "coin"}]
        }
        
        # Test with invalid signature
        is_valid = self.secure_signer.verify_transaction_signature(
            transaction_data=transaction_data,
            signature_hex="invalid_signature_hex",
            public_key_pem=self.public_key_pem
        )
        
        assert is_valid is False
    
    def test_security_warnings(self):
        """Test security warnings functionality."""
        # Test that warnings are enabled by default
        assert self.secure_signer._security_warnings_enabled is True
        
        # Disable warnings
        self.secure_signer.disable_security_warnings()
        assert self.secure_signer._security_warnings_enabled is False
        
        # Enable warnings
        self.secure_signer.enable_security_warnings()
        assert self.secure_signer._security_warnings_enabled is True


class TestIntegration:
    """Integration tests for the complete secure signature system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.private_key_pem, self.public_key_pem = secure_signature_handler.signer.generate_key_pair()
    
    def test_end_to_end_transaction_signing(self):
        """Test complete end-to-end transaction signing and verification."""
        # Step 1: Sign a transaction
        transaction_result = secure_signature_handler.sign_transaction(
            sender="alice",
            recipient="bob",
            nonce=123,
            value_data=[
                {"amount": 50, "type": "gold"},
                {"amount": 25, "type": "silver"}
            ],
            private_key_pem=self.private_key_pem
        )
        
        # Step 2: Verify the transaction signature
        is_valid = secure_signature_handler.verify_transaction_signature(
            transaction_data=transaction_result["transaction_data"],
            signature_hex=transaction_result["signature"],
            public_key_pem=self.public_key_pem
        )
        
        # Step 3: Assert the signature is valid
        assert is_valid is True
        
        # Step 4: Verify transaction hash is correct
        expected_hash = hashlib.sha256(
            json.dumps(transaction_result["transaction_data"], sort_keys=True, separators=(',', ':'))
            .encode('utf-8')
        ).hexdigest()
        assert transaction_result["transaction_hash"] == expected_hash
    
    def test_multiple_transactions_same_key(self):
        """Test signing multiple transactions with the same key."""
        transactions = []
        
        # Create multiple transactions
        for i in range(5):
            result = secure_signature_handler.sign_transaction(
                sender="alice",
                recipient=f"recipient_{i}",
                nonce=i,
                value_data=[{"amount": i * 10, "type": "coin"}],
                private_key_pem=self.private_key_pem
            )
            transactions.append(result)
        
        # Verify all signatures
        for i, transaction in enumerate(transactions):
            is_valid = secure_signature_handler.verify_transaction_signature(
                transaction_data=transaction["transaction_data"],
                signature_hex=transaction["signature"],
                public_key_pem=self.public_key_pem
            )
            assert is_valid is True
            
            # Verify transaction data integrity
            assert transaction["transaction_data"]["nonce"] == i
            assert transaction["transaction_data"]["recipient"] == f"recipient_{i}"
    
    def test_signature_uniqueness(self):
        """Test that different transactions produce different signatures."""
        # Sign two different transactions
        result1 = secure_signature_handler.sign_transaction(
            sender="alice",
            recipient="bob",
            nonce=1,
            value_data=[{"amount": 100, "type": "coin"}],
            private_key_pem=self.private_key_pem
        )
        
        result2 = secure_signature_handler.sign_transaction(
            sender="alice",
            recipient="charlie",
            nonce=2,
            value_data=[{"amount": 200, "type": "coin"}],
            private_key_pem=self.private_key_pem
        )
        
        # Signatures should be different
        assert result1["signature"] != result2["signature"]
        
        # Both should be valid
        assert secure_signature_handler.verify_transaction_signature(
            transaction_data=result1["transaction_data"],
            signature_hex=result1["signature"],
            public_key_pem=self.public_key_pem
        ) is True
        
        assert secure_signature_handler.verify_transaction_signature(
            transaction_data=result2["transaction_data"],
            signature_hex=result2["signature"],
            public_key_pem=self.public_key_pem
        ) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])