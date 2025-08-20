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
        self.assertEqual(self.value.beginIndex, self.valid_begin)
        self.assertEqual(self.value.valueNum, self.valid_num)
        self.assertEqual(self.value.endIndex, "0x1063")  # 0x1000 + 100 - 1 = 0x1063
        
    def test_hex_conversion(self):
        """Test hexadecimal conversion methods."""
        decimal_begin = self.value.get_decimal_beginIndex()
        decimal_end = self.value.get_decimal_endIndex()
        
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
        self.assertIn('value #end:' + str(self.value.endIndex), output)
        self.assertIn('value num:' + str(self.valid_num), output)


class TestValueValidation(unittest.TestCase):
    """Test suite for Value validation functionality."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.valid_value = Value("0x1000", 100)
        self.invalid_value_num = Value("0x1000", 0)
        self.invalid_value_begin = Value("invalid_hex", 100)
        self.invalid_value_end = Value("0x1000", 100)  # Will be modified
        
    def test_valid_value(self):
        """Test validation of valid Value objects."""
        self.assertTrue(self.valid_value.check_value())
        
    def test_invalid_value_num(self):
        """Test validation with invalid valueNum (<= 0)."""
        self.assertFalse(self.invalid_value_num.check_value())
        
    def test_invalid_hex_begin(self):
        """Test validation with invalid hexadecimal beginIndex."""
        self.assertFalse(self.invalid_value_begin.check_value())
        
    def test_invalid_hex_end(self):
        """Test validation with invalid hexadecimal endIndex."""
        # Manually set invalid endIndex to test
        self.invalid_value_end.endIndex = "invalid"
        self.assertFalse(self.invalid_value_end.check_value())
        
    def test_end_index_consistency(self):
        """Test that endIndex calculation is consistent."""
        value = Value("0x1000", 100)
        calculated_end = value.get_end_index("0x1000", 100)
        self.assertEqual(value.endIndex, calculated_end)


class TestValueSplitting(unittest.TestCase):
    """Test suite for Value splitting functionality."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.original_value = Value("0x1000", 200)
        
    def test_split_value_valid(self):
        """Test valid value splitting."""
        v1, v2 = self.original_value.split_value(50)
        
        # Check first part
        self.assertEqual(v1.beginIndex, "0x1000")
        self.assertEqual(v1.valueNum, 150)  # 200 - 50
        self.assertEqual(v1.endIndex, "0x10c7")  # 0x1000 + 150 - 1
        
        # Check second part (change)
        self.assertEqual(v2.beginIndex, "0x10c8")  # v1.endIndex + 1
        self.assertEqual(v2.valueNum, 50)
        self.assertEqual(v2.endIndex, "0x10e3")  # 0x10c8 + 50 - 1
        
    def test_split_value_at_boundary(self):
        """Test splitting at boundary conditions."""
        # Split all into second part
        v1, v2 = self.original_value.split_value(200)
        
        self.assertEqual(v1.beginIndex, "0x1000")
        self.assertEqual(v1.valueNum, 0)  # 200 - 200
        self.assertEqual(v1.endIndex, "0xfff")  # 0x1000 - 1
        
        self.assertEqual(v2.beginIndex, "0x1000")
        self.assertEqual(v2.valueNum, 200)
        
    def test_split_value_no_remainder(self):
        """Test splitting with no remainder in first part."""
        v1, v2 = self.original_value.split_value(0)
        
        self.assertEqual(v1.beginIndex, "0x1000")
        self.assertEqual(v1.valueNum, 200)
        self.assertEqual(v2.beginIndex, "0x10c8")  # After first part
        self.assertEqual(v2.valueNum, 0)


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
        
        # Check intersection: should be 0x1080 to 0x10c7 (128 units)
        self.assertEqual(intersect_value.beginIndex, "0x1080")
        self.assertEqual(intersect_value.valueNum, 128)  # 0x10c7 - 0x1080 + 1
        
        # Check rest values: two parts before and after intersection
        self.assertEqual(len(rest_values), 2)
        self.assertEqual(rest_values[0].beginIndex, "0x1000")
        self.assertEqual(rest_values[0].valueNum, 128)  # 0x1080 - 0x1000
        
        self.assertEqual(rest_values[1].beginIndex, "0x10c8")
        self.assertEqual(rest_values[1].valueNum, 72)   # 0x10c7 - 0x10c8 + 1
        
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
        self.assertEqual(intersect_value.beginIndex, "0x1000")
        self.assertEqual(intersect_value.valueNum, 200)
        
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
        self.assertEqual(self.small_value.beginIndex, "0x1")
        self.assertEqual(self.small_value.endIndex, "0x1")
        self.assertEqual(self.small_value.valueNum, 1)
        
        # Test splitting single unit
        v1, v2 = self.small_value.split_value(1)
        self.assertEqual(v1.valueNum, 0)
        self.assertEqual(v2.valueNum, 1)
        
    def test_large_value(self):
        """Test with large values."""
        decimal_begin = self.large_value.get_decimal_beginIndex()
        decimal_end = self.large_value.get_decimal_endIndex()
        
        self.assertEqual(decimal_begin, 0x1000000)
        self.assertEqual(decimal_end, 0x1000000 + 1000000 - 1)
        
    def test_maximum_value_boundary(self):
        """Test boundary conditions with maximum values."""
        # Test with large hex values
        large_hex_value = Value("0xffff0000", 1000)
        self.assertTrue(large_hex_value.check_value())
        
        # Test end index calculation
        calculated_end = large_hex_value.get_end_index("0xffff0000", 1000)
        self.assertEqual(large_hex_value.endIndex, calculated_end)
        
    def test_zero_splitting(self):
        """Test splitting with zero change."""
        v1, v2 = Value("0x1000", 100).split_value(0)
        
        self.assertEqual(v1.beginIndex, "0x1000")
        self.assertEqual(v1.valueNum, 100)
        self.assertEqual(v2.beginIndex, "0x10c8")  # After v1
        self.assertEqual(v2.valueNum, 0)
        
    def test_full_splitting(self):
        """Test splitting entire value into second part."""
        v1, v2 = Value("0x1000", 100).split_value(100)
        
        self.assertEqual(v1.valueNum, 0)
        self.assertEqual(v2.beginIndex, "0x1000")
        self.assertEqual(v2.valueNum, 100)


class TestValueErrorHandling(unittest.TestCase):
    """Test suite for Value error handling."""
    
    def test_invalid_hex_input(self):
        """Test handling of invalid hexadecimal inputs."""
        # Invalid hex format
        with self.assertRaises(ValueError):
            int("invalid_hex", 16)
            
    def test_value_boundary_checks(self):
        """Test boundary conditions in value operations."""
        # Test with minimum valid value
        min_value = Value("0x1", 1)
        self.assertTrue(min_value.check_value())
        
        # Test with value that would cause overflow
        large_value = Value("0xffffffffffffffff", 1)
        self.assertTrue(large_value.check_value())


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)