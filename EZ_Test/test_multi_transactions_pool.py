import unittest
import os
import tempfile
import time
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from EZ_Transaction.MultiTransactions import MultiTransactions
from EZ_Transaction.SingleTransaction import Transaction
from EZ_Value.Value import Value
from EZ_Transaction_Pool.TransactionPool import MultiTxnsPool, ValidationResult
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization


class TestMultiTxnsPool(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary database file
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        
        # Create pool instance with temporary database
        self.pool = MultiTxnsPool(self.temp_db.name)
        
        # Generate test keys
        self.private_key = ec.generate_private_key(ec.SECP256R1())
        self.public_key = self.private_key.public_key()
        
        # Serialize keys
        self.private_key_pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        self.public_key_pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        # Create test sender and recipient
        self.test_sender = "sender_test"
        self.test_recipient = "recipient_test"
        
        # Create test values
        self.test_value1 = Value("0x1000", 100)
        self.test_value2 = Value("0x2000", 200)
        
        # Create test transactions
        self.txn1 = Transaction.new_transaction(
            sender=self.test_sender,
            recipient=self.test_recipient,
            value=[self.test_value1],
            nonce=1
        )
        
        self.txn2 = Transaction.new_transaction(
            sender=self.test_sender,
            recipient=self.test_recipient,
            value=[self.test_value2],
            nonce=2
        )
        
        # Sign individual transactions
        self.txn1.sig_txn(self.private_key_pem)
        self.txn2.sig_txn(self.private_key_pem)
        
        # Create test MultiTransactions
        self.multi_txn = MultiTransactions(
            sender=self.test_sender,
            sender_id="sender_id_test",
            multi_txns=[self.txn1, self.txn2]
        )
        
        # Sign the MultiTransactions
        self.multi_txn.sig_acc_txn(self.private_key_pem)
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temporary database file
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
        
        # Stop the cleanup thread
        if hasattr(self.pool, '_cleanup_thread'):
            self.pool._cleanup_thread = None
    
    def test_initialization(self):
        """Test pool initialization."""
        self.assertEqual(len(self.pool.pool), 0)
        self.assertEqual(len(self.pool.sender_index), 0)
        self.assertEqual(len(self.pool.digest_index), 0)
        self.assertIsNotNone(self.pool.stats)
        
        # Check stats initial values
        expected_stats = {
            'total_received': 0,
            'valid_received': 0,
            'invalid_received': 0,
            'duplicates': 0
        }
        self.assertEqual(self.pool.stats, expected_stats)
    
    def test_validation_result(self):
        """Test ValidationResult dataclass."""
        validation_result = ValidationResult(
            is_valid=True,
            signature_valid=True,
            structural_valid=True,
            sender_match=True,
            duplicates_found=[]
        )
        
        self.assertTrue(validation_result.is_valid)
        self.assertTrue(validation_result.signature_valid)
        self.assertTrue(validation_result.structural_valid)
        self.assertTrue(validation_result.sender_match)
        self.assertEqual(len(validation_result.duplicates_found), 0)
    
    def test_validate_multi_transactions_empty(self):
        """Test validation of empty MultiTransactions."""
        empty_multi_txn = MultiTransactions(
            sender=self.test_sender,
            sender_id="test_id",
            multi_txns=[]
        )
        
        validation_result = self.pool.validate_multi_transactions(empty_multi_txn, self.public_key_pem)
        
        self.assertFalse(validation_result.is_valid)
        self.assertEqual(validation_result.error_message, "MultiTransactions cannot be empty")
        self.assertFalse(validation_result.structural_valid)
    
    def test_validate_multi_transactions_missing_sender(self):
        """Test validation of MultiTransactions with missing sender."""
        invalid_multi_txn = MultiTransactions(
            sender="",
            sender_id="test_id",
            multi_txns=[self.txn1]
        )
        
        validation_result = self.pool.validate_multi_transactions(invalid_multi_txn, self.public_key_pem)
        
        self.assertFalse(validation_result.is_valid)
        self.assertEqual(validation_result.error_message, "Missing sender or sender_id")
        self.assertFalse(validation_result.structural_valid)
    
    def test_validate_multi_transactions_invalid_transaction_type(self):
        """Test validation with invalid transaction type."""
        invalid_multi_txn = MultiTransactions(
            sender=self.test_sender,
            sender_id="test_id",
            multi_txns=[self.txn1, "invalid_transaction"]
        )
        
        validation_result = self.pool.validate_multi_transactions(invalid_multi_txn, self.public_key_pem)
        
        self.assertFalse(validation_result.is_valid)
        self.assertIn("is not a valid Transaction object", validation_result.error_message)
    
    def test_validate_multi_transactions_different_senders(self):
        """Test validation with transactions from different senders."""
        # Create transaction with different sender
        different_sender = "different_sender"
        different_value = Value("0x3000", 300)
        different_txn = Transaction.new_transaction(
            sender=different_sender,
            recipient=self.test_recipient,
            value=[different_value],
            nonce=3
        )
        
        invalid_multi_txn = MultiTransactions(
            sender=self.test_sender,
            sender_id="test_id",
            multi_txns=[self.txn1, different_txn]
        )
        
        validation_result = self.pool.validate_multi_transactions(invalid_multi_txn, self.public_key_pem)
        
        self.assertFalse(validation_result.is_valid)
        self.assertIn("different sender", validation_result.error_message)
        self.assertFalse(validation_result.sender_match)
    
    def test_validate_multi_transactions_missing_signature(self):
        """Test validation of MultiTransactions without signature."""
        unsigned_multi_txn = MultiTransactions(
            sender=self.test_sender,
            sender_id="test_id",
            multi_txns=[self.txn1]
        )
        
        validation_result = self.pool.validate_multi_transactions(unsigned_multi_txn, self.public_key_pem)
        
        self.assertFalse(validation_result.is_valid)
        self.assertEqual(validation_result.error_message, "MultiTransactions signature is missing")
        self.assertFalse(validation_result.signature_valid)
    
    def test_validate_multi_transactions_invalid_signature(self):
        """Test validation of MultiTransactions with invalid signature."""
        # Create MultiTransactions with wrong key
        wrong_key = ec.generate_private_key(ec.SECP256R1())
        wrong_key_pem = wrong_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        wrong_multi_txn = MultiTransactions(
            sender=self.test_sender,
            sender_id="test_id",
            multi_txns=[self.txn1]
        )
        wrong_multi_txn.sig_acc_txn(wrong_key_pem)
        
        validation_result = self.pool.validate_multi_transactions(wrong_multi_txn, self.public_key_pem)
        
        self.assertFalse(validation_result.is_valid)
        self.assertIn("signature verification failed", validation_result.error_message)
        self.assertFalse(validation_result.signature_valid)
    
    def test_validate_multi_transactions_invalid_transaction_signature(self):
        """Test validation with invalid transaction signature."""
        # Create transaction with wrong key
        wrong_key = ec.generate_private_key(ec.SECP256R1())
        wrong_key_pem = wrong_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        invalid_txn = Transaction.new_transaction(
            sender=self.test_sender,
            recipient=self.test_recipient,
            value=[self.test_value1],
            nonce=4
        )
        invalid_txn.sig_txn(wrong_key_pem)
        
        invalid_multi_txn = MultiTransactions(
            sender=self.test_sender,
            sender_id="test_id",
            multi_txns=[invalid_txn]
        )
        invalid_multi_txn.sig_acc_txn(self.private_key_pem)
        
        validation_result = self.pool.validate_multi_transactions(invalid_multi_txn, self.public_key_pem)
        
        self.assertFalse(validation_result.is_valid)
        self.assertIn("signature verification failed", validation_result.error_message)
    
    def test_validate_multi_transactions_valid(self):
        """Test validation of valid MultiTransactions."""
        # Sign individual transactions in the test MultiTransactions
        for txn in self.multi_txn.multi_txns:
            if txn.signature is None:
                txn.sig_txn(self.private_key_pem)
        
        validation_result = self.pool.validate_multi_transactions(self.multi_txn, self.public_key_pem)
        
        self.assertTrue(validation_result.is_valid)
        self.assertTrue(validation_result.signature_valid)
        self.assertTrue(validation_result.structural_valid)
        self.assertTrue(validation_result.sender_match)
        self.assertEqual(len(validation_result.duplicates_found), 0)
    
    def test_add_multi_transactions_success(self):
        """Test successful addition of MultiTransactions."""
        success, message = self.pool.add_multi_transactions(self.multi_txn, self.public_key_pem)
        
        self.assertTrue(success)
        self.assertEqual(message, "MultiTransactions added successfully")
        
        # Check pool contents
        self.assertEqual(len(self.pool.pool), 1)
        self.assertEqual(len(self.pool.sender_index), 1)
        self.assertEqual(len(self.pool.digest_index), 1)
        
        # Check stats
        self.assertEqual(self.pool.stats['total_received'], 1)
        self.assertEqual(self.pool.stats['valid_received'], 1)
        self.assertEqual(self.pool.stats['invalid_received'], 0)
        self.assertEqual(self.pool.stats['duplicates'], 0)
    
    def test_add_multi_transactions_invalid(self):
        """Test addition of invalid MultiTransactions."""
        invalid_multi_txn = MultiTransactions(
            sender="",
            sender_id="test_id",
            multi_txns=[self.txn1]
        )
        
        success, message = self.pool.add_multi_transactions(invalid_multi_txn, self.public_key_pem)
        
        self.assertFalse(success)
        self.assertIn("Missing sender or sender_id", message)
        
        # Check stats
        self.assertEqual(self.pool.stats['total_received'], 1)
        self.assertEqual(self.pool.stats['valid_received'], 0)
        self.assertEqual(self.pool.stats['invalid_received'], 1)
    
    def test_add_multi_transactions_duplicate(self):
        """Test addition of duplicate MultiTransactions."""
        # Add first time
        success1, message1 = self.pool.add_multi_transactions(self.multi_txn, self.public_key_pem)
        self.assertTrue(success1)
        
        # Add second time (duplicate)
        success2, message2 = self.pool.add_multi_transactions(self.multi_txn, self.public_key_pem)
        
        self.assertFalse(success2)
        self.assertEqual(message2, "Duplicate MultiTransactions")
        
        # Check stats
        self.assertEqual(self.pool.stats['total_received'], 2)
        self.assertEqual(self.pool.stats['valid_received'], 1)
        self.assertEqual(self.pool.stats['invalid_received'], 0)
        self.assertEqual(self.pool.stats['duplicates'], 1)
    
    def test_get_multi_transactions_by_sender(self):
        """Test getting MultiTransactions by sender."""
        # Add the test MultiTransactions
        self.pool.add_multi_transactions(self.multi_txn, self.public_key_pem)
        
        # Get by sender
        result = self.pool.get_multi_transactions_by_sender(self.test_sender)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], self.multi_txn)
        
        # Get non-existent sender
        result = self.pool.get_multi_transactions_by_sender("non_existent_sender")
        self.assertEqual(len(result), 0)
    
    def test_get_multi_transactions_by_digest(self):
        """Test getting MultiTransactions by digest."""
        # Add the test MultiTransactions
        self.pool.add_multi_transactions(self.multi_txn, self.public_key_pem)
        
        # Get by digest
        result = self.pool.get_multi_transactions_by_digest(self.multi_txn.digest)
        
        self.assertIsNotNone(result)
        self.assertEqual(result, self.multi_txn)
        
        # Get non-existent digest
        result = self.pool.get_multi_transactions_by_digest("non_existent_digest")
        self.assertIsNone(result)
    
    def test_remove_multi_transactions(self):
        """Test removing MultiTransactions."""
        # Add the test MultiTransactions
        self.pool.add_multi_transactions(self.multi_txn, self.public_key_pem)
        
        # Remove by digest
        success = self.pool.remove_multi_transactions(self.multi_txn.digest)
        
        self.assertTrue(success)
        self.assertEqual(len(self.pool.pool), 0)
        self.assertEqual(len(self.pool.sender_index), 0)
        self.assertEqual(len(self.pool.digest_index), 0)
        
        # Try to remove non-existent digest
        success = self.pool.remove_multi_transactions("non_existent_digest")
        self.assertFalse(success)
    
    def test_get_pool_stats(self):
        """Test getting pool statistics."""
        # Add multiple MultiTransactions
        self.pool.add_multi_transactions(self.multi_txn, self.public_key_pem)
        
        # Create another MultiTransactions
        multi_txn2 = MultiTransactions(
            sender=self.test_sender,
            sender_id="sender_id_test2",
            multi_txns=[self.txn1]
        )
        multi_txn2.sig_acc_txn(self.private_key_pem)
        self.pool.add_multi_transactions(multi_txn2, self.public_key_pem)
        
        stats = self.pool.get_pool_stats()
        
        self.assertEqual(stats['total_transactions'], 2)
        self.assertEqual(stats['unique_senders'], 1)
        self.assertEqual(stats['stats']['total_received'], 2)
        self.assertEqual(stats['stats']['valid_received'], 2)
        self.assertIn('pool_size_bytes', stats)
    
    def test_get_all_multi_transactions(self):
        """Test getting all MultiTransactions."""
        # Add multiple MultiTransactions
        self.pool.add_multi_transactions(self.multi_txn, self.public_key_pem)
        
        # Create another MultiTransactions
        multi_txn2 = MultiTransactions(
            sender=self.test_sender,
            sender_id="sender_id_test2",
            multi_txns=[self.txn1]
        )
        multi_txn2.sig_acc_txn(self.private_key_pem)
        self.pool.add_multi_transactions(multi_txn2, self.public_key_pem)
        
        result = self.pool.get_all_multi_transactions()
        
        self.assertEqual(len(result), 2)
        # Check that we get copies, not references
        self.assertIsNot(result[0], self.pool.pool[0])
        self.assertIsNot(result[1], self.pool.pool[1])
    
    def test_clear_pool(self):
        """Test clearing the pool."""
        # Add multiple MultiTransactions
        self.pool.add_multi_transactions(self.multi_txn, self.public_key_pem)
        self.pool.add_multi_transactions(self.multi_txn, self.public_key_pem)
        
        # Clear pool
        self.pool.clear_pool()
        
        self.assertEqual(len(self.pool.pool), 0)
        self.assertEqual(len(self.pool.sender_index), 0)
        self.assertEqual(len(self.pool.digest_index), 0)
    
    def test_thread_safety(self):
        """Test thread safety of pool operations."""
        import threading
        import time
        
        # Create multiple threads that add MultiTransactions
        results = []
        errors = []
        
        def worker(thread_id):
            try:
                # Create unique MultiTransactions for each thread
                multi_txn = MultiTransactions(
                    sender=f"sender_{thread_id}",
                    sender_id=f"sender_id_{thread_id}",
                    multi_txns=[self.txn1]
                )
                multi_txn.sig_acc_txn(self.private_key_pem)
                
                success, message = self.pool.add_multi_transactions(multi_txn, self.public_key_pem)
                results.append((thread_id, success, message))
                
            except Exception as e:
                errors.append((thread_id, str(e)))
        
        # Start multiple threads
        threads = []
        for i in range(10):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()
        
        # Wait for all threads to complete
        for t in threads:
            t.join()
        
        # Check results
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(results), 10)
        
        # All should have succeeded
        for thread_id, success, message in results:
            self.assertTrue(success)
        
        # Check final pool size
        self.assertEqual(len(self.pool.pool), 10)
    
    def test_database_persistence(self):
        """Test database persistence."""
        # Add MultiTransactions
        self.pool.add_multi_transactions(self.multi_txn, self.public_key_pem)
        
        # Create new pool instance with same database
        new_pool = MultiTxnsPool(self.temp_db.name)
        
        # Check that data persists
        self.assertEqual(len(new_pool.pool), 1)
        self.assertEqual(len(new_pool.sender_index), 1)
        self.assertEqual(len(new_pool.digest_index), 1)
        
        # Check stats
        self.assertEqual(new_pool.stats['total_received'], 1)
        self.assertEqual(new_pool.stats['valid_received'], 1)
    
    def test_index_rebuilding(self):
        """Test index rebuilding after removal."""
        # Add multiple MultiTransactions
        self.pool.add_multi_transactions(self.multi_txn, self.public_key_pem)
        
        multi_txn2 = MultiTransactions(
            sender=self.test_sender,
            sender_id="sender_id_test2",
            multi_txns=[self.txn1]
        )
        multi_txn2.sig_acc_txn(self.private_key_pem)
        self.pool.add_multi_transactions(multi_txn2, self.public_key_pem)
        
        # Remove first MultiTransactions
        self.pool.remove_multi_transactions(self.multi_txn.digest)
        
        # Check that indices are properly rebuilt
        self.assertEqual(len(self.pool.pool), 1)
        self.assertEqual(len(self.pool.sender_index), 1)
        self.assertEqual(len(self.pool.digest_index), 1)
        
        # Check that the remaining MultiTransactions is accessible
        result = self.pool.get_multi_transactions_by_digest(multi_txn2.digest)
        self.assertIsNotNone(result)
        self.assertEqual(result, multi_txn2)


if __name__ == '__main__':
    unittest.main()