#!/usr/bin/env python3
"""
Comprehensive unit tests for Value class with intersection and validation functionality.
"""

import pytest
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from EZ_Value.Value import Value, ValueState
except ImportError as e:
    print(f"Error importing Value: {e}")
    sys.exit(1)


@pytest.fixture
def value_test_data():
    """Fixture for value test data."""
    valid_begin = "0x1000"
    valid_num = 100
    return valid_begin, valid_num, Value(valid_begin, valid_num)


class TestValueInitialization:
    """Test suite for Value class initialization and basic properties."""
        
    def test_valid_initialization(self, value_test_data):
        """Test valid Value initialization."""
        valid_begin, valid_num, value = value_test_data
        assert value.begin_index == valid_begin
        assert value.value_num == valid_num
        assert value.end_index == "0x1063"  # 0x1000 + 100 - 1 = 0x1063
        
    def test_hex_conversion(self, value_test_data):
        """Test hexadecimal conversion methods."""
        valid_begin, valid_num, value = value_test_data
        decimal_begin = value.get_decimal_begin_index()
        decimal_end = value.get_decimal_end_index()
        
        assert decimal_begin == 4096  # 0x1000 = 4096
        assert decimal_end == 4195    # 0x1063 = 4195
        
    def test_print_functionality(self, value_test_data):
        """Test print methods (capture stdout to verify)."""
        import io
        from contextlib import redirect_stdout
        
        valid_begin, valid_num, value = value_test_data
        
        # Test print_value method
        f = io.StringIO()
        with redirect_stdout(f):
            value.print_value()
        output = f.getvalue()
        
        assert f'value #begin:{valid_begin}' in output
        assert f'value #end:{value.end_index}' in output
        assert f'value num:{valid_num}' in output
        assert 'value state:unspent' in output
        
    def test_default_state(self):
        """Test that Value objects default to UNSPENT state."""
        value = Value("0x1000", 100)
        assert value.is_unspent()
        assert not value.is_local_committed()
        assert not value.is_confirmed()
        assert value.state == ValueState.UNSPENT
        
    def test_custom_state(self):
        """Test Value initialization with custom state."""
        value = Value("0x1000", 100, ValueState.LOCAL_COMMITTED)
        assert not value.is_unspent()
        assert value.is_local_committed()
        assert not value.is_confirmed()
        assert value.state == ValueState.LOCAL_COMMITTED
        
        value2 = Value("0x1000", 100, ValueState.CONFIRMED)
        assert not value2.is_unspent()
        assert not value2.is_local_committed()
        assert value2.is_confirmed()
        assert value2.state == ValueState.CONFIRMED


class TestValueValidation:
    """Test suite for Value validation functionality."""
    
    def test_valid_value(self):
        """Test validation of valid Value objects."""
        valid_value = Value("0x1000", 100)
        assert valid_value.check_value()
        
    def test_invalid_value_num(self):
        """Test that invalid valueNum (<= 0) raises ValueError in initialization."""
        with pytest.raises(ValueError):
            Value("0x1000", 0)
        
    def test_invalid_hex_begin(self):
        """Test that invalid hexadecimal beginIndex raises ValueError in initialization."""
        with pytest.raises(ValueError):
            Value("invalid_hex", 100)
        
    def test_invalid_hex_end(self):
        """Test validation with invalid hexadecimal endIndex."""
        # Manually set invalid endIndex to test
        valid_value_modified = Value("0x1000", 100)
        valid_value_modified.end_index = "invalid"
        assert not valid_value_modified.check_value()
        
    def test_end_index_consistency(self):
        """Test that endIndex calculation is consistent."""
        value = Value("0x1000", 100)
        calculated_end = value.get_end_index("0x1000", 100)
        assert value.end_index == calculated_end


@pytest.fixture
def value_splitting_data():
    """Fixture for value splitting tests."""
    original_value = Value("0x1000", 200)
    return original_value


class TestValueSplitting:
    """Test suite for Value splitting functionality."""
        
    def test_split_value_valid(self, value_splitting_data):
        """Test valid value splitting."""
        original_value = value_splitting_data
        v1, v2 = original_value.split_value(50)
        
        # Check first part
        assert v1.begin_index == "0x1000"
        assert v1.value_num == 150  # 200 - 50
        assert v1.end_index == "0x1095"  # 0x1000 + 150 - 1
        
        # Check second part (change)
        assert v2.begin_index == "0x1096"  # v1.end_index + 1
        assert v2.value_num == 50
        assert v2.end_index == "0x10c7"  # 0x1096 + 50 - 1
        
    def test_split_value_at_boundary(self, value_splitting_data):
        """Test that splitting with full amount raises ValueError."""
        with pytest.raises(ValueError):
            value_splitting_data.split_value(200)
            
    def test_split_value_no_remainder(self, value_splitting_data):
        """Test that splitting with zero change raises ValueError."""
        with pytest.raises(ValueError):
            value_splitting_data.split_value(0)


@pytest.fixture
def value_intersection_data():
    """Fixture for value intersection tests."""
    # Create overlapping values for testing
    value1 = Value("0x1000", 200)  # 0x1000 to 0x10c7
    value2 = Value("0x1080", 150)  # 0x1080 to 0x1157 (overlaps with value1)
    value3 = Value("0x1200", 100)  # 0x1200 to 0x1263 (no overlap)
    value4 = Value("0x1000", 200)  # Same as value1
    return value1, value2, value3, value4


class TestValueIntersection:
    """Test suite for Value intersection functionality."""
        
    def test_intersect_value_exists(self, value_intersection_data):
        """Test intersection when overlap exists."""
        value1, value2, value3, value4 = value_intersection_data
        result = value1.get_intersect_value(value2)
        
        assert result is not None
        intersect_value, rest_values = result
        
        # Check intersection: should be 0x1080 to 0x10c7 (72 units)
        assert intersect_value.begin_index == "0x1080"
        assert intersect_value.value_num == 72  # 0x10c7 - 0x1080 + 1
        
        # Check rest values: two parts before and after intersection
        assert len(rest_values) == 1
        assert rest_values[0].begin_index == "0x1000"
        assert rest_values[0].value_num == 128  # 0x1080 - 0x1000
        
    def test_intersect_value_no_overlap(self, value_intersection_data):
        """Test intersection when no overlap exists."""
        value1, value2, value3, value4 = value_intersection_data
        result = value1.get_intersect_value(value3)
        assert result is None
        
    def test_intersect_value_complete_overlap(self, value_intersection_data):
        """Test intersection when one value completely contains another."""
        value1, value2, value3, value4 = value_intersection_data
        result = value1.get_intersect_value(value4)
        
        assert result is not None
        intersect_value, rest_values = result
        
        # Intersection should be the same as value4
        assert intersect_value.begin_index == "0x1000"
        assert intersect_value.value_num == 200
        
        # No rest values since complete overlap
        assert len(rest_values) == 0
        
    def test_intersect_value_adjacent(self, value_intersection_data):
        """Test intersection with adjacent values (no overlap)."""
        value1, value2, value3, value4 = value_intersection_data
        adjacent_value = Value("0x10c8", 100)  # Starts right after value1 ends
        result = value1.get_intersect_value(adjacent_value)
        assert result is None


class TestValueIntersectionChecks:
    """Test suite for Value intersection checking methods."""
    
    def test_is_intersect_value_true(self, value_intersection_data):
        """Test intersection check when overlap exists."""
        value1, value2, value3, value4 = value_intersection_data
        # Use value2 which overlaps with value1
        assert value1.is_intersect_value(value2)
        assert value2.is_intersect_value(value1)
        
    def test_is_intersect_value_false(self, value_intersection_data):
        """Test intersection check when no overlap exists."""
        value1, value2, value3, value4 = value_intersection_data
        assert not value1.is_intersect_value(value3)
        assert not value3.is_intersect_value(value1)
        
    def test_is_intersect_value_adjacent(self, value_intersection_data):
        """Test intersection check with adjacent values."""
        value1, value2, value3, value4 = value_intersection_data
        adjacent_value = Value("0x10c8", 100)
        assert not value1.is_intersect_value(adjacent_value)
        
    def test_is_in_value_true(self, value_intersection_data):
        """Test containment check when target is within value."""
        value1, value2, value3, value4 = value_intersection_data
        smaller_value = Value("0x1080", 50)  # Within value1
        assert value1.is_in_value(smaller_value)
        
    def test_is_in_value_false(self, value_intersection_data):
        """Test containment check when target is not within value."""
        value1, value2, value3, value4 = value_intersection_data
        # Partial overlap
        overlapping_value = Value("0x1080", 200)  # Extends beyond value1
        assert not value1.is_in_value(overlapping_value)
        
        # No overlap
        separate_value = Value("0x1200", 100)
        assert not value1.is_in_value(separate_value)
        
    def test_is_same_value_true(self, value_intersection_data):
        """Test equality check for identical values."""
        value1, value2, value3, value4 = value_intersection_data
        assert value1.is_same_value(value4)
        
    def test_is_same_value_false(self, value_intersection_data):
        """Test equality check for different values."""
        value1, value2, value3, value4 = value_intersection_data
        different_value = Value("0x1000", 201)
        assert not value1.is_same_value(different_value)
        
        different_begin_value = Value("0x1001", 200)
        assert not value1.is_same_value(different_begin_value)
        
    def test_is_same_value_invalid_input(self, value_intersection_data):
        """Test equality check with invalid input type."""
        value1, value2, value3, value4 = value_intersection_data
        assert not value1.is_same_value("invalid")
        assert not value1.is_same_value(123)
        assert not value1.is_same_value(None)


@pytest.fixture
def value_edge_cases_data():
    """Fixture for value edge cases tests."""
    small_value = Value("0x1", 1)
    large_value = Value("0x1000000", 1000000)
    return small_value, large_value


class TestValueEdgeCases:
    """Test suite for Value edge cases and boundary conditions."""
        
    def test_single_unit_value(self, value_edge_cases_data):
        """Test value with only one unit."""
        small_value, large_value = value_edge_cases_data
        assert small_value.begin_index == "0x1"
        assert small_value.end_index == "0x1"
        assert small_value.value_num == 1
        
    def test_split_single_unit_value(self, value_edge_cases_data):
        """Test that splitting single unit raises ValueError."""
        small_value, large_value = value_edge_cases_data
        with pytest.raises(ValueError):
            small_value.split_value(1)
        
    def test_large_value(self, value_edge_cases_data):
        """Test with large values."""
        small_value, large_value = value_edge_cases_data
        decimal_begin = large_value.get_decimal_begin_index()
        decimal_end = large_value.get_decimal_end_index()

        assert decimal_begin == 0x1000000
        assert decimal_end == 0x1000000 + 1000000 - 1
        
    def test_maximum_value_boundary(self):
        """Test boundary conditions with maximum values."""
        # Test with large hex values
        large_hex_value = Value("0xffff0000", 1000)
        assert large_hex_value.check_value()
        
        # Test end index calculation
        calculated_end = large_hex_value.get_end_index("0xffff0000", 1000)
        assert large_hex_value.end_index == calculated_end
        
    def test_zero_splitting(self):
        """Test that splitting with zero change raises ValueError."""
        with pytest.raises(ValueError):
            Value("0x1000", 100).split_value(0)
            
    def test_full_splitting(self):
        """Test that splitting with full amount raises ValueError."""
        with pytest.raises(ValueError):
            Value("0x1000", 100).split_value(100)


class TestValueStateManagement:
    """Test suite for Value state management functionality."""
        
    def test_set_state_valid(self):
        """Test setting valid state."""
        value = Value("0x1000", 100)
        value.set_state(ValueState.LOCAL_COMMITTED)
        assert value.is_local_committed()
        assert not value.is_unspent()
        
        value.set_state(ValueState.CONFIRMED)
        assert value.is_confirmed()
        assert not value.is_local_committed()
        
        value.set_state(ValueState.UNSPENT)
        assert value.is_unspent()
        assert not value.is_confirmed()
        
    def test_set_state_invalid(self):
        """Test setting invalid state raises TypeError."""
        value = Value("0x1000", 100)
        with pytest.raises(TypeError):
            value.set_state("invalid_state")
        with pytest.raises(TypeError):
            value.set_state(123)
        with pytest.raises(TypeError):
            value.set_state(None)
            
    def test_state_methods_consistency(self):
        """Test that state methods are consistent."""
        value = Value("0x1000", 100)
        # Test UNSPENT state
        value.set_state(ValueState.UNSPENT)
        assert value.is_unspent()
        assert not value.is_local_committed()
        assert not value.is_confirmed()
        
        # Test LOCAL_COMMITTED state
        value.set_state(ValueState.LOCAL_COMMITTED)
        assert not value.is_unspent()
        assert value.is_local_committed()
        assert not value.is_confirmed()
        
        # Test CONFIRMED state
        value.set_state(ValueState.CONFIRMED)
        assert not value.is_unspent()
        assert not value.is_local_committed()
        assert value.is_confirmed()
        
    def test_state_persistence_in_operations(self):
        """Test that state persists during value operations."""
        # Set initial state
        value = Value("0x1000", 100)
        value.set_state(ValueState.LOCAL_COMMITTED)
        
        # Split value and check state persistence
        v1, v2 = value.split_value(50)
        
        # Both parts should maintain the same state
        assert v1.state == ValueState.LOCAL_COMMITTED
        assert v2.state == ValueState.LOCAL_COMMITTED
        
        # Test intersection operations
        other_value = Value("0x1080", 100, ValueState.UNSPENT)
        result = value.get_intersect_value(other_value)
        
        if result:
            intersect_value, rest_values = result
            assert intersect_value.state == ValueState.LOCAL_COMMITTED
            for rest_value in rest_values:
                assert rest_value.state == ValueState.LOCAL_COMMITTED


class TestValueErrorHandling:
    """Test suite for Value error handling."""
    
    def test_invalid_hex_input(self):
        """Test handling of invalid hexadecimal inputs in Value initialization."""
        # Test invalid hex format in Value constructor
        with pytest.raises(ValueError):
            Value("invalid_hex", 100)
            
    def test_value_boundary_checks(self):
        """Test boundary conditions in value operations."""
        # Test with minimum valid value
        min_value = Value("0x1", 1)
        assert min_value.check_value()
        
        # Test with value that would cause overflow
        large_value = Value("0xffffffffffffffff", 1)
        assert large_value.check_value()
        
    def test_invalid_value_num_in_init(self):
        """Test that invalid valueNum (<= 0) raises ValueError in initialization."""
        with pytest.raises(ValueError):
            Value("0x1000", 0)
        
    def test_invalid_begin_index_in_init(self):
        """Test that invalid beginIndex raises ValueError in initialization."""
        with pytest.raises(ValueError):
            Value("invalid_hex", 100)
    
    def test_invalid_type_in_init(self):
        """Test that invalid parameter types raise TypeError in initialization."""
        with pytest.raises(TypeError):
            Value(123, 100)  # beginIndex should be string
        
        with pytest.raises(TypeError):
            Value("0x1000", "100")  # valueNum should be int
            
        with pytest.raises(TypeError):
            Value("0x1000", 100, "invalid_state")  # state should be ValueState

def main():
    """Simple entry function to run tests."""
    print("Running Test_value tests...")
    print("To run all tests, use: pytest -v")
    print("To run specific test class, use: pytest -v test_value.py::TestValue")
    print("To run with coverage, use: pytest --cov=.")
    
    # Run pytest programmatically
    exit_code = pytest.main([__file__, "-v"])
    return exit_code


if __name__ == "__main__":
    exit(main())