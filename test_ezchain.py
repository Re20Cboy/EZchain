#!/usr/bin/env python3
"""
Comprehensive test suite for EZchain blockchain project.
This test file covers all existing and future code in the project.
"""

import unittest
import sys
import os
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'EZ_main_chain'))

try:
    from Block import Block
except ImportError as e:
    print(f"Error importing Block: {e}")
    sys.exit(1)


class TestEZchain(unittest.TestCase):
    """Test suite for EZchain blockchain components."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_miner = "test_miner_123"
        self.test_prev_hash = "0" * 64  # Genesis block hash
        self.test_merkle_root = "test_merkle_root_hash"
        self.test_time = datetime(2024, 1, 1, 12, 0, 0)
        
    def test_block_initialization(self):
        """Test Block class initialization with various parameters."""
        # Test basic initialization
        block = Block(
            index=1,
            m_tree_root=self.test_merkle_root,
            miner=self.test_miner,
            pre_hash=self.test_prev_hash
        )
        
        self.assertEqual(block.get_index(), 1)
        self.assertEqual(block.get_miner(), self.test_miner)
        self.assertEqual(block.get_pre_hash(), self.test_prev_hash)
        self.assertEqual(block.get_m_tree_root(), self.test_merkle_root)
        self.assertEqual(block.get_nonce(), 0)
        self.assertIsInstance(block.get_time(), datetime)
        
    def test_block_with_custom_parameters(self):
        """Test Block initialization with custom parameters."""
        custom_nonce = 42
        custom_time = datetime(2024, 6, 15, 14, 30, 0)
        
        block = Block(
            index=2,
            m_tree_root="custom_merkle",
            miner="custom_miner",
            pre_hash="prev_hash",
            nonce=custom_nonce,
            time=custom_time
        )
        
        self.assertEqual(block.get_index(), 2)
        self.assertEqual(block.get_nonce(), custom_nonce)
        self.assertEqual(block.get_time(), custom_time)
        
    def test_block_hash_generation(self):
        """Test block hash generation."""
        block = Block(
            index=1,
            m_tree_root=self.test_merkle_root,
            miner=self.test_miner,
            pre_hash=self.test_prev_hash
        )
        
        # Hash should be deterministic for the same block
        hash1 = block.get_hash()
        hash2 = block.get_hash()
        self.assertEqual(hash1, hash2)
        
        # Hash should be a SHA-256 hex string (64 characters)
        self.assertEqual(len(hash1), 64)
        self.assertTrue(all(c in '0123456789abcdef' for c in hash1))
        
    def test_block_to_str(self):
        """Test block string representation."""
        block = Block(
            index=1,
            m_tree_root=self.test_merkle_root,
            miner=self.test_miner,
            pre_hash=self.test_prev_hash
        )
        
        block_str = block.block_to_str()
        self.assertIsInstance(block_str, str)
        self.assertIn(f"Index: {block.get_index()}", block_str)
        self.assertIn(f"Nonce: {block.get_nonce()}", block_str)
        self.assertIn(f"Miner: {block.get_miner()}", block_str)
        self.assertIn(f"Previous Hash: {block.get_pre_hash()}", block_str)
        
    def test_block_to_short_str(self):
        """Test short string representation of block."""
        block = Block(
            index=42,
            m_tree_root=self.test_merkle_root,
            miner=self.test_miner,
            pre_hash=self.test_prev_hash
        )
        
        short_str = block.block_to_short_str()
        expected_str = f"Index: {block.get_index()}, Miner: {block.get_miner()}"
        self.assertEqual(short_str, expected_str)
        
    def test_block_json_serialization(self):
        """Test block JSON serialization."""
        block = Block(
            index=1,
            m_tree_root=self.test_merkle_root,
            miner=self.test_miner,
            pre_hash=self.test_prev_hash
        )
        
        # Add some items to bloom filter
        block.add_item_to_bloom("test_item_1")
        block.add_item_to_bloom("test_item_2")
        
        json_data = block.block_to_json()
        self.assertIsInstance(json_data, tuple)
        self.assertEqual(len(json_data), 2)
        
        # Both elements should be JSON strings
        for element in json_data:
            self.assertIsInstance(element, str)
            # Should be valid JSON
            import json
            json.loads(element)
            
    def test_block_pickle_serialization(self):
        """Test block pickle serialization."""
        block = Block(
            index=1,
            m_tree_root=self.test_merkle_root,
            miner=self.test_miner,
            pre_hash=self.test_prev_hash
        )
        
        pickle_data = block.block_to_pickle()
        self.assertIsInstance(pickle_data, bytes)
        
        # Test deserialization
        import pickle
        deserialized_block = pickle.loads(pickle_data)
        self.assertEqual(deserialized_block.get_index(), block.get_index())
        self.assertEqual(deserialized_block.get_miner(), block.get_miner())
        self.assertEqual(deserialized_block.get_pre_hash(), block.get_pre_hash())
        
    def test_bloom_filter_operations(self):
        """Test Bloom filter functionality."""
        block = Block(
            index=1,
            m_tree_root=self.test_merkle_root,
            miner=self.test_miner,
            pre_hash=self.test_prev_hash
        )
        
        # Test adding items to bloom filter
        test_items = ["item1", "item2", "item3"]
        for item in test_items:
            block.add_item_to_bloom(item)
            
        # Test checking items in bloom filter
        for item in test_items:
            self.assertTrue(block.is_in_bloom(item))
            
        # Test that non-existent items return False (may have false positives)
        self.assertFalse(block.is_in_bloom("nonexistent_item"))
        
    def test_next_block_validation(self):
        """Test validation of next block in chain."""
        # Create current block
        current_block = Block(
            index=1,
            m_tree_root=self.test_merkle_root,
            miner=self.test_miner,
            pre_hash=self.test_prev_hash
        )
        
        # Create next block
        next_block = Block(
            index=2,
            m_tree_root="next_merkle",
            miner="next_miner",
            pre_hash=current_block.get_hash()
        )
        
        # Test valid next block
        self.assertTrue(current_block.is_valid_next_block_dst(next_block))
        
        # Test invalid next block (wrong index)
        invalid_block = Block(
            index=4,  # Wrong index (should be 2)
            m_tree_root="next_merkle",
            miner="next_miner",
            pre_hash=current_block.get_hash()
        )
        self.assertFalse(current_block.is_valid_next_block_dst(invalid_block))
        
        # Test invalid next block (wrong previous hash)
        invalid_block2 = Block(
            index=2,
            m_tree_root="next_merkle",
            miner="next_miner",
            pre_hash="wrong_hash"
        )
        self.assertFalse(current_block.is_valid_next_block_dst(invalid_block2))
        
    def test_genesis_block(self):
        """Test genesis block (index 0) characteristics."""
        genesis_block = Block(
            index=0,
            m_tree_root="genesis_merkle",
            miner="genesis_miner",
            pre_hash="0" * 64
        )
        
        self.assertEqual(genesis_block.get_index(), 0)
        self.assertEqual(genesis_block.get_sig(), 0)  # Genesis block has no signature
        
    def test_time_handling(self):
        """Test timestamp handling in blocks."""
        custom_time = datetime(2023, 12, 25, 18, 45, 30)
        
        block = Block(
            index=1,
            m_tree_root=self.test_merkle_root,
            miner=self.test_miner,
            pre_hash=self.test_prev_hash,
            time=custom_time
        )
        
        self.assertEqual(block.get_time(), custom_time)
        
    def test_getter_methods(self):
        """Test all getter methods return expected values."""
        block = Block(
            index=99,
            m_tree_root="test_root",
            miner="miner_99",
            pre_hash="prev_99",
            nonce=123
        )
        
        self.assertEqual(block.get_index(), 99)
        self.assertEqual(block.get_nonce(), 123)
        self.assertEqual(block.get_m_tree_root(), "test_root")
        self.assertEqual(block.get_miner(), "miner_99")
        self.assertEqual(block.get_pre_hash(), "prev_99")
        self.assertIsInstance(block.get_time(), datetime)
        self.assertIsInstance(block.get_bloom(), type)  # Bloom filter object
        self.assertIsInstance(block.get_sig(), int)  # Should be integer signature
        
    def test_error_handling(self):
        """Test error handling and edge cases."""
        # Test with very long strings
        long_miner = "miner_" + "a" * 1000
        long_hash = "a" * 1000
        long_merkle = "b" * 1000
        
        block = Block(
            index=1,
            m_tree_root=long_merkle,
            miner=long_miner,
            pre_hash=long_hash
        )
        
        # Should handle large data without crashing
        self.assertIsNotNone(block.get_hash())
        self.assertIsNotNone(block.block_to_str())
        self.assertIsNotNone(block.block_to_json())


class TestIntegration(unittest.TestCase):
    """Integration tests for blockchain components."""
    
    def test_blockchain_sequence(self):
        """Test creating a sequence of blocks that form a valid blockchain."""
        blocks = []
        prev_hash = "0" * 64  # Genesis block hash
        
        for i in range(5):
            block = Block(
                index=i,
                m_tree_root=f"merkle_{i}",
                miner=f"miner_{i}",
                pre_hash=prev_hash
            )
            
            # Verify the block is valid
            self.assertEqual(block.get_index(), i)
            self.assertEqual(block.get_pre_hash(), prev_hash)
            
            blocks.append(block)
            prev_hash = block.get_hash()
            
        # Verify the chain is valid
        for i in range(len(blocks) - 1):
            current_block = blocks[i]
            next_block = blocks[i + 1]
            self.assertTrue(current_block.is_valid_next_block_dst(next_block))
            
    def test_hash_consistency(self):
        """Test that hash generation is consistent across multiple calls."""
        block = Block(
            index=1,
            m_tree_root=self.test_merkle_root,
            miner=self.test_miner,
            pre_hash=self.test_prev_hash
        )
        
        # Hash should be the same across multiple calls
        hash1 = block.get_hash()
        hash2 = block.get_hash()
        hash3 = block.get_hash()
        
        self.assertEqual(hash1, hash2)
        self.assertEqual(hash2, hash3)


def run_tests():
    """Run all tests and return results."""
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(unittest.makeSuite(TestEZchain))
    suite.addTest(unittest.makeSuite(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == '__main__':
    print("Starting EZchain Test Suite...")
    print("=" * 50)
    
    # Run tests
    result = run_tests()
    
    print("\n" + "=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
            
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
            
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)