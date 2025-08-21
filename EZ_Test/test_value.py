#!/usr/bin/env python3
"""
Comprehensive unit tests for Value class with intersection and validation functionality.
"""

import unittest
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from EZ_Value.Value import Value
except ImportError as e:
    print(f"Error importing Value: {e}")
    sys.exit(1)


class TestValueInitialization(unittest.TestCase):
    """Test suite for Value class initialization and basic properties."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.valid_begin = "0x1000"
        self.valid_num = 100
        self.value = Value(self.valid_begin, self.valid_num)
        
    def test_valid_initialization(self):
        """Test valid Value initialization."""
        self.assertEqual(self.value.begin_index, self.valid_begin)
        self.assertEqual(self.value.value_num, self.valid_num)
        self.assertEqual(self.value.end_index, "0x1063")  # 0x1000 + 100 - 1 = 0x1063
        
    def test_hex_conversion(self):
        """Test hexadecimal conversion methods."""
        decimal_begin = self.value.get_decimal_begin_index()
        decimal_end = self.value.get_decimal_end_index()
        
        self.assertEqual(decimal_begin, 4096)  # 0x1000 = 4096
        self.assertEqual(decimal_end, 4195)    # 0x1063 = 4195
        
    def test_print_functionality(self):
        """Test print methods (capture stdout to verify)."""
        import io
        from contextlib import redirect_stdout
        
        # Test print_value method
        f = io.StringIO()
        with redirect_stdout(f):
            self.value.print_value()
        output = f.getvalue()
        
        self.assertIn('value #begin:' + str(self.valid_begin), output)
        self.assertIn('value #end:' + str(self.value.end_index), output)
        self.assertIn('value num:' + str(self.valid_num), output)


class TestValueValidation(unittest.TestCase):
    """Test suite for Value validation functionality."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.valid_value = Value("0x1000", 100)
        # Note: invalid_value_num, invalid_value_begin are created in respective tests due to exceptions
        self.valid_value_modified = Value("0x1000", 100)  # Will be modified
        
    def test_valid_value(self):
        """Test validation of valid Value objects."""
        self.assertTrue(self.valid_value.check_value())
        
    def test_invalid_value_num(self):
        """Test that invalid valueNum (<= 0) raises ValueError in initialization."""
        with self.assertRaises(ValueError):
            Value("0x1000", 0)
        
    def test_invalid_hex_begin(self):
        """Test that invalid hexadecimal beginIndex raises ValueError in initialization."""
        with self.assertRaises(ValueError):
            Value("invalid_hex", 100)
        
    def test_invalid_hex_end(self):
        """Test validation with invalid hexadecimal endIndex."""
        # Manually set invalid endIndex to test
        self.valid_value_modified.end_index = "invalid"
        self.assertFalse(self.valid_value_modified.check_value())
        
    def test_end_index_consistency(self):
        """Test that endIndex calculation is consistent."""
        value = Value("0x1000", 100)
        calculated_end = value.get_end_index("0x1000", 100)
        self.assertEqual(value.end_index, calculated_end)


class TestValueSplitting(unittest.TestCase):
    """Test suite for Value splitting functionality."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.original_value = Value("0x1000", 200)
        
    def test_split_value_valid(self):
        """Test valid value splitting."""
        v1, v2 = self.original_value.split_value(50)
        
        # Check first part
        self.assertEqual(v1.begin_index, "0x1000")
        self.assertEqual(v1.value_num, 150)  # 200 - 50
        self.assertEqual(v1.end_index, "0x1095")  # 0x1000 + 150 - 1
        
        # Check second part (change)
        self.assertEqual(v2.begin_index, "0x1096")  # v1.end_index + 1
        self.assertEqual(v2.value_num, 50)
        self.assertEqual(v2.end_index, "0x10c7")  # 0x1096 + 50 - 1
        
    def test_split_value_at_boundary(self):
        """Test that splitting with full amount raises ValueError."""
        with self.assertRaises(ValueError):
            self.original_value.split_value(200)
            
    def test_split_value_no_remainder(self):
        """Test that splitting with zero change raises ValueError."""
        with self.assertRaises(ValueError):
            self.original_value.split_value(0)


class TestValueIntersection(unittest.TestCase):
    """Test suite for Value intersection functionality."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create overlapping values for testing
        self.value1 = Value("0x1000", 200)  # 0x1000 to 0x10c7
        self.value2 = Value("0x1080", 150)  # 0x1080 to 0x1157 (overlaps with value1)
        self.value3 = Value("0x1200", 100)  # 0x1200 to 0x1263 (no overlap)
        self.value4 = Value("0x1000", 200)  # Same as value1
        
    def test_intersect_value_exists(self):
        """Test intersection when overlap exists."""
        result = self.value1.get_intersect_value(self.value2)
        
        self.assertIsNotNone(result)
        intersect_value, rest_values = result
        
        # Check intersection: should be 0x1080 to 0x10c7 (72 units)
        self.assertEqual(intersect_value.begin_index, "0x1080")
        self.assertEqual(intersect_value.value_num, 72)  # 0x10c7 - 0x1080 + 1
        
        # Check rest values: two parts before and after intersection
        self.assertEqual(len(rest_values), 1)
        self.assertEqual(rest_values[0].begin_index, "0x1000")
        self.assertEqual(rest_values[0].value_num, 128)  # 0x1080 - 0x1000
        
    def test_intersect_value_no_overlap(self):
        """Test intersection when no overlap exists."""
        result = self.value1.get_intersect_value(self.value3)
        self.assertIsNone(result)
        
    def test_intersect_value_complete_overlap(self):
        """Test intersection when one value completely contains another."""
        result = self.value1.get_intersect_value(self.value4)
        
        self.assertIsNotNone(result)
        intersect_value, rest_values = result
        
        # Intersection should be the same as value4
        self.assertEqual(intersect_value.begin_index, "0x1000")
        self.assertEqual(intersect_value.value_num, 200)
        
        # No rest values since complete overlap
        self.assertEqual(len(rest_values), 0)
        
    def test_intersect_value_adjacent(self):
        """Test intersection with adjacent values (no overlap)."""
        adjacent_value = Value("0x10c8", 100)  # Starts right after value1 ends
        result = self.value1.get_intersect_value(adjacent_value)
        self.assertIsNone(result)


class TestValueIntersectionChecks(unittest.TestCase):
    """Test suite for Value intersection checking methods."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.value1 = Value("0x1000", 200)  # 0x1000 to 0x10c7
        self.value2 = Value("0x1080", 100)  # Overlaps with value1
        self.value3 = Value("0x1200", 100)  # No overlap
        self.value4 = Value("0x1000", 200)  # Same as value1
        
    def test_is_intersect_value_true(self):
        """Test intersection check when overlap exists."""
        self.assertTrue(self.value1.is_intersect_value(self.value2))
        self.assertTrue(self.value2.is_intersect_value(self.value1))
        
    def test_is_intersect_value_false(self):
        """Test intersection check when no overlap exists."""
        self.assertFalse(self.value1.is_intersect_value(self.value3))
        self.assertFalse(self.value3.is_intersect_value(self.value1))
        
    def test_is_intersect_value_adjacent(self):
        """Test intersection check with adjacent values."""
        adjacent_value = Value("0x10c8", 100)
        self.assertFalse(self.value1.is_intersect_value(adjacent_value))
        
    def test_is_in_value_true(self):
        """Test containment check when target is within value."""
        smaller_value = Value("0x1080", 50)  # Within value1
        self.assertTrue(self.value1.is_in_value(smaller_value))
        
    def test_is_in_value_false(self):
        """Test containment check when target is not within value."""
        # Partial overlap
        overlapping_value = Value("0x1080", 200)  # Extends beyond value1
        self.assertFalse(self.value1.is_in_value(overlapping_value))
        
        # No overlap
        separate_value = Value("0x1200", 100)
        self.assertFalse(self.value1.is_in_value(separate_value))
        
    def test_is_same_value_true(self):
        """Test equality check for identical values."""
        self.assertTrue(self.value1.is_same_value(self.value4))
        
    def test_is_same_value_false(self):
        """Test equality check for different values."""
        different_value = Value("0x1000", 201)
        self.assertFalse(self.value1.is_same_value(different_value))
        
        different_begin_value = Value("0x1001", 200)
        self.assertFalse(self.value1.is_same_value(different_begin_value))
        
    def test_is_same_value_invalid_input(self):
        """Test equality check with invalid input type."""
        self.assertFalse(self.value1.is_same_value("invalid"))
        self.assertFalse(self.value1.is_same_value(123))
        self.assertFalse(self.value1.is_same_value(None))


class TestValueEdgeCases(unittest.TestCase):
    """Test suite for Value edge cases and boundary conditions."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.small_value = Value("0x1", 1)
        self.large_value = Value("0x1000000", 1000000)
        
    def test_single_unit_value(self):
        """Test value with only one unit."""
        self.assertEqual(self.small_value.begin_index, "0x1")
        self.assertEqual(self.small_value.end_index, "0x1")
        self.assertEqual(self.small_value.value_num, 1)
        
    def test_split_single_unit_value(self):
        """Test that splitting single unit raises ValueError."""
        with self.assertRaises(ValueError):
            self.small_value.split_value(1)
        
    def test_large_value(self):
        """Test with large values."""
        decimal_begin = self.large_value.get_decimal_begin_index()
        decimal_end = self.large_value.get_decimal_end_index()

        self.assertEqual(decimal_begin, 0x1000000)
        self.assertEqual(decimal_end, 0x1000000 + 1000000 - 1)
        
    def test_maximum_value_boundary(self):
        """Test boundary conditions with maximum values."""
        # Test with large hex values
        large_hex_value = Value("0xffff0000", 1000)
        self.assertTrue(large_hex_value.check_value())
        
        # Test end index calculation
        calculated_end = large_hex_value.get_end_index("0xffff0000", 1000)
        self.assertEqual(large_hex_value.end_index, calculated_end)
        
    def test_zero_splitting(self):
        """Test that splitting with zero change raises ValueError."""
        with self.assertRaises(ValueError):
            Value("0x1000", 100).split_value(0)
            
    def test_full_splitting(self):
        """Test that splitting with full amount raises ValueError."""
        with self.assertRaises(ValueError):
            Value("0x1000", 100).split_value(100)


class TestValueErrorHandling(unittest.TestCase):
    """Test suite for Value error handling."""
    
    def test_invalid_hex_input(self):
        """Test handling of invalid hexadecimal inputs in Value initialization."""
        # Test invalid hex format in Value constructor
        with self.assertRaises(ValueError):
            Value("invalid_hex", 100)
            
    def test_value_boundary_checks(self):
        """Test boundary conditions in value operations."""
        # Test with minimum valid value
        min_value = Value("0x1", 1)
        self.assertTrue(min_value.check_value())
        
        # Test with value that would cause overflow
        large_value = Value("0xffffffffffffffff", 1)
        self.assertTrue(large_value.check_value())
        
    def test_invalid_value_num_in_init(self):
        """Test that invalid valueNum (<= 0) raises ValueError in initialization."""
        with self.assertRaises(ValueError):
            Value("0x1000", 0)
        
    def test_invalid_begin_index_in_init(self):
        """Test that invalid beginIndex raises ValueError in initialization."""
        with self.assertRaises(ValueError):
            Value("invalid_hex", 100)
    
    def test_invalid_type_in_init(self):
        """Test that invalid parameter types raise TypeError in initialization."""
        with self.assertRaises(TypeError):
            Value(123, 100)  # beginIndex should be string
        
        with self.assertRaises(TypeError):
            Value("0x1000", "100")  # valueNum should be int


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)