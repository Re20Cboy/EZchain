#!/usr/bin/env python3
"""
Comprehensive unit tests for AccountValueCollection class with linked list structure and state management.
"""

import unittest
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from EZ_Value.AccountValueCollection import AccountValueCollection, ValueNode
    from EZ_Value.Value import Value, ValueState
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)


class TestValueNodeInitialization(unittest.TestCase):
    """Test suite for ValueNode class initialization."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_value = Value("0x1000", 100)
        
    def test_value_node_initialization(self):
        """Test ValueNode initialization."""
        node = ValueNode(self.test_value)
        
        self.assertEqual(node.value, self.test_value)
        self.assertIsNotNone(node.node_id)
        self.assertIsInstance(node.node_id, str)
        self.assertIsNone(node.next)
        self.assertIsNone(node.prev)
        
    def test_value_node_custom_id(self):
        """Test ValueNode with custom node ID."""
        custom_id = "custom_node_123"
        node = ValueNode(self.test_value, custom_id)
        
        self.assertEqual(node.node_id, custom_id)
        
    def test_value_node_initialization_with_value_properties(self):
        """Test ValueNode with different value properties."""
        value = Value("0x2000", 200, ValueState.LOCAL_COMMITTED)
        node = ValueNode(value)
        
        self.assertEqual(node.value.begin_index, "0x2000")
        self.assertEqual(node.value.value_num, 200)
        self.assertEqual(node.value.state, ValueState.LOCAL_COMMITTED)


class TestAccountValueCollectionInitialization(unittest.TestCase):
    """Test suite for AccountValueCollection class initialization."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.account_address = "0xTestAccount123"
        self.collection = AccountValueCollection(self.account_address)
        
    def test_account_value_collection_initialization(self):
        """Test AccountValueCollection initialization."""
        self.assertEqual(self.collection.account_address, self.account_address)
        self.assertIsNone(self.collection.head)
        self.assertIsNone(self.collection.tail)
        self.assertEqual(self.collection.size, 0)
        self.assertEqual(len(self.collection._index_map), 0)
        self.assertEqual(len(self.collection._state_index), 0)
        self.assertEqual(len(self.collection._decimal_begin_map), 0)
        
    def test_account_value_collection_empty_properties(self):
        """Test empty collection properties."""
        self.assertEqual(len(self.collection), 0)
        self.assertEqual(list(self.collection), [])
        self.assertFalse(Value("0x1000", 100) in self.collection)


class TestAccountValueCollectionAddition(unittest.TestCase):
    """Test suite for AccountValueCollection addition functionality."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.collection = AccountValueCollection("0xTestAccount")
        self.test_values = [
            Value("0x1000", 100),
            Value("0x2000", 200),
            Value("0x3000", 300)
        ]
        
    def test_add_value_end_position(self):
        """Test adding value at end position."""
        value = self.test_values[0]
        result = self.collection.add_value(value, "end")
        
        self.assertTrue(result)
        self.assertEqual(self.collection.size, 1)
        self.assertIsNotNone(self.collection.head)
        self.assertIsNotNone(self.collection.tail)
        self.assertEqual(self.collection.head.value, value)
        self.assertEqual(self.collection.tail.value, value)
        self.assertEqual(len(self.collection._index_map), 1)
        self.assertEqual(len(self.collection._state_index[ValueState.UNSPENT]), 1)
        self.assertEqual(self.collection._decimal_begin_map[4096], self.collection.head.node_id)  # 0x1000 = 4096
        
    def test_add_value_beginning_position(self):
        """Test adding value at beginning position."""
        value = self.test_values[0]
        result = self.collection.add_value(value, "beginning")
        
        self.assertTrue(result)
        self.assertEqual(self.collection.size, 1)
        self.assertIsNotNone(self.collection.head)
        self.assertIsNotNone(self.collection.tail)
        self.assertEqual(self.collection.head.value, value)
        self.assertEqual(self.collection.tail.value, value)
        
    def test_add_multiple_values(self):
        """Test adding multiple values."""
        for value in self.test_values:
            self.collection.add_value(value, "end")
            
        self.assertEqual(self.collection.size, 3)
        self.assertIsNotNone(self.collection.head)
        self.assertIsNotNone(self.collection.tail)
        
        # Verify linked list structure
        current = self.collection.head
        for expected_value in self.test_values:
            self.assertEqual(current.value, expected_value)
            current = current.next
            
        # Verify tail
        self.assertEqual(self.collection.tail.value, self.test_values[-1])
        
    def test_add_values_different_states(self):
        """Test adding values with different states."""
        values_with_states = [
            Value("0x1000", 100, ValueState.UNSPENT),
            Value("0x2000", 200, ValueState.LOCAL_COMMITTED),
            Value("0x3000", 300, ValueState.CONFIRMED)
        ]
        
        for value in values_with_states:
            self.collection.add_value(value, "end")
            
        self.assertEqual(self.collection.size, 3)
        
        # Verify state indexing
        self.assertEqual(len(self.collection._state_index[ValueState.UNSPENT]), 1)
        self.assertEqual(len(self.collection._state_index[ValueState.LOCAL_COMMITTED]), 1)
        self.assertEqual(len(self.collection._state_index[ValueState.CONFIRMED]), 1)
        
    def test_add_value_invalid_position(self):
        """Test adding value with invalid position."""
        value = Value("0x1000", 100)
        
        with self.assertRaises(ValueError) as context:
            self.collection.add_value(value, "invalid_position")
            
        self.assertIn("position must be", str(context.exception))
        
    def test_decimal_begin_index_mapping(self):
        """Test decimal begin index mapping."""
        value = Value("0x1000", 100)  # 4096 in decimal
        self.collection.add_value(value, "end")
        
        # Verify decimal begin index mapping
        self.assertIn(4096, self.collection._decimal_begin_map)
        self.assertEqual(self.collection._decimal_begin_map[4096], self.collection.head.node_id)


class TestAccountValueCollectionRemoval(unittest.TestCase):
    """Test suite for AccountValueCollection removal functionality."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.collection = AccountValueCollection("0xTestAccount")
        self.test_values = [Value("0x1000", 100), Value("0x2000", 200), Value("0x3000", 300)]
        
        # Add all values
        for value in self.test_values:
            self.collection.add_value(value, "end")
            
    def test_remove_value_head(self):
        """Test removing head node."""
        node_id = self.collection.head.node_id
        result = self.collection.remove_value(node_id)
        
        self.assertTrue(result)
        self.assertEqual(self.collection.size, 2)
        self.assertEqual(self.collection.head.value, self.test_values[1])
        self.assertEqual(self.collection.head.prev, None)
        self.assertEqual(self.collection.head.next.value, self.test_values[2])
        self.assertEqual(self.collection.tail.value, self.test_values[2])
        
        # Verify indexes are updated
        self.assertNotIn(node_id, self.collection._index_map)
        self.assertNotIn(4096, self.collection._decimal_begin_map)
        
    def test_remove_value_tail(self):
        """Test removing tail node."""
        node_id = self.collection.tail.node_id
        result = self.collection.remove_value(node_id)
        
        self.assertTrue(result)
        self.assertEqual(self.collection.size, 2)
        self.assertEqual(self.collection.tail.value, self.test_values[1])
        self.assertEqual(self.collection.tail.next, None)
        self.assertEqual(self.collection.head.value, self.test_values[0])
        
    def test_remove_value_middle(self):
        """Test removing middle node."""
        node_id = self.collection.head.next.node_id
        result = self.collection.remove_value(node_id)
        
        self.assertTrue(result)
        self.assertEqual(self.collection.size, 2)
        
        # Verify linked list connections
        self.assertEqual(self.collection.head.next.value, self.test_values[2])
        self.assertEqual(self.collection.tail.prev.value, self.test_values[0])
        
    def test_remove_nonexistent_value(self):
        """Test removing nonexistent value."""
        result = self.collection.remove_value("nonexistent_id")
        self.assertFalse(result)
        self.assertEqual(self.collection.size, 3)  # Size should not change
        
    def test_remove_value_state_indexing(self):
        """Test that state indexing is updated when removing value."""
        # Add a value with specific state
        value = Value("0x4000", 100, ValueState.LOCAL_COMMITTED)
        self.collection.add_value(value, "end")
        
        # Get its node ID
        node_id = None
        for nid, node in self.collection._index_map.items():
            if node.value == value:
                node_id = nid
                break
                
        self.assertIsNotNone(node_id)
        
        # Remove it
        result = self.collection.remove_value(node_id)
        self.assertTrue(result)
        
        # Verify state index is updated
        self.assertNotIn(node_id, self.collection._state_index[ValueState.LOCAL_COMMITTED])
        
    def test_remove_all_values(self):
        """Test removing all values."""
        # Remove all values one by one
        current = self.collection.head
        while current:
            node_id = current.node_id
            current = current.next
            self.collection.remove_value(node_id)
            
        self.assertEqual(self.collection.size, 0)
        self.assertIsNone(self.collection.head)
        self.assertIsNone(self.collection.tail)
        self.assertEqual(len(self.collection._index_map), 0)
        self.assertEqual(len(self.collection._state_index), 0)
        self.assertEqual(len(self.collection._decimal_begin_map), 0)


class TestAccountValueCollectionFinding(unittest.TestCase):
    """Test suite for AccountValueCollection finding functionality."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.collection = AccountValueCollection("0xTestAccount")
        self.test_values = [
            Value("0x1000", 100, ValueState.UNSPENT),
            Value("0x2000", 200, ValueState.LOCAL_COMMITTED),
            Value("0x3000", 300, ValueState.CONFIRMED),
            Value("0x4000", 150, ValueState.UNSPENT)
        ]
        
        # Add all values
        for value in self.test_values:
            self.collection.add_value(value, "end")
            
    def test_find_by_state_unspent(self):
        """Test finding values by UNSPENT state."""
        unspent_values = self.collection.find_by_state(ValueState.UNSPENT)
        
        self.assertEqual(len(unspent_values), 2)
        self.assertTrue(all(v.state == ValueState.UNSPENT for v in unspent_values))
        
    def test_find_by_state_local_committed(self):
        """Test finding values by LOCAL_COMMITTED state."""
        committed_values = self.collection.find_by_state(ValueState.LOCAL_COMMITTED)
        
        self.assertEqual(len(committed_values), 1)
        self.assertEqual(committed_values[0].state, ValueState.LOCAL_COMMITTED)
        
    def test_find_by_state_confirmed(self):
        """Test finding values by CONFIRMED state."""
        confirmed_values = self.collection.find_by_state(ValueState.CONFIRMED)
        
        self.assertEqual(len(confirmed_values), 1)
        self.assertEqual(confirmed_values[0].state, ValueState.CONFIRMED)
        
    def test_find_by_state_no_results(self):
        """Test finding values by state with no results."""
        non_existent_state = ValueState.UNSPENT  # All states already tested
        if len(self.collection._state_index.get(non_existent_state, set())) == 0:
            values = self.collection.find_by_state(non_existent_state)
            self.assertEqual(len(values), 0)
            
    def test_find_by_range(self):
        """Test finding values by decimal range."""
        # Test range that should include values from 0x2000 to 0x3000
        start_decimal = 8192  # 0x2000
        end_decimal = 12287   # 0x2fff
        
        range_values = self.collection.find_by_range(start_decimal, end_decimal)
        
        self.assertEqual(len(range_values), 2)  # Should include Value("0x2000", 200) and Value("0x3000", 300)
        
    def test_find_by_range_no_overlap(self):
        """Test finding values by range with no overlap."""
        start_decimal = 20000
        end_decimal = 21000
        
        range_values = self.collection.find_by_range(start_decimal, end_decimal)
        self.assertEqual(len(range_values), 0)
        
    def test_find_by_range_partial_overlap(self):
        """Test finding values by range with partial overlap."""
        # Value("0x1000", 100) = 4096-4195, Value("0x2000", 200) = 8192-8391
        # Range 4000-8500 should partially overlap both
        start_decimal = 4000
        end_decimal = 8500
        
        range_values = self.collection.find_by_range(start_decimal, end_decimal)
        
        # Should find both values due to partial overlap
        self.assertGreaterEqual(len(range_values), 1)
        
    def test_find_intersecting_values(self):
        """Test finding intersecting values."""
        # Create a value that intersects with existing values
        intersecting_value = Value("0x1500", 1000)  # Should intersect with Value("0x1000", 100) and Value("0x2000", 200)
        
        intersecting_values = self.collection.find_intersecting_values(intersecting_value)
        
        # Should find at least one intersecting value
        self.assertGreater(len(intersecting_values), 0)
        self.assertTrue(any(v.is_intersect_value(intersecting_value) for v in intersecting_values))


class TestAccountValueCollectionSplitting(unittest.TestCase):
    """Test suite for AccountValueCollection splitting functionality."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.collection = AccountValueCollection("0xTestAccount")
        self.original_value = Value("0x1000", 200)
        self.collection.add_value(self.original_value, "end")
        
    def test_split_value_valid(self):
        """Test valid value splitting."""
        change_amount = 50
        v1, v2 = self.collection.split_value(self.collection.head.node_id, change_amount)
        
        self.assertIsNotNone(v1)
        self.assertIsNotNone(v2)
        self.assertEqual(v1.value_num, 150)  # 200 - 50
        self.assertEqual(v2.value_num, 50)
        self.assertEqual(v1.begin_index, "0x1000")
        self.assertEqual(v2.begin_index, "0x1096")  # v1.end_index + 1
        
        # Verify collection state
        self.assertEqual(self.collection.size, 2)
        self.assertIsNotNone(self.collection.head.next)
        self.assertEqual(self.collection.tail.value, v2)
        
        # Verify indexes
        self.assertEqual(len(self.collection._index_map), 2)
        self.assertEqual(len(self.collection._state_index[ValueState.UNSPENT]), 2)
        
    def test_split_value_invalid_amount(self):
        """Test splitting value with invalid amount."""
        # Test with zero change
        with self.assertRaises(ValueError):
            v1, v2 = self.collection.split_value(self.collection.head.node_id, 0)
            
        # Test with full amount
        with self.assertRaises(ValueError):
            v1, v2 = self.collection.split_value(self.collection.head.node_id, 200)
            
        # Test with negative amount
        with self.assertRaises(ValueError):
            v1, v2 = self.collection.split_value(self.collection.head.node_id, -10)
            
    def test_split_nonexistent_value(self):
        """Test splitting nonexistent value."""
        v1, v2 = self.collection.split_value("nonexistent_id", 50)
        self.assertIsNone(v1)
        self.assertIsNone(v2)
        
    def test_split_value_update_indexes(self):
        """Test that indexes are properly updated after splitting."""
        change_amount = 50
        v1, v2 = self.collection.split_value(self.collection.head.node_id, change_amount)
        
        # Verify decimal begin index map is updated
        self.assertIn(4096, self.collection._decimal_begin_map)  # v1's begin index
        self.assertIn(4240, self.collection._decimal_begin_map)  # v2's begin index (0x1096 = 4240)
        
    def test_split_multiple_times(self):
        """Test splitting value multiple times."""
        # First split
        v1, v2 = self.collection.split_value(self.collection.head.node_id, 50)
        
        # Split the second part
        v2a, v2b = self.collection.split_value(self.collection.tail.node_id, 25)
        
        self.assertEqual(v2a.value_num, 25)
        self.assertEqual(v2b.value_num, 25)
        self.assertEqual(self.collection.size, 3)


class TestAccountValueCollectionMerging(unittest.TestCase):
    """Test suite for AccountValueCollection merging functionality."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.collection = AccountValueCollection("0xTestAccount")
        
    def test_merge_adjacent_values_valid(self):
        """Test merging adjacent values."""
        # Add two adjacent values with same state
        value1 = Value("0x1000", 100)  # 0x1000 to 0x1063
        value2 = Value("0x1064", 100)  # 0x1064 to 0x10c7 (adjacent to value1)
        
        self.collection.add_value(value1, "end")
        node_id1 = self.collection.head.node_id
        self.collection.add_value(value2, "end")
        node_id2 = self.collection.tail.node_id
        
        # Verify they are adjacent in the linked list
        self.assertEqual(self.collection.head.next.node_id, node_id2)
        
        # Merge them
        merged_value = self.collection.merge_adjacent_values(node_id1, node_id2)
        
        self.assertIsNotNone(merged_value)
        self.assertEqual(merged_value.begin_index, "0x1000")
        self.assertEqual(merged_value.value_num, 200)  # 100 + 100
        self.assertEqual(merged_value.end_index, "0x10c7")
        
        # Verify collection state
        self.assertEqual(self.collection.size, 1)
        self.assertEqual(self.collection.head.value, merged_value)
        self.assertEqual(len(self.collection._index_map), 1)
        
    def test_merge_non_adjacent_values(self):
        """Test merging non-adjacent values."""
        # Add non-adjacent values
        value1 = Value("0x1000", 100)
        value2 = Value("0x2000", 100)
        
        self.collection.add_value(value1, "end")
        node_id1 = self.collection.head.node_id
        self.collection.add_value(value2, "end")
        node_id2 = self.collection.tail.node_id
        
        # Merge should fail
        merged_value = self.collection.merge_adjacent_values(node_id1, node_id2)
        self.assertIsNone(merged_value)
        
        # Collection should remain unchanged
        self.assertEqual(self.collection.size, 2)
        
    def test_merge_different_states(self):
        """Test merging values with different states."""
        # Add values with different states
        value1 = Value("0x1000", 100, ValueState.UNSPENT)
        value2 = Value("0x1064", 100, ValueState.LOCAL_COMMITTED)
        
        self.collection.add_value(value1, "end")
        node_id1 = self.collection.head.node_id
        self.collection.add_value(value2, "end")
        node_id2 = self.collection.tail.node_id
        
        # Merge should fail due to different states
        merged_value = self.collection.merge_adjacent_values(node_id1, node_id2)
        self.assertIsNone(merged_value)
        
    def test_merge_nonexistent_nodes(self):
        """Test merging nonexistent nodes."""
        result = self.collection.merge_adjacent_values("nonexistent1", "nonexistent2")
        self.assertIsNone(result)


class TestAccountValueCollectionStateManagement(unittest.TestCase):
    """Test suite for AccountValueCollection state management functionality."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.collection = AccountValueCollection("0xTestAccount")
        self.test_values = [Value("0x1000", 100), Value("0x2000", 200)]
        
        # Add all values
        for value in self.test_values:
            self.collection.add_value(value, "end")
            
    def test_update_value_state(self):
        """Test updating value state."""
        node_id = self.collection.head.node_id
        
        # Update to LOCAL_COMMITTED
        result = self.collection.update_value_state(node_id, ValueState.LOCAL_COMMITTED)
        self.assertTrue(result)
        
        # Verify state change
        updated_value = self.collection._index_map[node_id].value
        self.assertEqual(updated_value.state, ValueState.LOCAL_COMMITTED)
        
        # Verify state index update
        self.assertNotIn(node_id, self.collection._state_index[ValueState.UNSPENT])
        self.assertIn(node_id, self.collection._state_index[ValueState.LOCAL_COMMITTED])
        
    def test_update_same_state(self):
        """Test updating value to same state."""
        node_id = self.collection.head.node_id
        
        # Update to same state
        result = self.collection.update_value_state(node_id, ValueState.UNSPENT)
        self.assertTrue(result)
        
        # State should remain unchanged
        self.assertEqual(self.collection._index_map[node_id].value.state, ValueState.UNSPENT)
        
    def test_update_nonexistent_value(self):
        """Test updating nonexistent value state."""
        result = self.collection.update_value_state("nonexistent_id", ValueState.LOCAL_COMMITTED)
        self.assertFalse(result)
        
    def test_state_index_consistency(self):
        """Test that state index remains consistent."""
        # Update all values to LOCAL_COMMITTED
        for node_id in list(self.collection._index_map.keys()):
            self.collection.update_value_state(node_id, ValueState.LOCAL_COMMITTED)
            
        # Verify state index
        self.assertEqual(len(self.collection._state_index[ValueState.UNSPENT]), 0)
        self.assertEqual(len(self.collection._state_index[ValueState.LOCAL_COMMITTED]), 2)
        self.assertEqual(len(self.collection._state_index[ValueState.CONFIRMED]), 0)


class TestAccountValueCollectionBalanceCalculation(unittest.TestCase):
    """Test suite for AccountValueCollection balance calculation functionality."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.collection = AccountValueCollection("0xTestAccount")
        
    def test_get_balance_by_state_unspent(self):
        """Test getting balance by UNSPENT state."""
        values = [Value("0x1000", 100, ValueState.UNSPENT), Value("0x2000", 200, ValueState.UNSPENT)]
        
        for value in values:
            self.collection.add_value(value, "end")
            
        balance = self.collection.get_balance_by_state(ValueState.UNSPENT)
        self.assertEqual(balance, 300)  # 100 + 200
        
    def test_get_balance_by_state_other_states(self):
        """Test getting balance by other states."""
        values = [
            Value("0x1000", 100, ValueState.LOCAL_COMMITTED),
            Value("0x2000", 200, ValueState.CONFIRMED)
        ]
        
        for value in values:
            self.collection.add_value(value, "end")
            
        local_committed_balance = self.collection.get_balance_by_state(ValueState.LOCAL_COMMITTED)
        confirmed_balance = self.collection.get_balance_by_state(ValueState.CONFIRMED)
        
        self.assertEqual(local_committed_balance, 100)
        self.assertEqual(confirmed_balance, 200)
        
    def test_get_balance_by_state_no_values(self):
        """Test getting balance by state with no values."""
        balance = self.collection.get_balance_by_state(ValueState.UNSPENT)
        self.assertEqual(balance, 0)
        
    def test_get_total_balance(self):
        """Test getting total balance."""
        values = [Value("0x1000", 100), Value("0x2000", 200), Value("0x3000", 300)]
        
        for value in values:
            self.collection.add_value(value, "end")
            
        total_balance = self.collection.get_total_balance()
        self.assertEqual(total_balance, 600)  # 100 + 200 + 300
        
    def test_get_total_balance_empty(self):
        """Test getting total balance with empty collection."""
        total_balance = self.collection.get_total_balance()
        self.assertEqual(total_balance, 0)


class TestAccountValueCollectionIterationAndContains(unittest.TestCase):
    """Test suite for AccountValueCollection iteration and contains functionality."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.collection = AccountValueCollection("0xTestAccount")
        self.test_values = [Value("0x1000", 100), Value("0x2000", 200), Value("0x3000", 300)]
        
        # Add all values
        for value in self.test_values:
            self.collection.add_value(value, "end")
            
    def test_iteration(self):
        """Test collection iteration."""
        iterated_values = list(self.collection)
        
        self.assertEqual(len(iterated_values), 3)
        self.assertEqual(iterated_values[0], self.test_values[0])
        self.assertEqual(iterated_values[1], self.test_values[1])
        self.assertEqual(iterated_values[2], self.test_values[2])
        
    def test_contains_existing_value(self):
        """Test contains method with existing value."""
        self.assertTrue(self.test_values[0] in self.collection)
        
    def test_contains_nonexistent_value(self):
        """Test contains method with nonexistent value."""
        nonexistent_value = Value("0x9999", 999)
        self.assertFalse(nonexistent_value in self.collection)
        
    def test_contains_different_values_same_properties(self):
        """Test contains method with different values that have same properties."""
        same_value = Value("0x1000", 100)  # Same as test_values[0]
        self.assertTrue(same_value in self.collection)
        
    def test_contains_with_state_mismatch(self):
        """Test contains method with value that has same properties but different state."""
        different_state_value = Value("0x1000", 100, ValueState.LOCAL_COMMITTED)
        # Should still be found if there's a value with same begin_index and value_num
        # but different state
        self.assertTrue(different_state_value in self.collection)


class TestAccountValueCollectionValidation(unittest.TestCase):
    """Test suite for AccountValueCollection validation functionality."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.collection = AccountValueCollection("0xTestAccount")
        
    def test_validate_no_overlap_empty(self):
        """Test validation with empty collection."""
        result = self.collection.validate_no_overlap()
        self.assertTrue(result)
        
    def test_validate_no_overlap_valid(self):
        """Test validation with non-overlapping values."""
        values = [Value("0x1000", 100), Value("0x2000", 200)]
        
        for value in values:
            self.collection.add_value(value, "end")
            
        result = self.collection.validate_no_overlap()
        self.assertTrue(result)
        
    def test_validate_no_overlap_with_overlap(self):
        """Test validation with overlapping values."""
        values = [Value("0x1000", 200), Value("0x1500", 100)]  # Overlapping
        
        for value in values:
            self.collection.add_value(value, "end")
            
        result = self.collection.validate_no_overlap()
        self.assertFalse(result)
        
    def test_validate_no_adjacent_overlap(self):
        """Test validation with adjacent but not overlapping values."""
        values = [Value("0x1000", 100), Value("0x1064", 100)]  # Adjacent but not overlapping
        
        for value in values:
            self.collection.add_value(value, "end")
            
        result = self.collection.validate_no_overlap()
        self.assertTrue(result)  # Adjacent values should not be considered overlapping


class TestAccountValueCollectionClearSpent(unittest.TestCase):
    """Test suite for AccountValueCollection clear spent functionality."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.collection = AccountValueCollection("0xTestAccount")
        
    def test_clear_spent_values_empty(self):
        """Test clearing spent values from empty collection."""
        # Should not raise any exceptions
        self.collection.clear_spent_values()
        self.assertEqual(self.collection.size, 0)
        
    def test_clear_spent_values_no_confirmed(self):
        """Test clearing spent values with no confirmed values."""
        values = [Value("0x1000", 100, ValueState.UNSPENT)]
        
        for value in values:
            self.collection.add_value(value, "end")
            
        self.collection.clear_spent_values()
        
        # Values should remain unchanged
        self.assertEqual(self.collection.size, 1)
        
    def test_clear_spent_values_with_confirmed(self):
        """Test clearing spent values with confirmed values."""
        values = [
            Value("0x1000", 100, ValueState.UNSPENT),
            Value("0x2000", 200, ValueState.CONFIRMED),
            Value("0x3000", 300, ValueState.LOCAL_COMMITTED)
        ]
        
        for value in values:
            self.collection.add_value(value, "end")
            
        # Should only remove CONFIRMED values
        initial_size = self.collection.size
        self.collection.clear_spent_values()
        
        # Should have removed one CONFIRMED value
        self.assertEqual(self.collection.size, initial_size - 1)
        
    def test_clear_all_confirmed_values(self):
        """Test clearing all confirmed values."""
        # Add multiple confirmed values
        for i in range(3):
            value = Value(f"0x{i*1000}", 100, ValueState.CONFIRMED)
            self.collection.add_value(value, "end")
            
        self.assertEqual(self.collection.size, 3)
        
        # Clear all confirmed values
        self.collection.clear_spent_values()
        
        self.assertEqual(self.collection.size, 0)
        self.assertEqual(len(self.collection._state_index[ValueState.CONFIRMED]), 0)


class TestAccountValueCollectionEdgeCases(unittest.TestCase):
    """Test suite for AccountValueCollection edge cases."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.collection = AccountValueCollection("0xTestAccount")
        
    def test_large_number_of_values(self):
        """Test with large number of values."""
        values = [Value(f"0x{i}", 1) for i in range(1000)]
        
        for value in values:
            self.collection.add_value(value, "end")
            
        self.assertEqual(self.collection.size, 1000)
        self.assertEqual(self.collection.get_total_balance(), 1000)
        
        # Test finding values
        found_values = self.collection.find_by_state(ValueState.UNSPENT)
        self.assertEqual(len(found_values), 1000)
        
    def test_single_value_operations(self):
        """Test operations with single value."""
        value = Value("0x1000", 100)
        self.collection.add_value(value, "end")
        
        # Test all operations
        self.assertEqual(self.collection.size, 1)
        self.assertEqual(self.collection.get_total_balance(), 100)
        self.assertEqual(len(self.collection.find_by_state(ValueState.UNSPENT)), 1)
        self.assertTrue(value in self.collection)
        
        # Test splitting
        v1, v2 = self.collection.split_value(self.collection.head.node_id, 50)
        self.assertIsNotNone(v1)
        self.assertIsNotNone(v2)
        self.assertEqual(self.collection.size, 2)
        
    def test_values_with_large_numbers(self):
        """Test with large value numbers."""
        large_value = Value("0x1000000", 1000000)  # Large hex, large number
        self.collection.add_value(large_value, "end")
        
        self.assertEqual(self.collection.size, 1)
        self.assertEqual(self.collection.get_total_balance(), 1000000)
        
        # Test range finding
        decimal_begin = large_value.get_decimal_begin_index()
        decimal_end = large_value.get_decimal_end_index()
        found_values = self.collection.find_by_range(decimal_begin, decimal_end)
        self.assertEqual(len(found_values), 1)
        
    def test_mixed_operations_sequence(self):
        """Test complex sequence of operations."""
        # Add multiple values
        values = [Value("0x1000", 100), Value("0x2000", 200), Value("0x3000", 300)]
        for value in values:
            self.collection.add_value(value, "end")
            
        # Split one value
        v1, v2 = self.collection.split_value(self.collection.head.node_id, 50)
        
        # Update states
        self.collection.update_value_state(self.collection.head.node_id, ValueState.LOCAL_COMMITTED)
        self.collection.update_value_state(self.collection.tail.node_id, ValueState.CONFIRMED)
        
        # Check balance
        unspent_balance = self.collection.get_balance_by_state(ValueState.UNSPENT)
        committed_balance = self.collection.get_balance_by_state(ValueState.LOCAL_COMMITTED)
        confirmed_balance = self.collection.get_balance_by_state(ValueState.CONFIRMED)
        
        self.assertEqual(unspent_balance, 450)  # 200 + 250 (from split) 
        self.assertEqual(committed_balance, 50)
        self.assertEqual(confirmed_balance, 300)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)