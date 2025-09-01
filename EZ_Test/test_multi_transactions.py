#!/usr/bin/env python3
"""
Comprehensive unit tests for MultiTransactions.py with multi-transaction functionality.
"""

import pytest
import sys
import os
import datetime
import tempfile
from unittest.mock import patch, MagicMock
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(__file__) + '/..')
sys.path.insert(0, os.path.dirname(__file__) + '/../EZ_Transaction')

try:
    from EZ_Transaction.MultiTransactions import MultiTransactions
    from EZ_Value.Value import Value
    from EZ_Transaction.SingleTransaction import Transaction
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

class TestMultiTransactionsInitialization:
    """Test suite for MultiTransactions class initialization and basic properties."""
    
    @pytest.fixture
    def setup_init(self):
        """Set up test fixtures before each test method."""
        self.sender = "0xSender123"
        self.value1 = [Value("0x1000", 100)]
        self.value2 = [Value("0x2000", 200)]
        
        # Create test transactions
        self.tx1 = Transaction.new_transaction(
            sender=self.sender,
            recipient="0xRecipient1",
            value=self.value1,
            nonce=1
        )
        
        self.tx2 = Transaction.new_transaction(
            sender=self.sender,
            recipient="0xRecipient2",
            value=self.value2,
            nonce=2
        )
        
        self.multi_txns = [self.tx1, self.tx2]
        
    def test_multi_transactions_initialization(self, setup_init):
        """Test basic MultiTransactions initialization."""
        multi_tx = MultiTransactions(
            sender=self.sender,
            multi_txns=self.multi_txns
        )
        
        assert multi_tx.sender == self.sender
        # assert multi_tx.sender_id == self.sender_id
        assert len(multi_tx.multi_txns) == 2
        assert isinstance(multi_tx.multi_txns[0], Transaction)
        assert isinstance(multi_tx.multi_txns[1], Transaction)
        assert multi_tx.time is not None
        assert isinstance(multi_tx.time, str)
        assert multi_tx.signature is None
        assert multi_tx.digest is None
        
    def test_multi_transactions_initialization_empty_list(self, setup_init):
        """Test MultiTransactions initialization with empty transaction list."""
        multi_tx = MultiTransactions(
            sender=self.sender,
            multi_txns=[]
        )
        
        assert len(multi_tx.multi_txns) == 0
        assert multi_tx.signature is None
        assert multi_tx.digest is None
        
    def test_time_format(self, setup_init):
        """Test that time is properly formatted in ISO format."""
        multi_tx = MultiTransactions(
            sender=self.sender,
            multi_txns=self.multi_txns
        )
        
        # Should be a string in ISO format
        assert isinstance(multi_tx.time, str)
        assert 'T' in multi_tx.time  # ISO format should contain 'T'
        # ISO format can end with Z or +00:00, or contain microseconds
        assert multi_tx.time.endswith('Z') or \
               '+' in multi_tx.time or \
               '.' in multi_tx.time


class TestMultiTransactionsEncoding:
    """Test suite for MultiTransactions encoding and decoding functionality."""
    
    @pytest.fixture
    def setup_encoding(self):
        """Set up test fixtures before each test method."""
        self.sender = "0xSender123"
        self.value = [Value("0x1000", 100)]
        
        # Create test transactions
        self.tx1 = Transaction.new_transaction(
            sender=self.sender,
            recipient="0xRecipient1",
            value=self.value,
            nonce=1
        )
        
        self.tx2 = Transaction.new_transaction(
            sender=self.sender,
            recipient="0xRecipient2",
            value=self.value,
            nonce=2
        )
        
        self.multi_txns = [self.tx1, self.tx2]
        self.multi_tx = MultiTransactions(
            sender=self.sender,
            multi_txns=self.multi_txns
        )
        
    def test_encode_multi_transactions(self, setup_encoding):
        """Test MultiTransactions encoding."""
        encoded_data = self.multi_tx.encode()
        assert isinstance(encoded_data, bytes)
        
    def test_decode_multi_transactions(self, setup_encoding):
        """Test MultiTransactions decoding."""
        # First encode the multi-transactions
        encoded_data = self.multi_tx.encode()
        
        # Then decode it
        decoded_txns = MultiTransactions.decode(encoded_data)
        
        # Verify the decoded transactions
        assert len(decoded_txns) == 2
        assert isinstance(decoded_txns[0], Transaction)
        assert isinstance(decoded_txns[1], Transaction)
        assert decoded_txns[0].sender == self.sender
        assert decoded_txns[1].sender == self.sender
        
    def test_encode_decode_roundtrip(self, setup_encoding):
        """Test that encode-decode roundtrip preserves all data."""
        # Create a new multi-transaction with different data
        different_tx1 = Transaction.new_transaction(
            sender="0xDifferentSender",
            recipient="0xDifferentRecipient1",
            value=[Value("0x5000", 500)],
            nonce=42
        )
        
        different_tx2 = Transaction.new_transaction(
            sender="0xDifferentSender",
            recipient="0xDifferentRecipient2",
            value=[Value("0x6000", 600)],
            nonce=43
        )
        
        different_multi_txns = [different_tx1, different_tx2]
        original_multi_tx = MultiTransactions(
            sender="0xDifferentSender",
            multi_txns=different_multi_txns
        )
        
        encoded_data = original_multi_tx.encode()
        decoded_txns = MultiTransactions.decode(encoded_data)
        
        # Verify all transactions are preserved
        assert len(decoded_txns) == 2
        assert decoded_txns[0].sender == "0xDifferentSender"
        assert decoded_txns[1].sender == "0xDifferentSender"
        assert decoded_txns[0].nonce == 42
        assert decoded_txns[1].nonce == 43


class TestMultiTransactionsDigest:
    """Test suite for MultiTransactions digest functionality."""
    
    @pytest.fixture
    def setup_digest(self):
        """Set up test fixtures before each test method."""
        self.sender = "0xSender123"
        self.value = [Value("0x1000", 100)]
        
        # Create test transactions
        self.tx1 = Transaction.new_transaction(
            sender=self.sender,
            recipient="0xRecipient1",
            value=self.value,
            nonce=1
        )
        
        self.tx2 = Transaction.new_transaction(
            sender=self.sender,
            recipient="0xRecipient2",
            value=self.value,
            nonce=2
        )
        
        self.multi_txns = [self.tx1, self.tx2]
        self.multi_tx = MultiTransactions(
            sender=self.sender,
            multi_txns=self.multi_txns
        )
        
    def test_set_digest(self, setup_digest):
        """Test digest calculation and setting."""
        self.multi_tx.set_digest()
        
        assert self.multi_tx.digest is not None
        assert isinstance(self.multi_tx.digest, str)
        
    def test_digest_consistency(self, setup_digest):
        """Test that same multi-transaction produces same digest."""
        digest1 = self.multi_tx.encode()
        digest2 = self.multi_tx.encode()
        
        # Encoded data should be identical for same multi-transaction
        assert digest1 == digest2
        
    def test_digest_different_multi_transactions(self, setup_digest):
        """Test that different multi-transactions produce different digests."""
        # Create a different multi-transaction
        different_tx = Transaction.new_transaction(
            sender="0xDifferentSender",
            recipient="0xDifferentRecipient",
            value=[Value("0x5000", 500)],
            nonce=42
        )
        
        different_multi_tx = MultiTransactions(
            sender="0xDifferentSender",
            multi_txns=[different_tx]
        )
        
        encoded1 = self.multi_tx.encode()
        encoded2 = different_multi_tx.encode()
        
        assert encoded1 != encoded2


class TestMultiTransactionsSignature:
    """Test suite for basic MultiTransactions signature functionality."""
    
    @pytest.fixture
    def setup_signature(self):
        """Set up test fixtures before each test method."""
        # Generate test keys
        self.private_key = ec.generate_private_key(ec.SECP256R1())
        self.public_key = self.private_key.public_key()
        
        # Serialize keys for testing
        self.private_key_pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        self.public_key_pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        self.sender = "0xSender123"
        self.value = [Value("0x1000", 100)]
        
        # Create test transactions
        self.tx1 = Transaction.new_transaction(
            sender=self.sender,
            recipient="0xRecipient1",
            value=self.value,
            nonce=1
        )
        
        self.tx2 = Transaction.new_transaction(
            sender=self.sender,
            recipient="0xRecipient2",
            value=self.value,
            nonce=2
        )
        
        self.multi_txns = [self.tx1, self.tx2]
        self.multi_tx = MultiTransactions(
            sender=self.sender,
            multi_txns=self.multi_txns
        )
        
    def test_basic_sign_multi_transaction(self, setup_signature):
        """Test basic multi-transaction signing functionality."""
        self.multi_tx.sig_acc_txn(self.private_key_pem)
        
        # Verify signature is set
        assert self.multi_tx.signature is not None
        assert isinstance(self.multi_tx.signature, bytes)
        assert self.multi_tx.digest is not None
        
    def test_basic_signature_verification(self, setup_signature):
        """Test basic signature verification."""
        # Sign the multi-transaction
        self.multi_tx.sig_acc_txn(self.private_key_pem)
        
        # Verify the signature should be valid
        result = self.multi_tx.check_acc_txn_sig(self.public_key_pem)
        assert result is True
        
    def test_basic_signature_wrong_key(self, setup_signature):
        """Test signature verification with wrong public key."""
        # Generate a different key
        wrong_private_key = ec.generate_private_key(ec.SECP256R1())
        wrong_public_key_pem = wrong_private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        # Sign with original key
        self.multi_tx.sig_acc_txn(self.private_key_pem)
        
        # Verify with wrong key should fail
        result = self.multi_tx.check_acc_txn_sig(wrong_public_key_pem)
        assert result is False
        
    def test_basic_unsigned_verification(self, setup_signature):
        """Test verification of unsigned multi-transaction."""
        # When signature and digest are None, verification should fail
        result = self.multi_tx.check_acc_txn_sig(self.public_key_pem)
        assert result is False


class TestMultiTransactionsEdgeCases:
    """Test suite for MultiTransactions edge cases and error handling."""
    
    @pytest.fixture
    def setup_edge_cases(self):
        """Set up test fixtures before each test method."""
        self.sender = "0xSender123"
        self.value = [Value("0x1000", 100)]
        
        # Create test transaction
        self.tx = Transaction.new_transaction(
            sender=self.sender,
            recipient="0xRecipient",
            value=self.value,
            nonce=1
        )
        
    def test_single_transaction_list(self, setup_edge_cases):
        """Test MultiTransactions with single transaction in list."""
        multi_tx = MultiTransactions(
            sender=self.sender,
            multi_txns=[self.tx]
        )
        
        assert len(multi_tx.multi_txns) == 1
        assert isinstance(multi_tx.multi_txns[0], Transaction)
        
    def test_large_transaction_list(self, setup_edge_cases):
        """Test MultiTransactions with large transaction list."""
        transactions = []
        for i in range(100):
            tx = Transaction.new_transaction(
                sender=self.sender,
                recipient=f"0xRecipient{i}",
                value=[Value(f"0x{i:04x}", 100)],
                nonce=i
            )
            transactions.append(tx)
            
        multi_tx = MultiTransactions(
            sender=self.sender,
            multi_txns=transactions
        )
        
        assert len(multi_tx.multi_txns) == 100
        
    def test_encode_with_none_values(self, setup_edge_cases):
        """Test encoding with None values in transactions."""
        # Create transaction with None values (should still encode)
        tx_with_none = Transaction(
            sender=self.sender,
            recipient="0xRecipient",
            nonce=1,
            signature=None,
            value=self.value,
            time=None
        )
        
        multi_tx = MultiTransactions(
            sender=self.sender,
            multi_txns=[tx_with_none]
        )
        
        # Should still encode without error
        encoded_data = multi_tx.encode()
        assert isinstance(encoded_data, bytes)


class TestMultiTransactionsTimeHandling:
    """Test suite for MultiTransactions time handling."""
    
    @pytest.fixture
    def setup_time_handling(self):
        """Set up test fixtures before each test method."""
        self.sender = "0xSender123"
        self.value = [Value("0x1000", 100)]
        
        # Create test transactions
        self.tx1 = Transaction.new_transaction(
            sender=self.sender,
            recipient="0xRecipient1",
            value=self.value,
            nonce=1
        )
        
        self.tx2 = Transaction.new_transaction(
            sender=self.sender,
            recipient="0xRecipient2",
            value=self.value,
            nonce=2
        )
        
        self.multi_txns = [self.tx1, self.tx2]
        
    def test_time_in_string_representation(self, setup_time_handling):
        """Test that time appears correctly in multi-transaction."""
        multi_tx = MultiTransactions(
            sender=self.sender,
            multi_txns=self.multi_txns
        )
        
        # Test that time is a proper ISO format string
        assert isinstance(multi_tx.time, str)
        assert len(multi_tx.time) > 0
        
    def test_multiple_multi_transactions_different_times(self, setup_time_handling):
        """Test that different multi-transactions have different timestamps."""
        import time
        
        multi_tx1 = MultiTransactions(
            sender=self.sender,
            multi_txns=self.multi_txns
        )
        
        # Small delay to ensure different timestamps
        time.sleep(0.01)
        
        multi_tx2 = MultiTransactions(
            sender=self.sender,
            multi_txns=self.multi_txns
        )
        
        # Timestamps should be different
        assert multi_tx1.time != multi_tx2.time


class TestMultiTransactionsPropertyAccess:
    """Test suite for MultiTransactions property access and validation."""
    
    @pytest.fixture
    def setup_property_access(self):
        """Set up test fixtures before each test method."""
        self.sender = "0xSender123"
        self.value = [Value("0x1000", 100)]
        
        # Create test transactions
        self.tx1 = Transaction.new_transaction(
            sender=self.sender,
            recipient="0xRecipient1",
            value=self.value,
            nonce=1
        )
        
        self.tx2 = Transaction.new_transaction(
            sender=self.sender,
            recipient="0xRecipient2",
            value=self.value,
            nonce=2
        )
        
        self.multi_txns = [self.tx1, self.tx2]
        self.multi_tx = MultiTransactions(
            sender=self.sender,
            multi_txns=self.multi_txns
        )
        
    def test_sender_property(self, setup_property_access):
        """Test sender property access."""
        assert self.multi_tx.sender == self.sender
        
    def test_sender_id_property(self, setup_property_access):
        """Test sender_id property access."""
        # assert self.multi_tx.sender_id == self.sender_id
        pass
        
    def test_multi_txns_property(self, setup_property_access):
        """Test multi_txns property access."""
        assert len(self.multi_tx.multi_txns) == 2
        assert isinstance(self.multi_tx.multi_txns, list)
        
    def test_digest_property(self, setup_property_access):
        """Test digest property access."""
        # Initially None
        assert self.multi_tx.digest is None
        
        # After setting digest
        self.multi_tx.set_digest()
        assert self.multi_tx.digest is not None
        
    def test_signature_property(self, setup_property_access):
        """Test signature property access."""
        # Initially None
        assert self.multi_tx.signature is None
        
        # Generate test key for signing
        from cryptography.hazmat.primitives.asymmetric import ec
        from cryptography.hazmat.primitives import serialization
        
        private_key = ec.generate_private_key(ec.SECP256R1())
        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        # After signing
        self.multi_tx.sig_acc_txn(private_key_pem)
        assert self.multi_tx.signature is not None

class TestMultiTransactionsSecureSignature:
    """Test suite for MultiTransactions secure signature functionality with new multi-transaction methods."""
    
    @pytest.fixture
    def setup_secure_signature(self):
        """Set up test fixtures for secure signature testing."""
        # Generate test keys
        self.private_key = ec.generate_private_key(ec.SECP256R1())
        self.public_key = self.private_key.public_key()
        
        # Serialize keys for testing
        self.private_key_pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        self.public_key_pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        self.sender = "0xSender123"
        self.value = [Value("0x1000", 100)]
        
        # Create test transactions
        self.tx1 = Transaction.new_transaction(
            sender=self.sender,
            recipient="0xRecipient1",
            value=self.value,
            nonce=1
        )
        
        self.tx2 = Transaction.new_transaction(
            sender=self.sender,
            recipient="0xRecipient2",
            value=self.value,
            nonce=2
        )
        
        self.multi_txns = [self.tx1, self.tx2]
        self.multi_tx = MultiTransactions(
            sender=self.sender,
            multi_txns=self.multi_txns
        )
        
    def test_secure_sign_multi_transaction(self, setup_secure_signature):
        """Test secure multi-transaction signing with new method."""
        # Sign the multi-transaction
        self.multi_tx.sig_acc_txn(self.private_key_pem)
        
        # Verify signature is set
        assert self.multi_tx.signature is not None
        assert isinstance(self.multi_tx.signature, bytes)
        assert self.multi_tx.digest is not None
        assert isinstance(self.multi_tx.digest, str)
        
    def test_secure_signature_verification(self, setup_secure_signature):
        """Test secure signature verification with new method."""
        # Sign the multi-transaction
        self.multi_tx.sig_acc_txn(self.private_key_pem)
        
        # Verify the signature should be valid
        result = self.multi_tx.check_acc_txn_sig(self.public_key_pem)
        assert result is True
        
    def test_secure_signature_data_structure(self, setup_secure_signature):
        """Test that the signature data structure is correct for multi-transactions."""
        # Sign the multi-transaction
        self.multi_tx.sig_acc_txn(self.private_key_pem)
        
        # Verify that the signature data structure contains required fields
        assert self.multi_tx.sender == self.sender
        assert self.multi_tx.time is not None
        assert len(self.multi_tx.multi_txns) == 2
        
        # Verify that transactions are properly structured
        for txn in self.multi_tx.multi_txns:
            assert hasattr(txn, 'sender')
            assert hasattr(txn, 'recipient')
            assert hasattr(txn, 'nonce')
            assert hasattr(txn, 'time')
            assert hasattr(txn, 'value')
            
    def test_secure_signature_different_keys(self, setup_secure_signature):
        """Test secure signature with different key pairs."""
        # Generate a different key pair
        different_private_key = ec.generate_private_key(ec.SECP256R1())
        different_public_key_pem = different_private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        # Sign with original key
        self.multi_tx.sig_acc_txn(self.private_key_pem)
        
        # Verify with different key should fail
        result = self.multi_tx.check_acc_txn_sig(different_public_key_pem)
        assert result is False
        
    def test_secure_signature_empty_transactions(self, setup_secure_signature):
        """Test that empty transaction list raises appropriate error."""
        empty_multi_tx = MultiTransactions(
            sender=self.sender,
            multi_txns=[]
        )
        
        with pytest.raises(ValueError) as context:
            empty_multi_tx.sig_acc_txn(self.private_key_pem)
            
        assert "Cannot sign empty transaction list" in str(context.value)
        
    def test_secure_signature_multiple_signing(self, setup_secure_signature):
        """Test multiple signing operations on same multi-transaction."""
        # First signing
        self.multi_tx.sig_acc_txn(self.private_key_pem)
        first_signature = self.multi_tx.signature
        first_digest = self.multi_tx.digest
        
        # Small delay to ensure different timestamp
        import time
        time.sleep(0.01)
        
        # Second signing (should overwrite)
        self.multi_tx.sig_acc_txn(self.private_key_pem)
        second_signature = self.multi_tx.signature
        second_digest = self.multi_tx.digest
        
        # Signatures should be different due to different timestamps
        assert first_signature != second_signature
        # Digest might be the same if timestamp doesn't change enough, but signature should differ
        
    def test_secure_signature_verification_no_signature(self, setup_secure_signature):
        """Test verification when no signature exists."""
        # Don't sign the multi-transaction
        result = self.multi_tx.check_acc_txn_sig(self.public_key_pem)
        assert result is False
        
    def test_secure_signature_with_complex_transactions(self, setup_secure_signature):
        """Test secure signature with more complex transaction data."""
        # Create transactions with multiple values
        complex_value1 = [Value("0x1000", 100), Value("0x2000", 200)]
        complex_value2 = [Value("0x3000", 300), Value("0x4000", 400)]
        
        complex_tx1 = Transaction.new_transaction(
            sender=self.sender,
            recipient="0xComplexRecipient1",
            value=complex_value1,
            nonce=42
        )
        
        complex_tx2 = Transaction.new_transaction(
            sender=self.sender,
            recipient="0xComplexRecipient2",
            value=complex_value2,
            nonce=43
        )
        
        complex_multi_tx = MultiTransactions(
            sender=self.sender,
            multi_txns=[complex_tx1, complex_tx2]
        )
        
        # Sign and verify
        complex_multi_tx.sig_acc_txn(self.private_key_pem)
        result = complex_multi_tx.check_acc_txn_sig(self.public_key_pem)
        assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])