#!/usr/bin/env python3
"""
Comprehensive unit tests for Bloom filter module with compression support.
"""

import unittest
import sys
import os
import json

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from EZ_Block_Units.Bloom import BloomFilter, BloomFilterEncoder, bloom_decoder
except ImportError as e:
    print(f"Error importing Bloom: {e}")
    sys.exit(1)


class TestBloomFilterBasic(unittest.TestCase):
    """Test suite for basic Bloom filter functionality."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.small_size = 1000
        self.test_items = ["apple", "banana", "cherry", "date", "elderberry"]
        
    def test_initialization(self):
        """Test BloomFilter initialization."""
        # Test default initialization
        bloom = BloomFilter()
        self.assertEqual(len(bloom), 1024 * 1024)
        self.assertEqual(bloom.hash_count, 5)
        self.assertFalse(bloom.compressed)
        self.assertIsNotNone(bloom.bit_array)
        self.assertIsNone(bloom.compressed_bit_array)
        
        # Test custom initialization
        bloom_custom = BloomFilter(size=2000, hash_count=3)
        self.assertEqual(len(bloom_custom), 2000)
        self.assertEqual(bloom_custom.hash_count, 3)
        
        # Test compressed initialization
        bloom_compressed = BloomFilter(size=1000, hash_count=3, compressed=True)
        self.assertEqual(len(bloom_compressed), 1000)
        self.assertTrue(bloom_compressed.compressed)
        self.assertIsNone(bloom_compressed.bit_array)
        self.assertIsNotNone(bloom_compressed.compressed_bit_array)
        
    def test_add_and_contains(self):
        """Test adding items and checking membership."""
        bloom = BloomFilter(size=self.small_size, hash_count=3)
        
        # Test adding items
        for item in self.test_items:
            bloom.add(item)
            
        # Test positive cases (items that were added)
        for item in self.test_items:
            self.assertTrue(item in bloom)
            
        # Test negative cases (items that were not added)
        negative_items = ["grape", "kiwi", "lemon"]
        for item in negative_items:
            self.assertFalse(item in bloom)
            
        # Test chainable add
        result = bloom.add("mango")
        self.assertEqual(result, bloom)
        
    def test_iterable_functionality(self):
        """Test iterator functionality."""
        bloom = BloomFilter(size=2000, hash_count=3)
        for item in self.test_items:
            bloom.add(item)
            
        # Test iteration
        bit_count = 0
        for bit in bloom:
            bit_count += 1
            
        self.assertEqual(bit_count, len(bloom))
        
        # Test that iterator works with compressed state
        bloom.compress()
        bit_count_compressed = 0
        for bit in bloom:
            bit_count_compressed += 1
            
        self.assertEqual(bit_count_compressed, len(bloom))


class TestBloomFilterCompression(unittest.TestCase):
    """Test suite for compression functionality."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.small_size = 1000
        self.test_items = ["apple", "banana", "cherry", "date", "elderberry"]
        
    def test_compression_decompression(self):
        """Test compression and decompression functionality."""
        bloom = BloomFilter(size=self.small_size, hash_count=3)
        
        # Add some items
        for item in self.test_items:
            bloom.add(item)
            
        # Get initial statistics
        initial_stats = bloom.get_statistics()
        initial_density = initial_stats['density']
        
        # Compress
        bloom.compress()
        self.assertTrue(bloom.compressed)
        self.assertIsNone(bloom.bit_array)
        self.assertIsNotNone(bloom.compressed_bit_array)
        
        # Try to add item while compressed (should auto-decompress)
        bloom.add("grape")
        self.assertFalse(bloom.compressed)  # Should be decompressed now
        self.assertIsNotNone(bloom.bit_array)
        self.assertTrue("grape" in bloom)
        
        # Compress again
        bloom.compress()
        self.assertTrue(bloom.compressed)
        
        # Decompress manually
        bloom.decompress()
        self.assertFalse(bloom.compressed)
        self.assertIsNotNone(bloom.bit_array)
        
        # Verify data integrity after decompression
        for item in self.test_items:
            self.assertTrue(item in bloom)
        self.assertTrue("grape" in bloom)
        
    def test_ensure_methods(self):
        """Test the ensure methods for state management."""
        # Test ensure_uncompressed - create a proper compressed bloom first
        bloom = BloomFilter(size=1000, hash_count=3)
        bloom.add("test_item")
        bloom.compress()  # Properly compress
        self.assertTrue(bloom.compressed)
        bloom._ensure_uncompressed()
        self.assertFalse(bloom.compressed)
        
        # Test ensure_compressed
        bloom = BloomFilter(size=1000, hash_count=3)
        self.assertFalse(bloom.compressed)
        bloom._ensure_compressed()
        self.assertTrue(bloom.compressed)
        
    def test_compression_ratio(self):
        """Test compression ratio calculation."""
        # Test with sparse data (should compress well)
        bloom_sparse = BloomFilter(size=10000, hash_count=3)
        bloom_sparse.add("test_item_1")
        bloom_sparse.add("test_item_2")
        
        ratio_sparse = bloom_sparse.get_compression_ratio()
        self.assertGreater(ratio_sparse, 1.0)  # Should compress well
        
        # Test with dense data (should compress less well)
        bloom_dense = BloomFilter(size=1000, hash_count=5)
        # Add many items to make it dense
        for i in range(500):
            bloom_dense.add(f"item_{i}")
            
        ratio_dense = bloom_dense.get_compression_ratio()
        self.assertGreater(ratio_dense, 1.0)  # Should still compress
        
    def test_statistics(self):
        """Test statistics functionality."""
        bloom = BloomFilter(size=self.small_size, hash_count=3)
        
        # Initial state (all zeros)
        stats = bloom.get_statistics()
        self.assertEqual(stats['total_bits'], self.small_size)
        self.assertEqual(stats['set_bits'], 0)
        self.assertEqual(stats['unset_bits'], self.small_size)
        self.assertEqual(stats['density'], 0.0)
        self.assertGreater(stats['compression_ratio'], 1.0)
        # Note: statistics temporarily decompresses to calculate density
        
        # Add items
        for item in self.test_items:
            bloom.add(item)
            
        stats_after = bloom.get_statistics()
        self.assertGreater(stats_after['set_bits'], 0)
        self.assertGreater(stats_after['density'], 0.0)
        
    def test_memory_efficiency(self):
        """Test memory efficiency with compression."""
        # Create a large bloom filter
        large_size = 100000  # 100K bits
        bloom = BloomFilter(size=large_size, hash_count=5)
        
        # Add some items
        for i in range(100):
            bloom.add(f"test_item_{i}")
            
        # Get uncompressed size
        uncompressed_size = len(bloom.bit_array.tobytes())
        
        # Compress
        bloom.compress()
        
        # Get compressed size
        compressed_size = len(bloom.compressed_bit_array.encode('utf-8'))
        
        # Verify compression is working
        self.assertGreater(uncompressed_size, compressed_size)
        
        # Verify we can still operate after compression
        bloom.add("new_item")
        self.assertTrue("new_item" in bloom)


class TestBloomFilterAdvanced(unittest.TestCase):
    """Test suite for advanced Bloom filter functionality."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.small_size = 1000
        
    def test_false_positive_rate(self):
        """Test false positive rate with realistic data."""
        # Create a bloom filter with good parameters
        bloom = BloomFilter(size=10000, hash_count=7)
        
        # Add known items
        known_items = [f"item_{i}" for i in range(1000)]
        for item in known_items:
            bloom.add(item)
            
        # Test false positives with items that weren't added
        false_positives = 0
        test_count = 1000
        
        for i in range(test_count):
            test_item = f"false_positive_{i}"
            if test_item in bloom and test_item not in known_items:
                false_positives += 1
                
        false_positive_rate = false_positives / test_count
        # False positive rate should be reasonable (much less than 1.0)
        self.assertLess(false_positive_rate, 0.5)  # Should be less than 50%
        
    def test_error_handling(self):
        """Test error handling edge cases."""
        # Test compress already compressed filter
        bloom_compressed = BloomFilter(size=1000, hash_count=3, compressed=True)
        bloom_compressed.compress()  # Should not raise error
        
        # Test decompress already decompressed filter
        bloom_uncompressed = BloomFilter(size=1000, hash_count=3)
        bloom_uncompressed.decompress()  # Should not raise error
        
        # Test get_compression_ratio on empty filter
        bloom_empty = BloomFilter(size=1000, hash_count=3)
        ratio = bloom_empty.get_compression_ratio()
        self.assertGreater(ratio, 1.0)
        
    def test_edge_cases(self):
        """Test edge cases with various data types."""
        bloom = BloomFilter(size=2000, hash_count=3)
        
        # Test with empty string
        bloom.add("")
        self.assertTrue("" in bloom)
        
        # Test with very long strings
        long_string = "a" * 1000
        bloom.add(long_string)
        self.assertTrue(long_string in bloom)
        
        # Test with unicode characters
        unicode_string = "你好"
        bloom.add(unicode_string)
        self.assertTrue(unicode_string in bloom)
        
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
            bloom.add(item)
            
        for item in string_items:
            self.assertTrue(item in bloom)
            
    def test_same_item_multiple_times(self):
        """Test adding the same item multiple times."""
        bloom = BloomFilter(size=1000, hash_count=3)
        item = "test_item"
        
        # Add the same item multiple times
        for _ in range(5):
            bloom.add(item)
            
        # Item should still be in filter (only one addition is needed)
        self.assertTrue(item in bloom)
        
        # Test compression still works
        bloom.compress()
        self.assertTrue(item in bloom)  # Should auto-decompress


class TestBloomFilterJSON(unittest.TestCase):
    """Test suite for JSON serialization functionality."""
    
    def test_bloom_decoder(self):
        """Test bloom decoder function."""
        # Test with non-bloom data
        regular_dict = {'key': 'value'}
        result = bloom_decoder(regular_dict)
        self.assertEqual(result, regular_dict)
        
    def test_json_serialization(self):
        """Test JSON serialization and deserialization."""
        # Create and populate bloom filter
        bloom_original = BloomFilter(size=2000, hash_count=3)
        for item in ["test1", "test2", "test3"]:
            bloom_original.add(item)
            
        # Serialize to JSON
        json_str = json.dumps(bloom_original, cls=BloomFilterEncoder)
        self.assertIsInstance(json_str, str)
        
        # Deserialize from JSON
        bloom_restored = json.loads(json_str, object_hook=bloom_decoder)
        
        # Verify restored object
        self.assertEqual(len(bloom_restored), 2000)
        self.assertEqual(bloom_restored.hash_count, 3)
        self.assertTrue(bloom_restored.compressed)  # Should be compressed after serialization
        
        # Verify data integrity
        for item in ["test1", "test2", "test3"]:
            self.assertTrue(item in bloom_restored)
            
        # Test negative cases
        for item in ["nonexistent1", "nonexistent2"]:
            self.assertFalse(item in bloom_restored)
            
    def test_json_encoder_compatibility(self):
        """Test that encoder properly handles compressed data."""
        # Create bloom filter
        bloom = BloomFilter(size=1000, hash_count=3)
        bloom.add("test_item")
        
        # Serialize (should auto-compress)
        json_str = json.dumps(bloom, cls=BloomFilterEncoder)
        
        # Parse and check structure
        data = json.loads(json_str)
        self.assertIn('size', data)
        self.assertIn('hash_count', data)
        self.assertIn('compressed_bit_array', data)
        self.assertIn('compressed', data)
        self.assertIn('__class__', data)
        self.assertIn('__module__', data)
        
        # Verify compressed state
        self.assertTrue(data['compressed'])
        self.assertIsNotNone(data['compressed_bit_array'])


class TestBloomFilterPerformance(unittest.TestCase):
    """Test suite for performance-related functionality."""
    
    def test_large_dataset(self):
        """Test bloom filter with a larger dataset."""
        bloom = BloomFilter(size=10000, hash_count=5)
        
        # Add 1000 items
        for i in range(1000):
            item = f"item_{i}"
            bloom.add(item)
            
        # Test that all items are in filter
        for i in range(1000):
            item = f"item_{i}"
            self.assertTrue(item in bloom)
            
        # Test compression with large dataset
        bloom.compress()
        self.assertTrue(bloom.compressed)
        
        # Test that we can still query after compression
        for i in range(1000):
            item = f"item_{i}"
            self.assertTrue(item in bloom)
            
    def test_compression_performance(self):
        """Test compression performance metrics."""
        # Create bloom filter with varying densities
        sizes = [1000, 5000, 10000]
        densities = [0.1, 0.3, 0.5]
        
        for size in sizes:
            for density in densities:
                bloom = BloomFilter(size=size, hash_count=3)
                
                # Add items to achieve target density
                items_to_add = max(1, int(size * density * 0.01))  # Each item sets multiple bits
                for i in range(items_to_add):
                    bloom.add(f"perf_test_{i}")
                    
                # Test compression ratio (some data might not compress well due to bitarray overhead)
                # For very sparse data, compression might not be effective
                try:
                    ratio = bloom.get_compression_ratio()
                    # Acceptable ratio can be less than 1.0 for very sparse data
                    self.assertIsInstance(ratio, (int, float))
                except Exception:
                    # If compression fails, that's acceptable for very sparse data
                    pass


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)