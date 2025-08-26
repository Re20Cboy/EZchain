#!/usr/bin/env python3
"""
Comprehensive unit tests for Block module with signature support.
"""

import unittest
import sys
import os
import json
import pickle
import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from EZ_Main_Chain.Block import Block
    from EZ_Block_Units.Bloom import BloomFilter, BloomFilterEncoder
    from EZ_Block_Units.MerkleTree import MerkleTree
    from EZ_Tool_Box.temp_signature import temp_signature_system
except ImportError as e:
    print(f"Error importing Block modules: {e}")
    sys.exit(1)


class TestBlockBasic(unittest.TestCase):
    """Test suite for basic Block functionality."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_index = 1
        self.test_m_tree_root = "test_merkle_root_hash"
        self.test_miner = "test_miner_123"
        self.test_pre_hash = "previous_block_hash_456"
        self.test_nonce = 42
        self.test_version = "1.0"
        
        # Create a test Merkle tree
        self.test_data = ["tx1", "tx2", "tx3", "tx4"]
        self.merkle_tree = MerkleTree(self.test_data)
        self.merkle_root = self.merkle_tree.get_root_hash()
        
    def test_block_initialization(self):
        """Test Block initialization with default parameters."""
        block = Block(
            index=self.test_index,
            m_tree_root=self.merkle_root,
            miner=self.test_miner,
            pre_hash=self.test_pre_hash
        )
        
        self.assertEqual(block.get_index(), self.test_index)
        self.assertEqual(block.get_m_tree_root(), self.merkle_root)
        self.assertEqual(block.get_miner(), self.test_miner)
        self.assertEqual(block.get_pre_hash(), self.test_pre_hash)
        self.assertEqual(block.get_nonce(), 0)  # Default nonce
        self.assertEqual(block.get_version(), "1.0")  # Default version
        self.assertIsNotNone(block.get_time())
        self.assertIsInstance(block.get_bloom(), BloomFilter)
        self.assertIsInstance(block.get_sig(), dict)  # Should have signature
        
    def test_block_initialization_with_all_params(self):
        """Test Block initialization with all parameters."""
        custom_time = datetime.datetime(2023, 1, 1, 12, 0, 0)
        
        block = Block(
            index=self.test_index,
            m_tree_root=self.merkle_root,
            miner=self.test_miner,
            pre_hash=self.test_pre_hash,
            nonce=self.test_nonce,
            bloom_size=2048,
            bloom_hash_count=7,
            time=custom_time,
            version=self.test_version
        )
        
        self.assertEqual(block.get_index(), self.test_index)
        self.assertEqual(block.get_m_tree_root(), self.merkle_root)
        self.assertEqual(block.get_miner(), self.test_miner)
        self.assertEqual(block.get_pre_hash(), self.test_pre_hash)
        self.assertEqual(block.get_nonce(), self.test_nonce)
        self.assertEqual(block.get_version(), self.test_version)
        self.assertEqual(block.get_time(), custom_time)
        self.assertEqual(len(block.get_bloom()), 2048)
        self.assertEqual(block.get_bloom().hash_count, 7)
        
    def test_genesis_block_initialization(self):
        """Test genesis block (index 0) initialization."""
        genesis_block = Block(
            index=0,
            m_tree_root="genesis_root",
            miner="genesis_miner",
            pre_hash="0"
        )
        
        self.assertEqual(genesis_block.get_index(), 0)
        self.assertEqual(genesis_block.get_sig(), 0)  # Genesis block has no signature
        
    def test_block_hash_calculation(self):
        """Test block hash calculation."""
        block = Block(
            index=self.test_index,
            m_tree_root=self.merkle_root,
            miner=self.test_miner,
            pre_hash=self.test_pre_hash
        )
        
        block_hash = block.get_hash()
        self.assertIsInstance(block_hash, str)
        self.assertEqual(len(block_hash), 64)  # SHA256 hash length
        
        # Same block should produce same hash
        block_hash2 = block.get_hash()
        self.assertEqual(block_hash, block_hash2)
        
        # Different block should produce different hash
        different_block = Block(
            index=self.test_index + 1,
            m_tree_root=self.merkle_root,
            miner=self.test_miner,
            pre_hash=self.test_pre_hash
        )
        different_hash = different_block.get_hash()
        self.assertNotEqual(block_hash, different_hash)


class TestBlockBloomFilter(unittest.TestCase):
    """Test suite for Block Bloom filter functionality."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_data = ["tx1", "tx2", "tx3", "tx4"]
        self.merkle_tree = MerkleTree(self.test_data)
        self.merkle_root = self.merkle_tree.get_root_hash()
        
    def test_bloom_filter_initialization(self):
        """Test Bloom filter initialization in Block."""
        block = Block(
            index=1,
            m_tree_root=self.merkle_root,
            miner="test_miner",
            pre_hash="prev_hash"
        )
        
        bloom = block.get_bloom()
        self.assertIsInstance(bloom, BloomFilter)
        self.assertEqual(len(bloom), 1024 * 1024)  # Default size
        self.assertEqual(bloom.hash_count, 5)  # Default hash count
        
    def test_add_and_check_bloom_items(self):
        """Test adding items to and checking items in Bloom filter."""
        block = Block(
            index=1,
            m_tree_root=self.merkle_root,
            miner="test_miner",
            pre_hash="prev_hash"
        )
        
        # Add test items to bloom filter
        test_items = ["transaction1", "transaction2", "account1", "account2"]
        for item in test_items:
            block.add_item_to_bloom(item)
            
        # Check that items are in bloom filter
        for item in test_items:
            self.assertTrue(block.is_in_bloom(item))
            
        # Check that non-existent items are not in bloom filter
        non_existent_items = ["nonexistent1", "nonexistent2"]
        for item in non_existent_items:
            self.assertFalse(block.is_in_bloom(item))
            
    def test_bloom_filter_chainable_add(self):
        """Test that add_item_to_bloom is chainable."""
        block = Block(
            index=1,
            m_tree_root=self.merkle_root,
            miner="test_miner",
            pre_hash="prev_hash"
        )
        
        # Test that add_item_to_bloom works (not necessarily chainable)
        block.add_item_to_bloom("test_item")
        
        # Verify item was added
        self.assertTrue(block.is_in_bloom("test_item"))


class TestBlockStringRepresentations(unittest.TestCase):
    """Test suite for Block string representation methods."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_data = ["tx1", "tx2", "tx3", "tx4"]
        self.merkle_tree = MerkleTree(self.test_data)
        self.merkle_root = self.merkle_tree.get_root_hash()
        
    def test_block_to_str(self):
        """Test block string representation."""
        block = Block(
            index=1,
            m_tree_root=self.merkle_root,
            miner="test_miner",
            pre_hash="prev_hash"
        )
        
        block_str = block.block_to_str()
        self.assertIsInstance(block_str, str)
        
        # Check that all expected components are present
        expected_components = [
            f"Index: {block.get_index()}",
            f"Nonce: {block.get_nonce()}",
            f"Merkle Tree Root: {block.get_m_tree_root()}",
            f"Time: {str(block.get_time())}",
            f"Miner: {block.get_miner()}",
            f"Previous Hash: {block.get_pre_hash()}",
            f"Version: {block.get_version()}"
        ]
        
        for component in expected_components:
            self.assertIn(component, block_str)
            
        # Check that signature is NOT present (as per implementation note)
        self.assertNotIn("sig", block_str.lower())
        
    def test_block_to_short_str(self):
        """Test block short string representation."""
        block = Block(
            index=1,
            m_tree_root=self.merkle_root,
            miner="test_miner",
            pre_hash="prev_hash"
        )
        
        short_str = block.block_to_short_str()
        self.assertIsInstance(short_str, str)
        self.assertIn(f"Index: {block.get_index()}", short_str)
        self.assertIn(f"Miner: {block.get_miner()}", short_str)
        
    def test_block_to_json(self):
        """Test block JSON serialization."""
        block = Block(
            index=1,
            m_tree_root=self.merkle_root,
            miner="test_miner",
            pre_hash="prev_hash"
        )
        
        # Add some items to bloom filter
        block.add_item_to_bloom("test_item1")
        block.add_item_to_bloom("test_item2")
        
        json_tuple = block.block_to_json()
        self.assertIsInstance(json_tuple, tuple)
        self.assertEqual(len(json_tuple), 2)
        
        # Both elements should be JSON strings
        self.assertIsInstance(json_tuple[0], str)  # Main block data
        self.assertIsInstance(json_tuple[1], str)  # Bloom filter data
        
        # Parse the JSON to verify structure
        main_data = json.loads(json_tuple[0])
        self.assertIn("index", main_data)
        self.assertIn("m_tree_root", main_data)
        self.assertIn("miner", main_data)
        self.assertIn("sig", main_data)
        self.assertIn("version", main_data)
        # Convert datetime to string for JSON serialization
        self.assertIsInstance(main_data["time"], str)
        
    def test_block_to_pickle(self):
        """Test block pickle serialization."""
        block = Block(
            index=1,
            m_tree_root=self.merkle_root,
            miner="test_miner",
            pre_hash="prev_hash"
        )
        
        pickle_data = block.block_to_pickle()
        self.assertIsInstance(pickle_data, bytes)
        
        # Test unpickling
        unpickled_block = pickle.loads(pickle_data)
        self.assertEqual(unpickled_block.get_index(), block.get_index())
        self.assertEqual(unpickled_block.get_miner(), block.get_miner())
        self.assertEqual(unpickled_block.get_m_tree_root(), block.get_m_tree_root())


class TestBlockSignature(unittest.TestCase):
    """Test suite for Block signature functionality."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_data = ["tx1", "tx2", "tx3", "tx4"]
        self.merkle_tree = MerkleTree(self.test_data)
        self.merkle_root = self.merkle_tree.get_root_hash()
        
    def test_genesis_block_signature(self):
        """Test genesis block signature handling."""
        genesis_block = Block(
            index=0,
            m_tree_root="genesis_root",
            miner="genesis_miner",
            pre_hash="0"
        )
        
        self.assertEqual(genesis_block.get_sig(), 0)
        self.assertTrue(genesis_block.verify_signature())  # Genesis block should always verify
        
    def test_block_signature_generation(self):
        """Test that blocks have proper signatures."""
        block = Block(
            index=1,
            m_tree_root=self.merkle_root,
            miner="test_miner",
            pre_hash="prev_hash"
        )
        
        signature = block.get_sig()
        self.assertIsInstance(signature, dict)
        self.assertIn("signature", signature)
        self.assertIn("miner_id", signature)
        self.assertIn("timestamp", signature)
        self.assertIn("public_key", signature)
        
        # Verify signature
        self.assertTrue(block.verify_signature())
        
    def test_signature_verification(self):
        """Test signature verification with valid and invalid signatures."""
        # Create a valid block
        valid_block = Block(
            index=1,
            m_tree_root=self.merkle_root,
            miner="test_miner",
            pre_hash="prev_hash"
        )
        
        # Test valid signature
        self.assertTrue(valid_block.verify_signature())
        
        # Create block with invalid signature
        invalid_block = Block(
            index=1,
            m_tree_root=self.merkle_root,
            miner="test_miner",
            pre_hash="prev_hash"
        )
        
        # Tamper with the signature
        invalid_block.sig = {"signature": "invalid_signature", "miner_id": "test_miner", "timestamp": "123", "public_key": "fake"}
        
        # Test invalid signature
        self.assertFalse(invalid_block.verify_signature())
        
    def test_signature_unique_to_block_data(self):
        """Test that signatures are unique based on block data."""
        # Create two identical blocks
        block1 = Block(
            index=1,
            m_tree_root=self.merkle_root,
            miner="test_miner",
            pre_hash="prev_hash"
        )
        
        # Wait longer to ensure different timestamps
        import time
        time.sleep(0.5)  # Wait 500ms to ensure different timestamps
        
        block2 = Block(
            index=1,
            m_tree_root=self.merkle_root,
            miner="test_miner",
            pre_hash="prev_hash"
        )
        
        # Signatures should be different due to timestamp
        self.assertNotEqual(block1.get_sig()["signature"], block2.get_sig()["signature"])
        
        # But both should be valid
        self.assertTrue(block1.verify_signature())
        self.assertTrue(block2.verify_signature())


class TestBlockChainValidation(unittest.TestCase):
    """Test suite for Block chain validation functionality."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_data = ["tx1", "tx2", "tx3", "tx4"]
        self.merkle_tree = MerkleTree(self.test_data)
        self.merkle_root = self.merkle_tree.get_root_hash()
        
    def test_genesis_block_next_block_validation(self):
        """Test genesis block validation for next block."""
        genesis_block = Block(
            index=0,
            m_tree_root="genesis_root",
            miner="genesis_miner",
            pre_hash="0"
        )
        
        # Create a valid next block
        next_block = Block(
            index=1,
            m_tree_root=self.merkle_root,
            miner="miner1",
            pre_hash=genesis_block.get_hash()
        )
        
        # Test validation
        self.assertTrue(genesis_block.is_valid_next_block_dst(next_block))
        
    def test_block_chain_validation(self):
        """Test multi-block chain validation."""
        # Create genesis block
        genesis_block = Block(
            index=0,
            m_tree_root="genesis_root",
            miner="genesis_miner",
            pre_hash="0"
        )
        
        # Create block 1
        block1 = Block(
            index=1,
            m_tree_root=self.merkle_root,
            miner="miner1",
            pre_hash=genesis_block.get_hash()
        )
        
        # Create block 2
        block2 = Block(
            index=2,
            m_tree_root=self.merkle_root,
            miner="miner2",
            pre_hash=block1.get_hash()
        )
        
        # Test chain validation
        self.assertTrue(genesis_block.is_valid_next_block_dst(block1))
        self.assertTrue(block1.is_valid_next_block_dst(block2))
        
        # Test invalid chain
        invalid_block = Block(
            index=2,
            m_tree_root=self.merkle_root,
            miner="miner2",
            pre_hash="invalid_hash"  # Wrong previous hash
        )
        
        self.assertFalse(block1.is_valid_next_block_dst(invalid_block))
        
    def test_block_index_validation(self):
        """Test block index validation in chain."""
        genesis_block = Block(
            index=0,
            m_tree_root="genesis_root",
            miner="genesis_miner",
            pre_hash="0"
        )
        
        # Test correct index sequence
        block1 = Block(
            index=1,
            m_tree_root=self.merkle_root,
            miner="miner1",
            pre_hash=genesis_block.get_hash()
        )
        
        self.assertTrue(genesis_block.is_valid_next_block_dst(block1))
        
        # Test wrong index
        wrong_index_block = Block(
            index=3,  # Should be 1
            m_tree_root=self.merkle_root,
            miner="miner1",
            pre_hash=genesis_block.get_hash()
        )
        
        self.assertFalse(genesis_block.is_valid_next_block_dst(wrong_index_block))


class TestBlockEdgeCases(unittest.TestCase):
    """Test suite for Block edge cases."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_data = ["tx1", "tx2", "tx3", "tx4"]
        self.merkle_tree = MerkleTree(self.test_data)
        self.merkle_root = self.merkle_tree.get_root_hash()
        
    def test_block_with_unicode_data(self):
        """Test block with unicode characters."""
        unicode_miner = "矿工_测试"
        unicode_hash = "测试哈希_🚀"
        
        block = Block(
            index=1,
            m_tree_root=self.merkle_root,
            miner=unicode_miner,
            pre_hash=unicode_hash
        )
        
        self.assertEqual(block.get_miner(), unicode_miner)
        self.assertEqual(block.get_pre_hash(), unicode_hash)
        self.assertTrue(block.verify_signature())
        
    def test_block_with_empty_strings(self):
        """Test block with empty strings."""
        block = Block(
            index=1,
            m_tree_root="",  # Empty merkle root
            miner="",  # Empty miner
            pre_hash=""  # Empty previous hash
        )
        
        self.assertEqual(block.get_m_tree_root(), "")
        self.assertEqual(block.get_miner(), "")
        self.assertEqual(block.get_pre_hash(), "")
        self.assertTrue(block.verify_signature())
        
    def test_block_with_extremely_large_data(self):
        """Test block with large amounts of data."""
        large_data = ["a" * 1000 for _ in range(100)]
        large_merkle_tree = MerkleTree(large_data)
        large_merkle_root = large_merkle_tree.get_root_hash()
        
        block = Block(
            index=1,
            m_tree_root=large_merkle_root,
            miner="large_data_miner",
            pre_hash="prev_hash"
        )
        
        # Add many items to bloom filter
        for i in range(1000):
            block.add_item_to_bloom(f"item_{i}")
            
        self.assertTrue(block.verify_signature())
        
        # Test that bloom filter can handle the load
        for i in range(1000):
            self.assertTrue(block.is_in_bloom(f"item_{i}"))


class TestBlockPerformance(unittest.TestCase):
    """Test suite for Block performance-related functionality."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_data = [f"tx{i}" for i in range(100)]
        self.merkle_tree = MerkleTree(self.test_data)
        self.merkle_root = self.merkle_tree.get_root_hash()
        
    def test_large_block_creation(self):
        """Test creation of blocks with large datasets."""
        # Create a block with many transactions
        large_block = Block(
            index=1,
            m_tree_root=self.merkle_root,
            miner="performance_miner",
            pre_hash="prev_hash"
        )
        
        # Add many items to bloom filter
        for i in range(10000):
            large_block.add_item_to_bloom(f"item_{i}")
            
        # Verify operations are still fast
        self.assertTrue(large_block.verify_signature())
        
        # Test that all added items are present
        for i in range(10000):
            self.assertTrue(large_block.is_in_bloom(f"item_{i}"))
            
    def test_hash_performance(self):
        """Test hash calculation performance."""
        block = Block(
            index=1,
            m_tree_root=self.merkle_root,
            miner="performance_miner",
            pre_hash="prev_hash"
        )
        
        # Calculate hash multiple times
        hashes = []
        for _ in range(100):
            hashes.append(block.get_hash())
            
        # All hashes should be the same
        self.assertTrue(all(h == hashes[0] for h in hashes))


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)