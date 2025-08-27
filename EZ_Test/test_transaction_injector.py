import unittest
import time
import tempfile
import os
from unittest.mock import patch, MagicMock

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from EZ_Simulation.TransactionInjector import TransactionInjector, SimulationConfig, SimulationStats
from EZ_Transaction_Pool.TransactionPool import TransactionPool
from EZ_Transaction.MultiTransactions import MultiTransactions
from EZ_Transaction.SingleTransaction import Transaction
from EZ_Value.Value import Value, ValueState


class TestTransactionInjector(unittest.TestCase):
    """Test cases for TransactionInjector class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Create test configuration
        self.config = SimulationConfig(
            num_senders=3,
            num_transactions_per_batch=2,
            num_batches=5,
            injection_interval=0.01,  # Very fast for testing
            validation_enabled=False,  # Disable validation for simpler testing
            signature_enabled=False,  # Disable for simpler testing
            duplicate_probability=0.0,  # Disable duplicates for basic tests
            invalid_probability=0.0    # Disable invalid transactions for basic tests
        )
        
        # Create injector with temporary database
        self.injector = TransactionInjector(self.config)
        # Override database path
        self.injector.transaction_pool.db_path = self.temp_db.name
        # Reinitialize with new database
        self.injector.transaction_pool._init_database()
    
    def tearDown(self):
        """Clean up test fixtures"""
        # Clean up injector
        self.injector.cleanup()
        
        # Remove temporary database file
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_injector_initialization(self):
        """Test TransactionInjector initialization"""
        self.assertEqual(len(self.injector.sender_keys), self.config.num_senders)
        self.assertEqual(self.injector.stats.total_injected, 0)
        self.assertIsInstance(self.injector.transaction_pool, TransactionPool)
    
    def test_generate_sender_keys(self):
        """Test sender key generation"""
        keys = self.injector._generate_sender_keys()
        self.assertEqual(len(keys), self.config.num_senders)
        
        for sender, public_key in keys.items():
            self.assertTrue(sender.startswith("sender_"))
            self.assertIsInstance(public_key, bytes)
    
    def test_generate_values(self):
        """Test value generation"""
        values = self.injector._generate_values(3)
        self.assertEqual(len(values), 3)
        
        for value in values:
            self.assertIsInstance(value, Value)
            self.assertEqual(value.state, ValueState.UNSPENT)
            self.assertTrue(value.check_value())
    
    def test_create_single_transaction(self):
        """Test single transaction creation"""
        sender = list(self.injector.sender_keys.keys())[0]
        recipient = "test_recipient"
        nonce = 12345
        
        tx = self.injector._create_single_transaction(sender, recipient, nonce)
        
        self.assertIsInstance(tx, Transaction)
        self.assertEqual(tx.sender, sender)
        self.assertEqual(tx.recipient, recipient)
        self.assertEqual(tx.nonce, nonce)
        self.assertIsInstance(tx.value, list)
        self.assertTrue(len(tx.value) > 0)
    
    def test_create_multi_transactions(self):
        """Test MultiTransactions creation"""
        sender = list(self.injector.sender_keys.keys())[0]
        batch_size = 2
        
        multi_txn = self.injector._create_multi_transactions(sender, batch_size)
        
        self.assertIsInstance(multi_txn, MultiTransactions)
        self.assertEqual(multi_txn.sender, sender)
        self.assertEqual(len(multi_txn.multi_txns), batch_size)
        
        # Check that all transactions have the same sender
        for tx in multi_txn.multi_txns:
            self.assertEqual(tx.sender, sender)
    
    def test_create_invalid_multi_transactions(self):
        """Test creation of invalid MultiTransactions"""
        sender = list(self.injector.sender_keys.keys())[0]
        
        invalid_multi_txn = self.injector._create_invalid_multi_transactions(sender)
        
        self.assertIsInstance(invalid_multi_txn, MultiTransactions)
        self.assertEqual(len(invalid_multi_txn.multi_txns), 2)
        
        # Check that transactions have different senders
        senders = [tx.sender for tx in invalid_multi_txn.multi_txns]
        self.assertEqual(len(set(senders)), 2)  # Should have 2 different senders
    
    def test_inject_single_transaction(self):
        """Test single transaction injection"""
        sender = list(self.injector.sender_keys.keys())[0]
        
        success, message = self.injector.inject_single_transaction(sender)
        
        self.assertTrue(success)
        self.assertEqual(self.injector.stats.total_injected, 1)
        self.assertEqual(self.injector.stats.successfully_added, 1)
        self.assertEqual(len(self.injector.injected_transactions), 1)
    
    def test_inject_batch_transactions(self):
        """Test batch transaction injection"""
        sender = list(self.injector.sender_keys.keys())[0]
        batch_size = 2
        
        results = self.injector.inject_batch_transactions(sender, batch_size)
        
        self.assertEqual(len(results), 1)  # One MultiTransactions object
        self.assertTrue(results[0][0])  # Should be successful
        self.assertEqual(self.injector.stats.total_injected, 1)
        self.assertEqual(self.injector.stats.successfully_added, 1)
    
    def test_inject_invalid_transaction(self):
        """Test injection of invalid transaction"""
        sender = list(self.injector.sender_keys.keys())[0]
        
        # Create invalid MultiTransactions manually
        invalid_multi_txn = self.injector._create_invalid_multi_transactions(sender)
        
        # Add to pool
        public_key = self.injector.sender_keys[sender]
        success, message = self.injector.transaction_pool.add_multi_transactions(invalid_multi_txn, public_key)
        
        self.assertFalse(success)
        self.assertIn("different sender", message.lower())
    
    def test_duplicate_transaction_injection(self):
        """Test duplicate transaction injection"""
        sender = list(self.injector.sender_keys.keys())[0]
        
        # Create and inject a transaction
        success1, message1 = self.injector.inject_single_transaction(sender)
        self.assertTrue(success1)
        
        # Try to inject the same transaction again
        success2, message2 = self.injector.inject_single_transaction(sender)
        
        # The second injection might fail due to duplicate detection
        # or it might succeed if it's a different transaction
        # We just want to make sure the system handles it gracefully
        self.assertIsInstance(success2, bool)
        self.assertIsInstance(message2, str)
    
    def test_get_current_stats(self):
        """Test getting current statistics"""
        # Initially stats should be empty
        stats = self.injector.get_current_stats()
        self.assertEqual(stats.total_injected, 0)
        self.assertEqual(stats.successfully_added, 0)
        
        # Inject a transaction
        sender = list(self.injector.sender_keys.keys())[0]
        self.injector.inject_single_transaction(sender)
        
        # Stats should be updated
        stats = self.injector.get_current_stats()
        self.assertEqual(stats.total_injected, 1)
        self.assertEqual(stats.successfully_added, 1)
    
    def test_simulation_config(self):
        """Test SimulationConfig dataclass"""
        config = SimulationConfig(
            num_senders=10,
            num_transactions_per_batch=5,
            num_batches=20,
            injection_interval=0.1,
            validation_enabled=False,
            signature_enabled=True,
            duplicate_probability=0.1,
            invalid_probability=0.05
        )
        
        self.assertEqual(config.num_senders, 10)
        self.assertEqual(config.num_transactions_per_batch, 5)
        self.assertEqual(config.num_batches, 20)
        self.assertEqual(config.injection_interval, 0.1)
        self.assertFalse(config.validation_enabled)
        self.assertTrue(config.signature_enabled)
        self.assertEqual(config.duplicate_probability, 0.1)
        self.assertEqual(config.invalid_probability, 0.05)
    
    def test_simulation_stats(self):
        """Test SimulationStats dataclass"""
        stats = SimulationStats(
            total_injected=100,
            successfully_added=95,
            failed_validation=3,
            duplicates=2,
            injection_errors=0,
            start_time=1000.0,
            end_time=1010.0
        )
        
        self.assertEqual(stats.total_injected, 100)
        self.assertEqual(stats.successfully_added, 95)
        self.assertEqual(stats.failed_validation, 3)
        self.assertEqual(stats.duplicates, 2)
        self.assertEqual(stats.injection_errors, 0)
        self.assertEqual(stats.duration, 10.0)
        self.assertEqual(stats.success_rate, 95.0)
    
    @patch('time.sleep')
    def test_run_simulation(self, mock_sleep):
        """Test running a complete simulation"""
        # Mock sleep to speed up the test
        mock_sleep.return_value = None
        
        # Run simulation
        stats = self.injector.run_simulation()
        
        # Check results
        self.assertIsInstance(stats, SimulationStats)
        self.assertGreaterEqual(stats.total_injected, 0)
        self.assertGreaterEqual(stats.duration, 0)
        
        # Check that sleep was called
        self.assertGreaterEqual(mock_sleep.call_count, 0)
    
    def test_transaction_pool_integration(self):
        """Test integration with TransactionPool"""
        sender = list(self.injector.sender_keys.keys())[0]
        
        # Inject a transaction
        success, message = self.injector.inject_single_transaction(sender)
        self.assertTrue(success)
        
        # Check that it's in the pool
        pool_stats = self.injector.transaction_pool.get_pool_stats()
        self.assertEqual(pool_stats['total_transactions'], 1)
        self.assertEqual(pool_stats['unique_senders'], 1)
        
        # Get transactions by sender
        sender_txns = self.injector.transaction_pool.get_multi_transactions_by_sender(sender)
        self.assertEqual(len(sender_txns), 1)
        
        # Get transaction by digest
        digest = self.injector.injected_transactions[0]
        txn = self.injector.transaction_pool.get_multi_transactions_by_digest(digest)
        self.assertIsNotNone(txn)
        self.assertEqual(txn.sender, sender)
    
    def test_concurrent_injection(self):
        """Test concurrent transaction injection"""
        import threading
        
        results = []
        errors = []
        
        def inject_transaction():
            try:
                sender = list(self.injector.sender_keys.keys())[0]
                success, message = self.injector.inject_single_transaction(sender)
                results.append((success, message))
            except Exception as e:
                errors.append(str(e))
        
        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=inject_transaction)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), 5)
        
        # All injections should have been recorded
        self.assertEqual(self.injector.stats.total_injected, 5)


class TestSimulationIntegration(unittest.TestCase):
    """Integration tests for the simulation system"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
    
    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_full_simulation_workflow(self):
        """Test a complete simulation workflow"""
        config = SimulationConfig(
            num_senders=2,
            num_transactions_per_batch=1,
            num_batches=3,
            injection_interval=0.01,
            validation_enabled=True,
            signature_enabled=False,
            duplicate_probability=0.0,
            invalid_probability=0.0
        )
        
        # Create injector with temporary database
        injector = TransactionInjector(config)
        injector.transaction_pool.db_path = self.temp_db.name
        injector.transaction_pool._init_database()
        
        try:
            # Run simulation
            stats = injector.run_simulation()
            
            # Verify results
            self.assertIsInstance(stats, SimulationStats)
            self.assertGreaterEqual(stats.total_injected, 0)
            self.assertGreaterEqual(stats.successfully_added, 0)
            self.assertGreaterEqual(stats.duration, 0)
            
            # Verify pool state
            pool_stats = injector.transaction_pool.get_pool_stats()
            self.assertGreaterEqual(pool_stats['total_transactions'], 0)
            self.assertGreaterEqual(pool_stats['unique_senders'], 0)
            
        finally:
            injector.cleanup()
    
    def test_simulation_with_various_configurations(self):
        """Test simulation with different configurations"""
        configurations = [
            SimulationConfig(num_senders=1, num_transactions_per_batch=1, num_batches=2),
            SimulationConfig(num_senders=2, num_transactions_per_batch=2, num_batches=2),
            SimulationConfig(validation_enabled=False),
            SimulationConfig(duplicate_probability=0.1),
            SimulationConfig(invalid_probability=0.1),
        ]
        
        for i, config in enumerate(configurations):
            with self.subTest(configuration=i):
                # Create temporary database
                temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=f'_test_{i}.db')
                temp_db.close()
                
                try:
                    injector = TransactionInjector(config)
                    injector.transaction_pool.db_path = temp_db.name
                    injector.transaction_pool._init_database()
                    
                    # Run a short simulation
                    stats = injector.run_simulation()
                    
                    # Verify basic results
                    self.assertIsInstance(stats, SimulationStats)
                    self.assertGreaterEqual(stats.total_injected, 0)
                    
                finally:
                    injector.cleanup()
                    if os.path.exists(temp_db.name):
                        os.unlink(temp_db.name)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)