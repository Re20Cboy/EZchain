#!/usr/bin/env python3
"""
Comprehensive unit tests for AccountValueCollection class with linked list management functionality.
"""

import pytest
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from EZ_Value.AccountValueCollection import AccountValueCollection, ValueNode
    from EZ_Value.Value import Value, ValueState
except ImportError as e:
    print(f"Error importing AccountValueCollection: {e}")
    sys.exit(1)


@pytest.fixture
def account_address():
    """Fixture for account address."""
    return "0x1234567890abcdef"


@pytest.fixture
def test_values():
    """Fixture for test values."""
    return [
        Value("0x1000", 100, ValueState.UNSPENT),
        Value("0x2000", 200, ValueState.SELECTED),
        Value("0x3000", 150, ValueState.LOCAL_COMMITTED),
        Value("0x4000", 300, ValueState.CONFIRMED),
        Value("0x5000", 250, ValueState.UNSPENT)
    ]


@pytest.fixture
def empty_collection(account_address):
    """Fixture for empty AccountValueCollection."""
    return AccountValueCollection(account_address)


@pytest.fixture
def populated_collection(account_address, test_values):
    """Fixture for AccountValueCollection with test values."""
    collection = AccountValueCollection(account_address)
    for value in test_values:
        collection.add_value(value)
    return collection


class TestAccountValueCollectionInitialization:
    """Test suite for AccountValueCollection initialization."""
    
    def test_empty_initialization(self, account_address):
        """Test initialization of empty collection."""
        collection = AccountValueCollection(account_address)
        
        assert collection.account_address == account_address
        assert collection.head is None
        assert collection.tail is None
        assert collection.size == 0
        assert len(collection._index_map) == 0
        assert len(collection._state_index) == 0
        assert len(collection._decimal_begin_map) == 0
        
    def test_length_operations(self, empty_collection):
        """Test length operations on empty collection."""
        assert len(empty_collection) == 0
        assert empty_collection.size == 0
        
    def test_iteration_empty(self, empty_collection):
        """Test iteration over empty collection."""
        values = list(empty_collection)
        assert len(values) == 0
        
    def test_contains_empty(self, empty_collection, test_values):
        """Test contains operation on empty collection."""
        assert test_values[0] not in empty_collection


class TestAccountValueCollectionAddition:
    """Test suite for adding values to collection."""
    
    def test_add_single_value_end(self, empty_collection, test_values):
        """Test adding single value at end."""
        value = test_values[0]
        result = empty_collection.add_value(value)
        
        assert result is True
        assert len(empty_collection) == 1
        assert empty_collection.head is not None
        assert empty_collection.tail is not None
        assert empty_collection.head == empty_collection.tail
        assert empty_collection.head.value == value
        
    def test_add_single_value_beginning(self, empty_collection, test_values):
        """Test adding single value at beginning."""
        value = test_values[0]
        result = empty_collection.add_value(value, position="beginning")
        
        assert result is True
        assert len(empty_collection) == 1
        assert empty_collection.head is not None
        assert empty_collection.tail is not None
        assert empty_collection.head == empty_collection.tail
        assert empty_collection.head.value == value
        
    def test_add_multiple_values_end(self, empty_collection, test_values):
        """Test adding multiple values at end."""
        for i, value in enumerate(test_values):
            result = empty_collection.add_value(value, position="end")
            assert result is True
            assert len(empty_collection) == i + 1
            
        # Check linked list order
        current = empty_collection.head
        for i, value in enumerate(test_values):
            assert current.value == value
            if i < len(test_values) - 1:
                current = current.next
        assert current == empty_collection.tail
        
    def test_add_multiple_values_beginning(self, empty_collection, test_values):
        """Test adding multiple values at beginning."""
        for i, value in enumerate(test_values):
            result = empty_collection.add_value(value, position="beginning")
            assert result is True
            assert len(empty_collection) == i + 1
            
        # Check linked list order (should be reversed)
        current = empty_collection.head
        for i, value in enumerate(reversed(test_values)):
            assert current.value == value
            if i < len(test_values) - 1:
                current = current.next
        assert current == empty_collection.tail
        
    def test_add_invalid_position(self, empty_collection, test_values):
        """Test adding value with invalid position."""
        with pytest.raises(ValueError, match="position must be 'end' or 'beginning'"):
            empty_collection.add_value(test_values[0], position="invalid")
            
    def test_add_duplicate_values(self, empty_collection, test_values):
        """Test adding duplicate values."""
        value = test_values[0]
        empty_collection.add_value(value)
        empty_collection.add_value(value)  # Same value again
        
        assert len(empty_collection) == 2
        assert empty_collection.head.value == value
        assert empty_collection.tail.value == value
        assert empty_collection.head != empty_collection.tail


class TestAccountValueCollectionRemoval:
    """Test suite for removing values from collection."""
    
    def test_remove_single_value(self, populated_collection, test_values):
        """Test removing single value."""
        # Get the node_id of the first value
        node_id = list(populated_collection._index_map.keys())[0]
        
        result = populated_collection.remove_value(node_id)
        
        assert result is True
        assert len(populated_collection) == len(test_values) - 1
        assert node_id not in populated_collection._index_map
        
    def test_remove_nonexistent_value(self, populated_collection):
        """Test removing nonexistent value."""
        result = populated_collection.remove_value("nonexistent_id")
        assert result is False
        assert len(populated_collection) == 5  # Should remain unchanged
        
    def test_remove_head_value(self, populated_collection, test_values):
        """Test removing head value."""
        head_node_id = populated_collection.head.node_id
        
        result = populated_collection.remove_value(head_node_id)
        
        assert result is True
        assert len(populated_collection) == 4
        assert populated_collection.head.value == test_values[1]  # Second value should be new head
        
    def test_remove_tail_value(self, populated_collection, test_values):
        """Test removing tail value."""
        tail_node_id = populated_collection.tail.node_id
        
        result = populated_collection.remove_value(tail_node_id)
        
        assert result is True
        assert len(populated_collection) == 4
        assert populated_collection.tail.value == test_values[-2]  # Second to last value should be new tail
        
    def test_remove_middle_value(self, populated_collection, test_values):
        """Test removing middle value."""
        # Remove the third value
        current = populated_collection.head
        for _ in range(2):  # Move to third node
            current = current.next
        middle_node_id = current.node_id
        
        result = populated_collection.remove_value(middle_node_id)
        
        assert result is True
        assert len(populated_collection) == 4
        
        # Check linked list integrity
        values = list(populated_collection)
        expected_values = [test_values[0], test_values[1], test_values[3], test_values[4]]
        assert values == expected_values
        
    def test_remove_all_values(self, populated_collection):
        """Test removing all values."""
        # Get initial node IDs
        initial_node_ids = list(populated_collection._index_map.keys())
        
        for node_id in initial_node_ids:
            result = populated_collection.remove_value(node_id)
            assert result is True
            
        assert len(populated_collection) == 0
        assert populated_collection.head is None
        assert populated_collection.tail is None
        assert len(populated_collection._index_map) == 0
        assert len(populated_collection._decimal_begin_map) == 0
        # Check that all state index sets are empty
        for state_set in populated_collection._state_index.values():
            assert len(state_set) == 0


class TestAccountValueCollectionStateManagement:
    """Test suite for state management functionality."""
    
    def test_update_value_state(self, populated_collection):
        """Test updating value state."""
        node_id = list(populated_collection._index_map.keys())[0]
        old_state = populated_collection._index_map[node_id].value.state
        
        result = populated_collection.update_value_state(node_id, ValueState.CONFIRMED)
        
        assert result is True
        new_state = populated_collection._index_map[node_id].value.state
        assert new_state == ValueState.CONFIRMED
        assert new_state != old_state
        
        # Check state index is updated
        assert node_id not in populated_collection._state_index[old_state]
        assert node_id in populated_collection._state_index[ValueState.CONFIRMED]
        
    def test_update_value_state_same_state(self, populated_collection):
        """Test updating value to same state."""
        node_id = list(populated_collection._index_map.keys())[0]
        node = populated_collection._index_map[node_id]
        current_state = node.value.state
        
        result = populated_collection.update_value_state(node_id, current_state)
        
        assert result is True
        assert node.value.state == current_state
        
    def test_update_value_state_nonexistent(self, populated_collection):
        """Test updating state of nonexistent value."""
        result = populated_collection.update_value_state("nonexistent_id", ValueState.CONFIRMED)
        assert result is False
        
    def test_find_by_state(self, populated_collection, test_values):
        """Test finding values by state."""
        # Find UNSPENT values
        unspent_values = populated_collection.find_by_state(ValueState.UNSPENT)
        expected_unspent = [v for v in test_values if v.state == ValueState.UNSPENT]
        assert len(unspent_values) == len(expected_unspent)
        
        # Check all found values are indeed UNSPENT
        for value in unspent_values:
            assert value.state == ValueState.UNSPENT
            
        # Find values by other states
        for state in ValueState:
            found_values = populated_collection.find_by_state(state)
            expected_values = [v for v in test_values if v.state == state]
            assert len(found_values) == len(expected_values)
            
    def test_find_by_state_empty(self, populated_collection):
        """Test finding values by state when no values match."""
        # Assuming no values with this state
        rare_state = ValueState.CONFIRMED  # This might have values, adjust if needed
        found_values = populated_collection.find_by_state(rare_state)
        assert isinstance(found_values, list)


class TestAccountValueCollectionValueSplitting:
    """Test suite for value splitting functionality."""
    
    def test_split_value_valid(self, empty_collection, test_values):
        """Test valid value splitting."""
        # Add a value that can be split
        value = Value("0x1000", 200, ValueState.UNSPENT)
        empty_collection.add_value(value)
        
        node_id = list(empty_collection._index_map.keys())[0]
        
        v1, v2 = empty_collection.split_value(node_id, 50)
        
        assert v1 is not None
        assert v2 is not None
        assert v1.value_num == 150
        assert v2.value_num == 50
        assert v1.begin_index == "0x1000"
        assert v2.begin_index == "0x1096"  # 0x1000 + 150 - 1 + 1 = 0x1096
        assert v1.state == ValueState.UNSPENT
        assert v2.state == ValueState.UNSPENT
        
        # Check collection size increased
        assert len(empty_collection) == 2
        
    def test_split_value_invalid_node_id(self, populated_collection):
        """Test splitting value with invalid node_id."""
        result = populated_collection.split_value("nonexistent_id", 50)
        assert result == (None, None)
        
    def test_split_value_invalid_change(self, populated_collection):
        """Test splitting value with invalid change amount."""
        node_id = list(populated_collection._index_map.keys())[0]
        
        # Test change <= 0
        result = populated_collection.split_value(node_id, 0)
        assert result == (None, None)
        
        result = populated_collection.split_value(node_id, -10)
        assert result == (None, None)
        
        # Test change >= value_num
        node = populated_collection._index_map[node_id]
        result = populated_collection.split_value(node_id, node.value.value_num)
        assert result == (None, None)
        
        result = populated_collection.split_value(node_id, node.value.value_num + 1)
        assert result == (None, None)
        
    def test_split_value_linked_list_integrity(self, empty_collection, test_values):
        """Test that splitting maintains linked list integrity."""
        value = Value("0x1000", 200, ValueState.UNSPENT)
        empty_collection.add_value(value)
        
        node_id = list(empty_collection._index_map.keys())[0]
        
        v1, v2 = empty_collection.split_value(node_id, 50)
        
        # Check linked list structure
        assert len(empty_collection) == 2
        assert empty_collection.head.value == v1
        assert empty_collection.tail.value == v2
        assert empty_collection.head.next == empty_collection.tail
        assert empty_collection.tail.prev == empty_collection.head


class TestAccountValueCollectionValueMerging:
    """Test suite for value merging functionality."""
    
    def test_merge_adjacent_values_valid(self, empty_collection):
        """Test valid merging of adjacent values."""
        # Create two adjacent values with same state
        value1 = Value("0x1000", 100, ValueState.UNSPENT)
        value2 = Value("0x1064", 100, ValueState.UNSPENT)  # Adjacent to value1
        
        empty_collection.add_value(value1)
        empty_collection.add_value(value2)
        
        node_id1 = list(empty_collection._index_map.keys())[0]
        node_id2 = list(empty_collection._index_map.keys())[1]
        
        merged_value = empty_collection.merge_adjacent_values(node_id1, node_id2)
        
        assert merged_value is not None
        assert merged_value.value_num == 200
        assert merged_value.begin_index == "0x1000"
        assert merged_value.state == ValueState.UNSPENT
        
        # Check collection size decreased
        assert len(empty_collection) == 1
        
    def test_merge_non_adjacent_values(self, empty_collection):
        """Test merging non-adjacent values."""
        value1 = Value("0x1000", 100, ValueState.UNSPENT)
        value2 = Value("0x2000", 100, ValueState.UNSPENT)  # Not adjacent
        
        empty_collection.add_value(value1)
        empty_collection.add_value(value2)
        
        # Get node IDs - need to check which nodes are actually adjacent in the list
        node_ids = list(empty_collection._index_map.keys())
        node_id1 = node_ids[0]
        node_id2 = node_ids[1]
        
        # Check if they are actually adjacent in the linked list
        node1 = empty_collection._index_map[node_id1]
        node2 = empty_collection._index_map[node_id2]
        
        # If they are not adjacent in the linked list, merge should return None
        if node1.next != node2:
            merged_value = empty_collection.merge_adjacent_values(node_id1, node_id2)
            assert merged_value is None
            assert len(empty_collection) == 2  # Size should remain unchanged
        
    def test_merge_different_states(self, empty_collection):
        """Test merging values with different states."""
        value1 = Value("0x1000", 100, ValueState.UNSPENT)
        value2 = Value("0x1064", 100, ValueState.SELECTED)  # Different state
        
        empty_collection.add_value(value1)
        empty_collection.add_value(value2)
        
        node_id1 = list(empty_collection._index_map.keys())[0]
        node_id2 = list(empty_collection._index_map.keys())[1]
        
        merged_value = empty_collection.merge_adjacent_values(node_id1, node_id2)
        
        assert merged_value is None
        assert len(empty_collection) == 2  # Size should remain unchanged
        
    def test_merge_invalid_node_ids(self, empty_collection):
        """Test merging with invalid node IDs."""
        merged_value = empty_collection.merge_adjacent_values("invalid1", "invalid2")
        assert merged_value is None


class TestAccountValueCollectionSearchAndFiltering:
    """Test suite for search and filtering functionality."""
    
    def test_find_by_range(self, empty_collection):
        """Test finding values by decimal range."""
        # Add test values
        values = [
            Value("0x1000", 100, ValueState.UNSPENT),   # 4096-4195
            Value("0x2000", 200, ValueState.UNSPENT),   # 8192-8391
            Value("0x3000", 150, ValueState.UNSPENT),   # 12288-12437
        ]
        
        for value in values:
            empty_collection.add_value(value)
            
        # Test range that includes first value
        result = empty_collection.find_by_range(4000, 4200)
        assert len(result) == 1
        assert result[0].begin_index == "0x1000"
        
        # Test range that includes multiple values
        result = empty_collection.find_by_range(4000, 9000)
        assert len(result) == 2
        
        # Test range that includes no values
        result = empty_collection.find_by_range(5000, 6000)
        assert len(result) == 0
        
    def test_find_intersecting_values(self, empty_collection):
        """Test finding intersecting values."""
        # Add test values with actual overlapping ranges
        values = [
            Value("0x1000", 200, ValueState.UNSPENT),   # 4096-4295
            Value("0x1080", 100, ValueState.UNSPENT),   # 4224-4323 (overlaps with first)
            Value("0x3000", 150, ValueState.UNSPENT),   # 12288-12437 (no overlap)
        ]
        
        for value in values:
            empty_collection.add_value(value)
            
        # Test target that intersects with first two values
        target = Value("0x1050", 300, ValueState.UNSPENT)  # 4176-4475
        result = empty_collection.find_intersecting_values(target)
        
        assert len(result) == 2
        result_begin_indices = [v.begin_index for v in result]
        assert "0x1000" in result_begin_indices
        assert "0x1080" in result_begin_indices
        
        # Test target that intersects with no values
        target = Value("0x4000", 100, ValueState.UNSPENT)
        result = empty_collection.find_intersecting_values(target)
        assert len(result) == 0
        
    def test_get_all_values(self, populated_collection, test_values):
        """Test getting all values."""
        all_values = populated_collection.get_all_values()
        
        assert len(all_values) == len(test_values)
        # Check that all original values are present
        for test_value in test_values:
            assert test_value in all_values
            
    def test_get_values_sorted_by_begin_index(self, populated_collection):
        """Test getting values sorted by begin index."""
        sorted_values = populated_collection.get_values_sorted_by_begin_index()
        
        # Check that values are sorted
        for i in range(len(sorted_values) - 1):
            current_begin = sorted_values[i].get_decimal_begin_index()
            next_begin = sorted_values[i + 1].get_decimal_begin_index()
            assert current_begin <= next_begin
            
    def test_iteration(self, populated_collection, test_values):
        """Test iteration over collection."""
        iterated_values = list(populated_collection)
        
        assert len(iterated_values) == len(test_values)
        # Check that all values are present
        for test_value in test_values:
            assert test_value in iterated_values
            
    def test_contains(self, populated_collection, test_values):
        """Test contains operation."""
        # Test with existing values
        for value in test_values:
            assert value in populated_collection
            
        # Test with non-existing value
        new_value = Value("0x9999", 100, ValueState.UNSPENT)
        assert new_value not in populated_collection


class TestAccountValueCollectionBalanceCalculation:
    """Test suite for balance calculation functionality."""
    
    def test_get_balance_by_state(self, populated_collection, test_values):
        """Test getting balance by state."""
        for state in ValueState:
            expected_balance = sum(v.value_num for v in test_values if v.state == state)
            actual_balance = populated_collection.get_balance_by_state(state)
            assert actual_balance == expected_balance
            
    def test_get_balance_by_state_default(self, populated_collection, test_values):
        """Test getting balance by state with default UNSPENT."""
        expected_balance = sum(v.value_num for v in test_values if v.state == ValueState.UNSPENT)
        actual_balance = populated_collection.get_balance_by_state()  # Default UNSPENT
        assert actual_balance == expected_balance
        
    def test_get_total_balance(self, populated_collection, test_values):
        """Test getting total balance."""
        expected_total = sum(v.value_num for v in test_values)
        actual_total = populated_collection.get_total_balance()
        assert actual_total == expected_total
        
    def test_get_balance_empty_collection(self, empty_collection):
        """Test getting balance from empty collection."""
        balance = empty_collection.get_balance_by_state()
        assert balance == 0
        
        total_balance = empty_collection.get_total_balance()
        assert total_balance == 0


class TestAccountValueCollectionValidation:
    """Test suite for validation functionality."""
    
    def test_validate_no_overlap_valid(self, empty_collection):
        """Test validation with no overlapping values."""
        # Add non-overlapping values
        values = [
            Value("0x1000", 100, ValueState.UNSPENT),   # 4096-4195
            Value("0x2000", 200, ValueState.UNSPENT),   # 8192-8391
            Value("0x3000", 150, ValueState.UNSPENT),   # 12288-12437
        ]
        
        for value in values:
            empty_collection.add_value(value)
            
        assert empty_collection.validate_no_overlap()
        
    def test_validate_no_overlap_invalid(self, empty_collection):
        """Test validation with overlapping values."""
        # Add overlapping values
        values = [
            Value("0x1000", 200, ValueState.UNSPENT),   # 4096-4295
            Value("0x1080", 100, ValueState.UNSPENT),   # 4224-4323 (overlaps with first)
        ]
        
        for value in values:
            empty_collection.add_value(value)
            
        assert not empty_collection.validate_no_overlap()
        
    def test_validate_no_overlap_empty(self, empty_collection):
        """Test validation on empty collection."""
        assert empty_collection.validate_no_overlap()
        
    def test_clear_spent_values(self, populated_collection, test_values):
        """Test clearing spent (CONFIRMED) values."""
        initial_size = len(populated_collection)
        
        populated_collection.clear_spent_values()
        
        # Check that CONFIRMED values are removed
        remaining_values = populated_collection.get_all_values()
        for value in remaining_values:
            assert value.state != ValueState.CONFIRMED
            
        # Check that other states remain
        expected_remaining = [v for v in test_values if v.state != ValueState.CONFIRMED]
        assert len(remaining_values) == len(expected_remaining)


class TestAccountValueCollectionEdgeCases:
    """Test suite for edge cases and error handling."""
    
    def test_single_value_operations(self, empty_collection):
        """Test operations with single value."""
        value = Value("0x1000", 100, ValueState.UNSPENT)
        empty_collection.add_value(value)
        
        # Test length
        assert len(empty_collection) == 1
        
        # Test contains
        assert value in empty_collection
        
        # Test removal
        node_id = list(empty_collection._index_map.keys())[0]
        result = empty_collection.remove_value(node_id)
        assert result is True
        assert len(empty_collection) == 0
        
    def test_large_number_of_values(self, empty_collection):
        """Test with large number of values."""
        num_values = 1000
        values = []
        for i in range(num_values):
            value = Value(hex(0x1000 + i * 100), 100, ValueState.UNSPENT)
            values.append(value)
            empty_collection.add_value(value)
            
        assert len(empty_collection) == num_values
        
        # Test iteration
        iterated_values = list(empty_collection)
        assert len(iterated_values) == num_values
        
        # Test state finding
        unspent_values = empty_collection.find_by_state(ValueState.UNSPENT)
        assert len(unspent_values) == num_values
        
    def test_value_with_same_begin_index(self, empty_collection):
        """Test handling values with same begin index."""
        value1 = Value("0x1000", 100, ValueState.UNSPENT)
        value2 = Value("0x1000", 200, ValueState.UNSPENT)  # Same begin index
        
        empty_collection.add_value(value1)
        empty_collection.add_value(value2)
        
        assert len(empty_collection) == 2
        
        # Test that both values are present
        all_values = empty_collection.get_all_values()
        assert value1 in all_values
        assert value2 in all_values
        
    def test_consecutive_values(self, empty_collection):
        """Test handling consecutive values."""
        value1 = Value("0x1000", 100, ValueState.UNSPENT)   # 4096-4195
        value2 = Value("0x10C4", 100, ValueState.UNSPENT)   # 4196-4295 (consecutive)
        
        empty_collection.add_value(value1)
        empty_collection.add_value(value2)
        
        assert len(empty_collection) == 2
        
        # Test validation - consecutive values should not overlap
        assert empty_collection.validate_no_overlap()
        
    def test_extreme_value_ranges(self, empty_collection):
        """Test with extreme value ranges."""
        # Very small values
        small_value = Value("0x1", 1, ValueState.UNSPENT)
        empty_collection.add_value(small_value)
        
        # Very large values
        large_value = Value("0xffff0000", 1000, ValueState.UNSPENT)
        empty_collection.add_value(large_value)
        
        assert len(empty_collection) == 2
        assert empty_collection.validate_no_overlap()
        
    def test_state_index_consistency(self, populated_collection):
        """Test that state index remains consistent."""
        # Get initial state counts
        initial_state_counts = {}
        for state in ValueState:
            initial_state_counts[state] = len(populated_collection._state_index[state])
            
        # Update some values' states
        node_ids = list(populated_collection._index_map.keys())
        for i, node_id in enumerate(node_ids[:2]):  # Update first 2 values
            new_state = list(ValueState)[(i + 1) % len(ValueState)]
            populated_collection.update_value_state(node_id, new_state)
            
        # Check state index consistency
        for state in ValueState:
            indexed_values = populated_collection.find_by_state(state)
            assert len(indexed_values) == len(populated_collection._state_index[state])
            
            # All indexed values should have the correct state
            for value in indexed_values:
                assert value.state == state


class TestValueNode:
    """Test suite for ValueNode class."""
    
    def test_value_node_initialization(self, test_values):
        """Test ValueNode initialization."""
        value = test_values[0]
        node = ValueNode(value)
        
        assert node.value == value
        assert node.next is None
        assert node.prev is None
        assert isinstance(node.node_id, str)
        assert len(node.node_id) > 0
        
    def test_value_node_with_custom_id(self, test_values):
        """Test ValueNode initialization with custom node_id."""
        value = test_values[0]
        custom_id = "custom_node_id"
        node = ValueNode(value, custom_id)
        
        assert node.node_id == custom_id
        
    def test_value_node_linking(self, test_values):
        """Test ValueNode linking functionality."""
        node1 = ValueNode(test_values[0])
        node2 = ValueNode(test_values[1])
        
        # Link nodes
        node1.next = node2
        node2.prev = node1
        
        assert node1.next == node2
        assert node2.prev == node1