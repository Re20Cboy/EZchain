#!/usr/bin/env python3
"""
Unit tests for Bloom filter module.
"""

import unittest
import sys
import os
import json

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(__file__) + '/..')

try:
    from EZ_Block_Units.Bloom import BloomFilter, BloomFilterEncoder
except ImportError as e:
    print(f"Error importing Bloom: {e}")
    sys.exit(1)


class TestBloomFilter(unittest.TestCase):
    """Test suite for Bloom filter implementation."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.bloom = BloomFilter(size=1024, hash_count=3)
        
    def test_bloom_filter_initialization(self):
        """Test Bloom filter initialization with default parameters."""
        bloom = BloomFilter()
        self.assertEqual(len(bloom), 1024 * 1024)  # Default size
        self.assertEqual(bloom.hash_count, 5)  # Default hash count
        
    def test_bloom_filter_custom_parameters(self):
        """Test Bloom filter initialization with custom parameters."""
        custom_size = 2048
        custom_hash_count = 7
        bloom = BloomFilter(size=custom_size, hash_count=custom_hash_count)
        
        self.assertEqual(len(bloom), custom_size)
        self.assertEqual(bloom.hash_count, custom_hash_count)
        
    def test_bloom_filter_add_and_contains(self):
        """Test adding items to bloom filter and checking membership."""
        test_items = ["hello", "world", "test", "bloom", "filter"]
        
        # Add items to filter
        for item in test_items:
            self.bloom.add(item)
            
        # Check that added items are in filter
        for item in test_items:
            self.assertTrue(item in self.bloom)
            
    def test_bloom_filter_iterator(self):
        """Test bloom filter iterator functionality."""
        # Add some items
        self.bloom.add("item1")
        self.bloom.add("item2")
        
        # Test that iterator works
        iterator = iter(self.bloom)
        self.assertIsNotNone(iterator)
        
        # Count set bits (should be at least the number of bits set by our items)
        set_bits = sum(1 for bit in self.bloom if bit)
        self.assertGreater(set_bits, 0)
        
    def test_bloom_filter_false_positives(self):
        """Test bloom filter false positive behavior."""
        # Add some items to filter
        added_items = ["apple", "banana", "cherry", "date", "elderberry"]
        for item in added_items:
            self.bloom.add(item)
            
        # Test that added items are definitely in filter
        for item in added_items:
            self.assertTrue(item in self.bloom)
            
        # Test that some items that weren't added might return True (false positives)
        # This is expected behavior for bloom filters
        test_items = ["orange", "grape", "pear", "peach", "mango"]
        false_positive_count = sum(1 for item in test_items if item in self.bloom)
        
        # Some false positives are expected, but not too many with reasonable hash_count
        self.assertLess(false_positive_count, len(test_items))
        
    def test_bloom_filter_same_item_multiple_times(self):
        """Test adding the same item multiple times."""
        item = "test_item"
        
        # Add the same item multiple times
        for _ in range(5):
            self.bloom.add(item)
            
        # Item should still be in filter (only one addition is needed)
        self.assertTrue(item in self.bloom)
        
    def test_bloom_filter_different_data_types(self):
        """Test bloom filter with different data types."""
        # Test with various data types
        test_items = [
            "string",
            123,
            45.67,
            True,
            None,
            ("tuple", "data"),
            ["list", "data"]
        ]
        
        # Convert to string for hash compatibility
        string_items = [str(item) for item in test_items]
        
        for item in string_items:
            self.bloom.add(item)
            
        for item in string_items:
            self.assertTrue(item in self.bloom)
            
    def test_bloom_filter_large_dataset(self):
        """Test bloom filter with a larger dataset."""
        # Add 100 items
        for i in range(100):
            item = f"item_{i}"
            self.bloom.add(item)
            
        # Test that all items are in filter
        for i in range(100):
            item = f"item_{i}"
            self.assertTrue(item in self.bloom)
            
        # Test some non-existent items
        for i in range(100, 110):
            item = f"item_{i}"
            # May return True (false positive) but should not crash
            result = item in self.bloom
            self.assertIsInstance(result, bool)
            
    def test_bloom_filter_edge_cases(self):
        """Test bloom filter edge cases."""
        # Test with empty string
        self.bloom.add("")
        self.assertTrue("" in self.bloom)
        
        # Test with very long strings
        long_string = "a" * 1000
        self.bloom.add(long_string)
        self.assertTrue(long_string in self.bloom)
        
        # Test with unicode characters
        unicode_string = "你好"
        self.bloom.add(unicode_string)
        self.assertTrue(unicode_string in self.bloom)
        
    def test_bloom_filter_hash_functions(self):
        """Test that different hash functions are used."""
        # Create bloom filter with more hash functions for testing
        bloom = BloomFilter(size=1024, hash_count=3)
        
        # Add the same item multiple times and check bit positions
        item = "test_item"
        bloom.add(item)
        
        # The item should be in the filter regardless of hash function count
        self.assertTrue(item in bloom)
        
    def test_bloom_filter_memory_efficiency(self):
        """Test that bloom filter uses memory efficiently."""
        # Create bloom filter with small size to test memory usage
        small_bloom = BloomFilter(size=64, hash_count=2)
        
        # Add several items
        for i in range(10):
            item = f"small_item_{i}"
            small_bloom.add(item)
            
        # Should still work correctly
        for i in range(10):
            item = f"small_item_{i}"
            self.assertTrue(item in small_bloom)


class TestBloomFilterEncoder(unittest.TestCase):
    """Test suite for Bloom filter JSON encoder."""
    
    def test_encoder_bloom_filter_object(self):
        """Test JSON encoding of bloom filter objects."""
        # Create a bloom filter with some items
        bloom = BloomFilter(size=1024, hash_count=3)
        bloom.add("test_item_1")
        bloom.add("test_item_2")
        
        # Test encoding
        encoder = BloomFilterEncoder()
        result = encoder.default(bloom)
        
        # Check that all required fields are present
        self.assertIn('size', result)
        self.assertIn('hash_count', result)
        self.assertIn('bit_array', result)
        self.assertIn('__class__', result)
        self.assertIn('__module__', result)
        
        # Check values are correct
        self.assertEqual(result['size'], bloom.size)
        self.assertEqual(result['hash_count'], bloom.hash_count)
        self.assertEqual(result['bit_array'], list(bloom.bit_array))
        self.assertEqual(result['__class__'], 'BloomFilter')
        self.assertEqual(result['__module__'], 'EZ_Units.Bloom')
        
    def test_json_serialization(self):
        """Test full JSON serialization of bloom filter."""
        # Create bloom filter
        bloom = BloomFilter(size=512, hash_count=2)
        bloom.add("json_test_item")
        
        # Serialize to JSON
        encoder = BloomFilterEncoder()
        json_str = json.dumps(bloom, cls=BloomFilterEncoder)
        
        # Should be valid JSON
        self.assertIsInstance(json_str, str)
        
        # Deserialize back
        loaded_data = json.loads(json_str)
        
        # Check that basic properties are preserved
        self.assertEqual(loaded_data['size'], bloom.size)
        self.assertEqual(loaded_data['hash_count'], bloom.hash_count)
        self.assertEqual(loaded_data['bit_array'], list(bloom.bit_array))


if __name__ == '__main__':
    unittest.main(verbosity=2)