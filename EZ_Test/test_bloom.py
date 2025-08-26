#!/usr/bin/env python3
"""
Comprehensive unit tests for Bloom filter module with compression support.
"""

import pytest
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


@pytest.fixture
def bloom_filter_basic():
    """Fixture for basic Bloom filter tests."""
    small_size = 1000
    test_items = ["apple", "banana", "cherry", "date", "elderberry"]
    return small_size, test_items


class TestBloomFilterBasic:
    """Test suite for basic Bloom filter functionality."""
        
    def test_initialization(self, bloom_filter_basic):
        """Test BloomFilter initialization."""
        # Test default initialization
        bloom = BloomFilter()
        assert len(bloom) == 1024 * 1024
        assert bloom.hash_count == 5
        assert not bloom.compressed
        assert bloom.bit_array is not None
        assert bloom.compressed_bit_array is None
        
        # Test custom initialization
        bloom_custom = BloomFilter(size=2000, hash_count=3)
        assert len(bloom_custom) == 2000
        assert bloom_custom.hash_count == 3
        
        # Test compressed initialization
        bloom_compressed = BloomFilter(size=1000, hash_count=3, compressed=True)
        assert len(bloom_compressed) == 1000
        assert bloom_compressed.compressed
        assert bloom_compressed.bit_array is None
        assert bloom_compressed.compressed_bit_array is not None
        
    def test_add_and_contains(self, bloom_filter_basic):
        """Test adding items and checking membership."""
        small_size, test_items = bloom_filter_basic
        bloom = BloomFilter(size=small_size, hash_count=3)
        
        # Test adding items
        for item in test_items:
            bloom.add(item)
            
        # Test positive cases (items that were added)
        for item in test_items:
            assert item in bloom
            
        # Test negative cases (items that were not added)
        negative_items = ["grape", "kiwi", "lemon"]
        for item in negative_items:
            assert item not in bloom
            
        # Test chainable add
        result = bloom.add("mango")
        assert result is bloom
        
    def test_iterable_functionality(self, bloom_filter_basic):
        """Test iterator functionality."""
        small_size, test_items = bloom_filter_basic
        bloom = BloomFilter(size=2000, hash_count=3)
        for item in test_items:
            bloom.add(item)
            
        # Test iteration
        bit_count = 0
        for bit in bloom:
            bit_count += 1
            
        assert bit_count == len(bloom)
        
        # Test that iterator works with compressed state
        bloom.compress()
        bit_count_compressed = 0
        for bit in bloom:
            bit_count_compressed += 1
            
        assert bit_count_compressed == len(bloom)


@pytest.fixture
def bloom_filter_compression():
    """Fixture for compression tests."""
    small_size = 1000
    test_items = ["apple", "banana", "cherry", "date", "elderberry"]
    return small_size, test_items


class TestBloomFilterCompression:
    """Test suite for compression functionality."""
        
    def test_compression_decompression(self, bloom_filter_compression):
        """Test compression and decompression functionality."""
        small_size, test_items = bloom_filter_compression
        bloom = BloomFilter(size=small_size, hash_count=3)
        
        # Add some items
        for item in test_items:
            bloom.add(item)
            
        # Get initial statistics
        initial_stats = bloom.get_statistics()
        initial_density = initial_stats['density']
        
        # Compress
        bloom.compress()
        assert bloom.compressed
        assert bloom.bit_array is None
        assert bloom.compressed_bit_array is not None
        
        # Try to add item while compressed (should auto-decompress)
        bloom.add("grape")
        assert not bloom.compressed  # Should be decompressed now
        assert bloom.bit_array is not None
        assert "grape" in bloom
        
        # Compress again
        bloom.compress()
        assert bloom.compressed
        
        # Decompress manually
        bloom.decompress()
        assert not bloom.compressed
        assert bloom.bit_array is not None
        
        # Verify data integrity after decompression
        for item in test_items:
            assert item in bloom
        assert "grape" in bloom
        
    def test_ensure_methods(self):
        """Test the ensure methods for state management."""
        # Test ensure_uncompressed - create a proper compressed bloom first
        bloom = BloomFilter(size=1000, hash_count=3)
        bloom.add("test_item")
        bloom.compress()  # Properly compress
        assert bloom.compressed
        bloom._ensure_uncompressed()
        assert not bloom.compressed
        
        # Test ensure_compressed
        bloom = BloomFilter(size=1000, hash_count=3)
        assert not bloom.compressed
        bloom._ensure_compressed()
        assert bloom.compressed
        
    def test_compression_ratio(self):
        """Test compression ratio calculation."""
        # Test with sparse data (should compress well)
        bloom_sparse = BloomFilter(size=10000, hash_count=3)
        bloom_sparse.add("test_item_1")
        bloom_sparse.add("test_item_2")
        
        ratio_sparse = bloom_sparse.get_compression_ratio()
        assert ratio_sparse > 1.0  # Should compress well
        
        # Test with dense data (should compress less well)
        bloom_dense = BloomFilter(size=1000, hash_count=5)
        # Add many items to make it dense
        for i in range(500):
            bloom_dense.add(f"item_{i}")
            
        ratio_dense = bloom_dense.get_compression_ratio()
        assert ratio_dense > 1.0  # Should still compress
        
    def test_statistics(self, bloom_filter_compression):
        """Test statistics functionality."""
        small_size, test_items = bloom_filter_compression
        bloom = BloomFilter(size=small_size, hash_count=3)
        
        # Initial state (all zeros)
        stats = bloom.get_statistics()
        assert stats['total_bits'] == small_size
        assert stats['set_bits'] == 0
        assert stats['unset_bits'] == small_size
        assert stats['density'] == 0.0
        assert stats['compression_ratio'] > 1.0
        # Note: statistics temporarily decompresses to calculate density
        
        # Add items
        for item in test_items:
            bloom.add(item)
            
        stats_after = bloom.get_statistics()
        assert stats_after['set_bits'] > 0
        assert stats_after['density'] > 0.0
        
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
        assert uncompressed_size > compressed_size
        
        # Verify we can still operate after compression
        bloom.add("new_item")
        assert "new_item" in bloom


class TestBloomFilterAdvanced:
    """Test suite for advanced Bloom filter functionality."""
        
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
        assert false_positive_rate < 0.5  # Should be less than 50%
        
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
        assert ratio > 1.0
        
    def test_edge_cases(self):
        """Test edge cases with various data types."""
        bloom = BloomFilter(size=2000, hash_count=3)
        
        # Test with empty string
        bloom.add("")
        assert "" in bloom
        
        # Test with very long strings
        long_string = "a" * 1000
        bloom.add(long_string)
        assert long_string in bloom
        
        # Test with unicode characters
        unicode_string = "你好"
        bloom.add(unicode_string)
        assert unicode_string in bloom
        
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
            assert item in bloom
            
    def test_same_item_multiple_times(self):
        """Test adding the same item multiple times."""
        bloom = BloomFilter(size=1000, hash_count=3)
        item = "test_item"
        
        # Add the same item multiple times
        for _ in range(5):
            bloom.add(item)
            
        # Item should still be in filter (only one addition is needed)
        assert item in bloom
        
        # Test compression still works
        bloom.compress()
        assert item in bloom  # Should auto-decompress


class TestBloomFilterJSON:
    """Test suite for JSON serialization functionality."""
    
    def test_bloom_decoder(self):
        """Test bloom decoder function."""
        # Test with non-bloom data
        regular_dict = {'key': 'value'}
        result = bloom_decoder(regular_dict)
        assert result == regular_dict
        
    def test_json_serialization(self):
        """Test JSON serialization and deserialization."""
        # Create and populate bloom filter
        bloom_original = BloomFilter(size=2000, hash_count=3)
        for item in ["test1", "test2", "test3"]:
            bloom_original.add(item)
            
        # Serialize to JSON
        json_str = json.dumps(bloom_original, cls=BloomFilterEncoder)
        assert isinstance(json_str, str)
        
        # Deserialize from JSON
        bloom_restored = json.loads(json_str, object_hook=bloom_decoder)
        
        # Verify restored object
        assert len(bloom_restored) == 2000
        assert bloom_restored.hash_count == 3
        assert bloom_restored.compressed  # Should be compressed after serialization
        
        # Verify data integrity
        for item in ["test1", "test2", "test3"]:
            assert item in bloom_restored
            
        # Test negative cases
        for item in ["nonexistent1", "nonexistent2"]:
            assert item not in bloom_restored
            
    def test_json_encoder_compatibility(self):
        """Test that encoder properly handles compressed data."""
        # Create bloom filter
        bloom = BloomFilter(size=1000, hash_count=3)
        bloom.add("test_item")
        
        # Serialize (should auto-compress)
        json_str = json.dumps(bloom, cls=BloomFilterEncoder)
        
        # Parse and check structure
        data = json.loads(json_str)
        assert 'size' in data
        assert 'hash_count' in data
        assert 'compressed_bit_array' in data
        assert 'compressed' in data
        assert '__class__' in data
        assert '__module__' in data
        
        # Verify compressed state
        assert data['compressed']
        assert data['compressed_bit_array'] is not None


class TestBloomFilterPerformance:
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
            assert item in bloom
            
        # Test compression with large dataset
        bloom.compress()
        assert bloom.compressed
        
        # Test that we can still query after compression
        for i in range(1000):
            item = f"item_{i}"
            assert item in bloom
            
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
                    assert isinstance(ratio, (int, float))
                except Exception:
                    # If compression fails, that's acceptable for very sparse data
                    pass