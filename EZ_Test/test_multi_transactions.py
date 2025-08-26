#!/usr/bin/env python3
"""
Comprehensive unit tests for MultiTransactions.py with multi-transaction functionality.
"""

import unittest
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

class TestMultiTransactionsInitialization(unittest.TestCase):
    """Test suite for MultiTransactions class initialization and basic properties."""
    
    def setUp(self):
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
        
    def test_multi_transactions_initialization(self):
        """Test basic MultiTransactions initialization."""
        multi_tx = MultiTransactions(
            sender=self.sender,
            multi_txns=self.multi_txns
        )
        
        self.assertEqual(multi_tx.sender, self.sender)
        self.assertEqual(len(multi_tx.multi_txns), 2)
        self.assertIsInstance(multi_tx.multi_txns[0], Transaction)
        self.assertIsInstance(multi_tx.multi_txns[1], Transaction)
        self.assertIsNotNone(multi_tx.time)
        self.assertIsInstance(multi_tx.time, str)
        self.assertIsNone(multi_tx.signature)
        self.assertIsNone(multi_tx.digest)
        
    def test_multi_transactions_initialization_empty_list(self):
        """Test MultiTransactions initialization with empty transaction list."""
        multi_tx = MultiTransactions(
            sender=self.sender,
            multi_txns=[]
        )
        
        self.assertEqual(len(multi_tx.multi_txns), 0)
        self.assertIsNone(multi_tx.signature)
        self.assertIsNone(multi_tx.digest)
        
    def test_time_format(self):
        """Test that time is properly formatted in ISO format."""
        multi_tx = MultiTransactions(
            sender=self.sender,
            multi_txns=self.multi_txns
        )
        
        # Should be a string in ISO format
        self.assertIsInstance(multi_tx.time, str)
        self.assertIn('T', multi_tx.time)  # ISO format should contain 'T'
        # ISO format can end with Z or +00:00, or contain microseconds
        self.assertTrue(multi_tx.time.endswith('Z') or 
                       '+' in multi_tx.time or 
                       '.' in multi_tx.time)


class TestMultiTransactionsEncoding(unittest.TestCase):
    """Test suite for MultiTransactions encoding and decoding functionality."""
    
    def setUp(self):
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
        
    def test_encode_multi_transactions(self):
        """Test MultiTransactions encoding."""
        encoded_data = self.multi_tx.encode()
        self.assertIsInstance(encoded_data, bytes)
        
    def test_decode_multi_transactions(self):
        """Test MultiTransactions decoding."""
        # First encode the multi-transactions
        encoded_data = self.multi_tx.encode()
        
        # Then decode it
        decoded_txns = MultiTransactions.decode(encoded_data)
        
        # Verify the decoded transactions
        self.assertEqual(len(decoded_txns), 2)
        self.assertIsInstance(decoded_txns[0], Transaction)
        self.assertIsInstance(decoded_txns[1], Transaction)
        self.assertEqual(decoded_txns[0].sender, self.sender)
        self.assertEqual(decoded_txns[1].sender, self.sender)
        
    def test_encode_decode_roundtrip(self):
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
        self.assertEqual(len(decoded_txns), 2)
        self.assertEqual(decoded_txns[0].sender, "0xDifferentSender")
        self.assertEqual(decoded_txns[1].sender, "0xDifferentSender")
        self.assertEqual(decoded_txns[0].nonce, 42)
        self.assertEqual(decoded_txns[1].nonce, 43)


class TestMultiTransactionsDigest(unittest.TestCase):
    """Test suite for MultiTransactions digest functionality."""
    
    def setUp(self):
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
        
    def test_set_digest(self):
        """Test digest calculation and setting."""
        self.multi_tx.set_digest()
        
        self.assertIsNotNone(self.multi_tx.digest)
        self.assertIsInstance(self.multi_tx.digest, str)
        
    def test_digest_consistency(self):
        """Test that same multi-transaction produces same digest."""
        digest1 = self.multi_tx.encode()
        digest2 = self.multi_tx.encode()
        
        # Encoded data should be identical for same multi-transaction
        self.assertEqual(digest1, digest2)
        
    def test_digest_different_multi_transactions(self):
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
        
        self.assertNotEqual(encoded1, encoded2)


class TestMultiTransactionsSignature(unittest.TestCase):
    """Test suite for MultiTransactions signature functionality."""
    
    def setUp(self):
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
        
    def test_sign_multi_transaction(self):
        """Test multi-transaction signing."""
        self.multi_tx.sig_acc_txn(self.private_key_pem)
        
        # Verify signature is set
        self.assertIsNotNone(self.multi_tx.signature)
        self.assertIsInstance(self.multi_tx.signature, bytes)
        self.assertIsNotNone(self.multi_tx.digest)
        
    def test_signature_verification(self):
        """Test signature verification."""
        # Sign the multi-transaction
        self.multi_tx.sig_acc_txn(self.private_key_pem)
        
        # Verify the signature should be valid
        result = self.multi_tx.check_acc_txn_sig(self.public_key_pem)
        self.assertTrue(result)
        
    def test_signature_verification_wrong_key(self):
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
        self.assertFalse(result)
        
    def test_unsigned_multi_transaction_verification(self):
        """Test verification of unsigned multi-transaction."""
        # When signature and digest are None, verification should fail
        result = self.multi_tx.check_acc_txn_sig(self.public_key_pem)
        self.assertFalse(result)
        
    def test_sign_empty_transaction_list(self):
        """Test signing empty transaction list should raise error."""
        empty_multi_tx = MultiTransactions(
            sender=self.sender,
            multi_txns=[]
        )
        
        with self.assertRaises(ValueError) as context:
            empty_multi_tx.sig_acc_txn(self.private_key_pem)
            
        self.assertIn("Cannot sign empty transaction list", str(context.exception))


class TestMultiTransactionsEdgeCases(unittest.TestCase):
    """Test suite for MultiTransactions edge cases and error handling."""
    
    def setUp(self):
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
        
    def test_single_transaction_list(self):
        """Test MultiTransactions with single transaction in list."""
        multi_tx = MultiTransactions(
            sender=self.sender,
            multi_txns=[self.tx]
        )
        
        self.assertEqual(len(multi_tx.multi_txns), 1)
        self.assertIsInstance(multi_tx.multi_txns[0], Transaction)
        
    def test_large_transaction_list(self):
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
        
        self.assertEqual(len(multi_tx.multi_txns), 100)
        
    def test_encode_with_none_values(self):
        """Test encoding with None values in transactions."""
        # Create transaction with None values (should still encode)
        tx_with_none = Transaction(
            sender=self.sender,
            recipient="0xRecipient",
            nonce=1,
            signature=None,
            value=self.value,
            tx_hash=None,
            time=None
        )
        
        multi_tx = MultiTransactions(
            sender=self.sender,
            multi_txns=[tx_with_none]
        )
        
        # Should still encode without error
        encoded_data = multi_tx.encode()
        self.assertIsInstance(encoded_data, bytes)


class TestMultiTransactionsTimeHandling(unittest.TestCase):
    """Test suite for MultiTransactions time handling."""
    
    def setUp(self):
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
        
    def test_time_in_string_representation(self):
        """Test that time appears correctly in multi-transaction."""
        multi_tx = MultiTransactions(
            sender=self.sender,
            multi_txns=self.multi_txns
        )
        
        # Test that time is a proper ISO format string
        self.assertIsInstance(multi_tx.time, str)
        self.assertTrue(len(multi_tx.time) > 0)
        
    def test_multiple_multi_transactions_different_times(self):
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
        self.assertNotEqual(multi_tx1.time, multi_tx2.time)


class TestMultiTransactionsPropertyAccess(unittest.TestCase):
    """Test suite for MultiTransactions property access and validation."""
    
    def setUp(self):
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
        
    def test_sender_property(self):
        """Test sender property access."""
        self.assertEqual(self.multi_tx.sender, self.sender)
        
    def test_multi_txns_property(self):
        """Test multi_txns property access."""
        self.assertEqual(len(self.multi_tx.multi_txns), 2)
        self.assertIsInstance(self.multi_tx.multi_txns, list)
        
    def test_digest_property(self):
        """Test digest property access."""
        # Initially None
        self.assertIsNone(self.multi_tx.digest)
        
        # After setting digest
        self.multi_tx.set_digest()
        self.assertIsNotNone(self.multi_tx.digest)
        
    def test_signature_property(self):
        """Test signature property access."""
        # Initially None
        self.assertIsNone(self.multi_tx.signature)
        
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
        self.assertIsNotNone(self.multi_tx.signature)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)