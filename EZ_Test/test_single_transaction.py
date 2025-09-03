#!/usr/bin/env python3
"""
Comprehensive unit tests for SingleTransaction.py with transaction functionality.
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
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from EZ_Transaction.SingleTransaction import Transaction
    from EZ_Value.Value import Value, ValueState
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)


class TestTransactionInitialization(unittest.TestCase):
    """Test suite for Transaction class initialization and basic properties."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.sender = "0xSender123"
        self.recipient = "0xRecipient456"
        self.nonce = 1
        self.signature = None
        self.value = [Value("0x1000", 100), Value("0x2000", 200)]
        self.tx_hash = None
        self.time = datetime.datetime.now().isoformat()
        
    def test_transaction_initialization(self):
        """Test basic Transaction initialization."""
        tx = Transaction(
            sender=self.sender,
            recipient=self.recipient,
            nonce=self.nonce,
            signature=self.signature,
            value=self.value,
                        time=self.time
        )
        
        self.assertEqual(tx.sender, self.sender)
        self.assertEqual(tx.recipient, self.recipient)
        self.assertEqual(tx.nonce, self.nonce)
        self.assertIsNone(tx.signature)
        self.assertEqual(tx.value, self.value)
        self.assertIsNotNone(tx.tx_hash)
        self.assertEqual(tx.time, self.time)
        
    def test_transaction_initialization_with_all_params(self):
        """Test Transaction initialization with all parameters."""
        test_signature = b'signature_data'
        test_hash = b'tx_hash_data'
        test_time = '2023-01-01T12:00:00'
        
        tx = Transaction(
            sender=self.sender,
            recipient=self.recipient,
            nonce=self.nonce,
            signature=test_signature,
            value=self.value,
                        time=test_time
        )
        
        self.assertEqual(tx.signature, test_signature)
        self.assertIsNotNone(tx.tx_hash)
        self.assertEqual(len(tx.tx_hash), 32)  # SHA-256 hash length
        self.assertEqual(tx.time, test_time)


class TestTransactionHashing(unittest.TestCase):
    """Test suite for Transaction hashing functionality."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.sender = "0xSender123"
        self.recipient = "0xRecipient456"
        self.nonce = 1
        self.value = [Value("0x1000", 100)]
        self.tx = Transaction(
            sender=self.sender,
            recipient=self.recipient,
            nonce=self.nonce,
            signature=None,
            value=self.value,
                        time=datetime.datetime.now().isoformat()
        )
        
    def test_calculate_hash(self):
        """Test hash calculation method."""
        hash_result = self.tx._calculate_hash()
        self.assertIsInstance(hash_result, bytes)
        self.assertEqual(len(hash_result), 32)  # SHA-256 produces 32 bytes
        
    def test_hash_consistency(self):
        """Test that same transaction produces same hash."""
        hash1 = self.tx._calculate_hash()
        hash2 = self.tx._calculate_hash()
        self.assertEqual(hash1, hash2)
        
    def test_hash_different_transaction(self):
        """Test that different transactions produce different hashes."""
        tx2 = Transaction(
            sender="0xDifferentSender",
            recipient=self.recipient,
            nonce=self.nonce,
            signature=None,
            value=self.value,
                        time=datetime.datetime.now().isoformat()
        )
        
        hash1 = self.tx._calculate_hash()
        hash2 = tx2._calculate_hash()
        self.assertNotEqual(hash1, hash2)
        
    def test_txn2str_format(self):
        """Test transaction string representation."""
        tx_str = self.tx.txn2str()
        
        self.assertIn(f"Sender: {self.sender}", tx_str)
        self.assertIn(f"Recipient: {self.recipient}", tx_str)
        self.assertIn(f"Nonce: {str(self.nonce)}", tx_str)
        self.assertIn(f"Value: {self.value}", tx_str)
        self.assertIn("TxHash: b'", tx_str)
        self.assertIn(f"Time: {self.tx.time}", tx_str)


class TestTransactionSerialization(unittest.TestCase):
    """Test suite for Transaction serialization and deserialization."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.sender = "0xSender123"
        self.recipient = "0xRecipient456"
        self.nonce = 1
        self.value = [Value("0x1000", 100)]
        self.tx = Transaction(
            sender=self.sender,
            recipient=self.recipient,
            nonce=self.nonce,
            signature=None,
            value=self.value,
                        time=datetime.datetime.now().isoformat()
        )
        
    def test_encode_transaction(self):
        """Test transaction encoding."""
        encoded_data = self.tx.encode()
        self.assertIsInstance(encoded_data, bytes)
        
    def test_decode_transaction(self):
        """Test transaction decoding."""
        # First encode the transaction
        encoded_data = self.tx.encode()
        
        # Then decode it
        decoded_tx = Transaction.decode(encoded_data)
        
        # Verify the decoded transaction
        self.assertEqual(decoded_tx.sender, self.tx.sender)
        self.assertEqual(decoded_tx.recipient, self.tx.recipient)
        self.assertEqual(decoded_tx.nonce, self.tx.nonce)
        self.assertEqual(decoded_tx.value[0].begin_index, self.tx.value[0].begin_index)
        self.assertEqual(decoded_tx.value[0].value_num, self.tx.value[0].value_num)
        self.assertEqual(decoded_tx.time, self.tx.time)
        
    def test_encode_decode_roundtrip(self):
        """Test that encode-decode roundtrip preserves all data."""
        original_tx = Transaction(
            sender="0xOriginalSender",
            recipient="0xOriginalRecipient",
            nonce=42,
            signature=b'test_signature',
            value=[Value("0x5000", 500)],
            time='2023-01-01T00:00:00'
        )
        
        encoded_data = original_tx.encode()
        decoded_tx = Transaction.decode(encoded_data)
        
        # Verify all fields are preserved
        self.assertEqual(decoded_tx.sender, original_tx.sender)
        self.assertEqual(decoded_tx.recipient, original_tx.recipient)
        self.assertEqual(decoded_tx.nonce, original_tx.nonce)
        self.assertEqual(decoded_tx.signature, original_tx.signature)
        self.assertEqual(decoded_tx.value[0].begin_index, original_tx.value[0].begin_index)
        self.assertEqual(decoded_tx.value[0].value_num, original_tx.value[0].value_num)
        self.assertEqual(decoded_tx.tx_hash, original_tx.tx_hash)
        self.assertEqual(decoded_tx.time, original_tx.time)


class TestTransactionFactoryMethod(unittest.TestCase):
    """Test suite for Transaction factory method."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.sender = "0xSender123"
        self.recipient = "0xRecipient456"
        self.value = [Value("0x1000", 100), Value("0x2000", 200)]
        self.nonce = 1
        
    def test_new_transaction_creation(self):
        """Test creating a new transaction using factory method."""
        tx = Transaction.new_transaction(
            sender=self.sender,
            recipient=self.recipient,
            value=self.value,
            nonce=self.nonce
        )
        
        # Verify all required fields are set
        self.assertEqual(tx.sender, self.sender)
        self.assertEqual(tx.recipient, self.recipient)
        self.assertEqual(tx.nonce, self.nonce)
        self.assertEqual(tx.value, self.value)
        self.assertIsNotNone(tx.time)
        self.assertIsInstance(tx.time, str)
        self.assertIsNone(tx.signature)
        self.assertIsNotNone(tx.tx_hash)
        self.assertIsInstance(tx.tx_hash, bytes)
        
    def test_new_transaction_hash_calculation(self):
        """Test that new transaction calculates hash correctly."""
        tx = Transaction.new_transaction(
            sender=self.sender,
            recipient=self.recipient,
            value=self.value,
            nonce=self.nonce
        )
        
        # Verify hash is calculated and is proper length
        self.assertIsNotNone(tx.tx_hash)
        self.assertEqual(len(tx.tx_hash), 32)  # SHA-256 produces 32 bytes
        
    def test_new_transaction_different_hashes(self):
        """Test that different transactions produce different hashes."""
        tx1 = Transaction.new_transaction(
            sender=self.sender,
            recipient=self.recipient,
            value=self.value,
            nonce=self.nonce
        )
        
        tx2 = Transaction.new_transaction(
            sender="0xDifferentSender",
            recipient=self.recipient,
            value=self.value,
            nonce=self.nonce
        )
        
        self.assertNotEqual(tx1.tx_hash, tx2.tx_hash)


class TestTransactionSignature(unittest.TestCase):
    """Test suite for Transaction signature functionality."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Generate test keys (in real scenario, these would be from key management)
        from cryptography.hazmat.primitives.asymmetric import ec
        from cryptography.hazmat.primitives import serialization
        
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
        self.recipient = "0xRecipient456"
        self.value = [Value("0x1000", 100)]
        self.tx = Transaction(
            sender=self.sender,
            recipient=self.recipient,
            nonce=1,
            signature=None,
            value=self.value,
                        time=datetime.datetime.now().isoformat()
        )
        
    def test_sign_transaction(self):
        """Test transaction signing."""
        self.tx.sig_txn(self.private_key_pem)
        
        # Verify signature is set
        self.assertIsNotNone(self.tx.signature)
        self.assertIsInstance(self.tx.signature, bytes)
        
    def test_signature_verification(self):
        """Test signature verification."""
        # Sign the transaction
        self.tx.sig_txn(self.private_key_pem)
        
        # Verify the signature should be valid
        result = self.tx.check_txn_sig(self.public_key_pem)
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
        self.tx.sig_txn(self.private_key_pem)
        
        # Verify with wrong key should fail
        result = self.tx.check_txn_sig(wrong_public_key_pem)
        self.assertFalse(result)
        
    def test_unsigned_transaction_verification(self):
        """Test verification of unsigned transaction."""
        # When signature is None, verification should fail
        result = self.tx.check_txn_sig(self.public_key_pem)
        self.assertFalse(result)
        
    def test_signature_verification_with_state_change(self):
        """Test that signature verification works even when value state changes."""
        # Sign the transaction when value is in UNSPENT state
        original_state = self.tx.value[0].state
        self.assertEqual(original_state, ValueState.UNSPENT)
        
        # Sign the transaction
        self.tx.sig_txn(self.private_key_pem)
        
        # Verify signature is valid with original state
        result = self.tx.check_txn_sig(self.public_key_pem)
        self.assertTrue(result)
        
        # Change the value state (simulating transaction lifecycle)
        self.tx.value[0].set_state(ValueState.SELECTED)
        
        # Signature should still be valid even with state change
        result = self.tx.check_txn_sig(self.public_key_pem)
        self.assertTrue(result)
        
        # Change state again to LOCAL_COMMITTED
        self.tx.value[0].set_state(ValueState.LOCAL_COMMITTED)
        
        # Signature should still be valid
        result = self.tx.check_txn_sig(self.public_key_pem)
        self.assertTrue(result)
        
        # Change state again to CONFIRMED
        self.tx.value[0].set_state(ValueState.CONFIRMED)
        
        # Signature should still be valid
        result = self.tx.check_txn_sig(self.public_key_pem)
        self.assertTrue(result)
        
    def test_serialization_methods_consistency(self):
        """Test that serialization methods work correctly."""
        # Test _serialize_values includes state
        regular_serialized = self.tx._serialize_values()
        self.assertEqual(len(regular_serialized), 1)
        self.assertIn("state", regular_serialized[0])
        self.assertEqual(regular_serialized[0]["state"], ValueState.UNSPENT.value)
        
        # Test _serialize_values_for_signing excludes state
        signing_serialized = self.tx._serialize_values_for_signing()
        self.assertEqual(len(signing_serialized), 1)
        self.assertNotIn("state", signing_serialized[0])
        
        # Both should contain the same essential value information
        self.assertEqual(regular_serialized[0]["begin_index"], signing_serialized[0]["begin_index"])
        self.assertEqual(regular_serialized[0]["end_index"], signing_serialized[0]["end_index"])
        self.assertEqual(regular_serialized[0]["value_num"], signing_serialized[0]["value_num"])
        
    def test_value_to_dict_methods(self):
        """Test that Value's to_dict methods work correctly."""
        value = self.tx.value[0]
        
        # Test regular to_dict includes state
        regular_dict = value.to_dict()
        self.assertIn("state", regular_dict)
        self.assertEqual(regular_dict["state"], ValueState.UNSPENT.value)
        
        # Test to_dict_for_signing excludes state
        signing_dict = value.to_dict_for_signing()
        self.assertNotIn("state", signing_dict)
        
        # Both should contain the same essential value information
        self.assertEqual(regular_dict["begin_index"], signing_dict["begin_index"])
        self.assertEqual(regular_dict["end_index"], signing_dict["end_index"])
        self.assertEqual(regular_dict["value_num"], signing_dict["value_num"])


class TestTransactionValidationMethods(unittest.TestCase):
    """Test suite for Transaction validation methods."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.sender = "0xSender123"
        self.recipient = "0xRecipient456"
        self.value = [Value("0x1000", 100)]
        self.tx = Transaction(
            sender=self.sender,
            recipient=self.recipient,
            nonce=1,
            signature=None,
            value=self.value,
                        time=datetime.datetime.now().isoformat()
        )
        
    def test_is_sent_to_self_true(self):
        """Test is_sent_to_self when sender equals recipient."""
        tx = Transaction(
            sender="0xSameAddress",
            recipient="0xSameAddress",
            nonce=1,
            signature=None,
            value=self.value,
                        time=datetime.datetime.now().isoformat()
        )
        
        self.assertTrue(tx.is_sent_to_self())
        
    def test_is_sent_to_self_false(self):
        """Test is_sent_to_self when sender differs from recipient."""
        self.assertFalse(self.tx.is_sent_to_self())
        
    def test_get_values(self):
        """Test get_values method."""
        values = self.tx.get_values()
        self.assertEqual(values, self.value)
        self.assertIsInstance(values, list)
        self.assertEqual(len(values), 1)
        self.assertIsInstance(values[0], Value)
        
    def test_value_attribute_type_validation(self):
        """Test that Transaction.value is properly typed as List[Value]."""
        # Verify value attribute is a list
        self.assertIsInstance(self.tx.value, list)
        
        # Verify all elements in value list are Value objects
        for value_obj in self.tx.value:
            self.assertIsInstance(value_obj, Value)
            
    def test_value_attribute_methods(self):
        """Test methods that work with value attribute."""
        # Test value operations
        self.assertEqual(self.tx.count_value_intersect_txn(Value("0x1050", 50)), 1)
        self.assertEqual(self.tx.count_value_in_value(Value("0x1050", 20)), 1)


class TestTransactionValueOperations(unittest.TestCase):
    """Test suite for Transaction value operations."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.sender = "0xSender123"
        self.recipient = "0xRecipient456"
        self.value = [Value("0x1000", 100), Value("0x2000", 200)]
        self.tx = Transaction(
            sender=self.sender,
            recipient=self.recipient,
            nonce=1,
            signature=None,
            value=self.value,
                        time=datetime.datetime.now().isoformat()
        )
        
        # Create test value for intersection operations
        self.test_value = Value("0x1050", 50)
        
    def test_count_value_intersect_txn(self):
        """Test count_value_intersect_txn method."""
        # Test value should intersect with first value in transaction
        count = self.tx.count_value_intersect_txn(self.test_value)
        self.assertEqual(count, 1)
        
    def test_count_value_intersect_txn_no_intersection(self):
        """Test count_value_intersect_txn with no intersection."""
        # Value with no intersection
        no_intersect_value = Value("0x3000", 100)
        count = self.tx.count_value_intersect_txn(no_intersect_value)
        self.assertEqual(count, 0)
        
    def test_count_value_in_value(self):
        """Test count_value_in_value method."""
        # Create a value that should be contained within transaction values
        contained_value = Value("0x1050", 20)
        count = self.tx.count_value_in_value(contained_value)
        self.assertEqual(count, 1)
        
    def test_count_value_in_value_no_containment(self):
        """Test count_value_in_value with no containment."""
        # Value not contained in transaction values
        not_contained_value = Value("0x3000", 100)
        count = self.tx.count_value_in_value(not_contained_value)
        self.assertEqual(count, 0)


class TestTransactionOutputMethods(unittest.TestCase):
    """Test suite for Transaction output and display methods."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.sender = "0xSender123"
        self.recipient = "0xRecipient456"
        self.value = [Value("0x1000", 100)]
        self.tx = Transaction(
            sender=self.sender,
            recipient=self.recipient,
            nonce=1,
            signature=None,
            value=self.value,
                        time=datetime.datetime.now().isoformat()
        )
        
    def test_print_tx_format(self):
        """Test print_tx method output format."""
        output = self.tx.print_tx()
        
        # Should contain the transaction details
        self.assertIn(self.sender, output)
        self.assertIn(self.recipient, output)
        self.assertIn(str(self.value), output)
        self.assertIn("b'", output)  # tx_hash is now auto-calculated
        
    @patch('builtins.print')
    def test_print_txn_dst(self, mock_print):
        """Test print_txn_dst method (captures print calls)."""
        self.tx.print_txn_dst()
        
        # Verify print was called
        self.assertTrue(mock_print.called)
        
        # Check that the print calls contain expected content
        print_calls = [str(call[0][0]) for call in mock_print.call_args_list]
        output_text = ' '.join(print_calls)
        
        self.assertIn('---------txn---------', output_text)
        self.assertIn('Sender: 0xSender123', output_text)
        self.assertIn('Recipient: 0xRecipient456', output_text)


class TestTransactionEdgeCases(unittest.TestCase):
    """Test suite for Transaction edge cases and error handling."""
    
    def test_empty_value_list(self):
        """Test Transaction with empty value list."""
        tx = Transaction(
            sender="0xSender",
            recipient="0xRecipient",
            nonce=1,
            signature=None,
            value=[],
                        time=datetime.datetime.now().isoformat()
        )
        
        self.assertEqual(len(tx.value), 0)
        self.assertEqual(tx.get_values(), [])
        self.assertIsInstance(tx.value, list)
        
    def test_multiple_value_objects(self):
        """Test Transaction with multiple Value objects."""
        values = [
            Value("0x1000", 100),
            Value("0x2000", 200),
            Value("0x3000", 300)
        ]
        
        tx = Transaction(
            sender="0xSender",
            recipient="0xRecipient",
            nonce=1,
            signature=None,
            value=values,
                        time=datetime.datetime.now().isoformat()
        )
        
        self.assertEqual(len(tx.value), 3)
        self.assertIsInstance(tx.value, list)
        for i, value_obj in enumerate(tx.value):
            self.assertIsInstance(value_obj, Value)
            self.assertEqual(value_obj.begin_index, values[i].begin_index)
            self.assertEqual(value_obj.value_num, values[i].value_num)
            
    def test_value_list_operations(self):
        """Test operations on Transaction value list."""
        values = [Value("0x1000", 100), Value("0x2000", 200)]
        tx = Transaction(
            sender="0xSender",
            recipient="0xRecipient",
            nonce=1,
            signature=None,
            value=values,
                        time=datetime.datetime.now().isoformat()
        )
        
        # Test list operations
        self.assertEqual(len(tx.value), 2)
        self.assertEqual(tx.value[0].begin_index, "0x1000")
        self.assertEqual(tx.value[1].begin_index, "0x2000")
        
        # Test get_values method returns same list
        self.assertEqual(tx.get_values(), values)
        self.assertEqual(tx.get_values()[0].begin_index, "0x1000")
        
    def test_large_value_list(self):
        """Test Transaction with large value list."""
        values = [Value(f"0x{i}", 100) for i in range(1000)]
        
        tx = Transaction(
            sender="0xSender",
            recipient="0xRecipient",
            nonce=1,
            signature=None,
            value=values,
                        time=datetime.datetime.now().isoformat()
        )
        
        self.assertEqual(len(tx.value), 1000)
        
    def test_invalid_signature_format(self):
        """Test Transaction with invalid signature format."""
        # This should not raise an exception during initialization
        tx = Transaction(
            sender="0xSender",
            recipient="0xRecipient",
            nonce=1,
            signature="invalid_signature",
            value=[Value("0x1000", 100)],
                        time=datetime.datetime.now().isoformat()
        )
        
        self.assertEqual(tx.signature, "invalid_signature")


class TestTransactionTimeHandling(unittest.TestCase):
    """Test suite for Transaction time handling."""
    
    def test_time_format(self):
        """Test that time is properly formatted."""
        test_time = "2023-01-01T12:00:00"
        
        tx = Transaction(
            sender="0xSender",
            recipient="0xRecipient",
            nonce=1,
            signature=None,
            value=[Value("0x1000", 100)],
                        time=test_time
        )
        
        self.assertEqual(tx.time, test_time)
        
    def test_new_transaction_time_format(self):
        """Test that new_transaction creates properly formatted time."""
        tx = Transaction.new_transaction(
            sender="0xSender",
            recipient="0xRecipient",
            value=[Value("0x1000", 100)],
            nonce=1
        )
        
        # Should be a string in ISO format
        self.assertIsInstance(tx.time, str)
        self.assertIn('T', tx.time)  # ISO format should contain 'T'
        
    def test_time_in_string_representation(self):
        """Test that time appears in transaction string representation."""
        test_time = "2023-01-01T12:00:00"
        
        tx = Transaction(
            sender="0xSender",
            recipient="0xRecipient",
            nonce=1,
            signature=None,
            value=[Value("0x1000", 100)],
                        time=test_time
        )
        
        tx_str = tx.txn2str()
        self.assertIn(f"Time: {test_time}", tx_str)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)