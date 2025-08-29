#!/usr/bin/env python3
"""
Comprehensive unit tests for AccountPickValues class with value selection and transaction management functionality.
"""

import pytest
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from EZ_Value.AccountPickValues import AccountPickValues
    from EZ_Value.Value import Value, ValueState
    from EZ_Transaction.SingleTransaction import Transaction
except ImportError as e:
    print(f"Error importing AccountPickValues: {e}")
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
        Value("0x2000", 200, ValueState.UNSPENT),
        Value("0x3000", 150, ValueState.UNSPENT),
        Value("0x4000", 300, ValueState.UNSPENT),
        Value("0x5000", 250, ValueState.UNSPENT)
    ]


@pytest.fixture
def account_pick_values(account_address):
    """Fixture for AccountPickValues instance."""
    return AccountPickValues(account_address)


@pytest.fixture
def populated_account_pick_values(account_address, test_values):
    """Fixture for AccountPickValues with test values."""
    apv = AccountPickValues(account_address)
    apv.add_values_from_list(test_values)
    return apv


class TestAccountPickValuesInitialization:
    """Test suite for AccountPickValues class initialization."""

    def test_initialization(self, account_pick_values, account_address):
        """Test AccountPickValues initialization."""
        assert account_pick_values.account_collection.account_address == account_address
        assert account_pick_values.get_account_balance() == 0
        assert account_pick_values.get_total_account_balance() == 0
        assert len(account_pick_values.get_account_values()) == 0


class TestAccountPickValuesAddValues:
    """Test suite for adding values to AccountPickValues."""

    def test_add_single_value(self, account_pick_values):
        """Test adding a single value."""
        value = Value("0x1000", 100, ValueState.UNSPENT)
        result = account_pick_values.add_values_from_list([value])
        assert result == 1
        assert account_pick_values.get_account_balance() == 100
        assert len(account_pick_values.get_account_values()) == 1

    def test_add_multiple_values(self, account_pick_values, test_values):
        """Test adding multiple values."""
        result = account_pick_values.add_values_from_list(test_values)
        assert result == len(test_values)
        assert account_pick_values.get_account_balance() == sum(v.value_num for v in test_values)
        assert len(account_pick_values.get_account_values()) == len(test_values)

    def test_add_empty_list(self, account_pick_values):
        """Test adding empty list of values."""
        result = account_pick_values.add_values_from_list([])
        assert result == 0
        assert account_pick_values.get_account_balance() == 0

    def test_add_values_with_different_states(self, account_pick_values):
        """Test adding values with different states."""
        values = [
            Value("0x1000", 100, ValueState.UNSPENT),
            Value("0x2000", 200, ValueState.SELECTED),
            Value("0x3000", 150, ValueState.LOCAL_COMMITTED),
            Value("0x4000", 300, ValueState.CONFIRMED)
        ]
        result = account_pick_values.add_values_from_list(values)
        assert result == len(values)
        assert account_pick_values.get_account_balance(ValueState.UNSPENT) == 100
        assert account_pick_values.get_account_balance(ValueState.SELECTED) == 200
        assert account_pick_values.get_account_balance(ValueState.LOCAL_COMMITTED) == 150
        assert account_pick_values.get_account_balance(ValueState.CONFIRMED) == 300


class TestAccountPickValuesPickValuesForTransaction:
    """Test suite for picking values for transactions."""

    def test_pick_values_exact_amount(self, populated_account_pick_values):
        """Test picking values for exact amount."""
        required_amount = 200
        sender = "0xsender"
        recipient = "0xrecipient"
        nonce = 1
        tx_hash = "0xtxhash"
        time = 1234567890

        selected_values, change_value, change_tx, main_tx = populated_account_pick_values.pick_values_for_transaction(
            required_amount, sender, recipient, nonce, tx_hash, time
        )

        # Check that we have selected values
        assert len(selected_values) >= 1
        # Check that the total selected amount is sufficient
        total_selected = sum(v.value_num for v in selected_values)
        assert total_selected >= required_amount
        
        # Check that transactions were created
        assert main_tx is not None
        assert main_tx.sender == sender
        assert main_tx.recipient == recipient
        
        # Note: change behavior depends on the specific values selected
        # We just verify the logic works correctly

    def test_pick_values_with_change(self, populated_account_pick_values):
        """Test picking values requiring change."""
        required_amount = 167
        sender = "0xsender"
        recipient = "0xrecipient"
        nonce = 1
        tx_hash = "0xtxhash"
        time = 1234567890

        selected_values, change_value, change_tx, main_tx = populated_account_pick_values.pick_values_for_transaction(
            required_amount, sender, recipient, nonce, tx_hash, time
        )

        # Check that we have selected values
        assert len(selected_values) >= 1
        
        # Calculate total amount from selected values and change
        total_selected = sum(v.value_num for v in selected_values)
        
        # The key assertion: total amount should equal required amount
        # because selected_values and change_value are split from original values
        assert total_selected == required_amount
        
        # Check that transactions were created
        assert main_tx is not None
        assert main_tx.sender == sender
        assert main_tx.recipient == recipient
        
        # If change was created, verify it
        if change_value is not None:
            assert change_value.value_num > 0
            assert change_tx is not None
            assert change_tx.sender == sender
            assert change_tx.recipient == sender  # Change goes back to sender

    def test_pick_values_multiple_with_change(self, populated_account_pick_values):
        """Test picking values requiring multiple inputs."""
        required_amount = 271
        sender = "0xsender"
        recipient = "0xrecipient"
        nonce = 1
        tx_hash = "0xtxhash"
        time = 1234567890

        selected_values, change_value, change_tx, main_tx = populated_account_pick_values.pick_values_for_transaction(
            required_amount, sender, recipient, nonce, tx_hash, time
        )

        # Check that we have selected values
        assert len(selected_values) >= 1
        
        # Calculate total amount from selected values and change
        total_selected = sum(v.value_num for v in selected_values)
        
        # The key assertion: total amount should equal required amount
        # because selected_values and change_value are split from original values
        assert total_selected == required_amount
        
        # Check that transactions were created
        assert main_tx is not None
        assert main_tx.sender == sender
        assert main_tx.recipient == recipient
        
        # If change was created, verify it
        if change_value is not None:
            assert change_value.value_num > 0
            assert change_tx is not None
            assert change_tx.sender == sender
            assert change_tx.recipient == sender  # Change goes back to sender

    def test_pick_values_multiple_values(self, populated_account_pick_values):
        """Test picking values requiring multiple inputs."""
        required_amount = 457
        sender = "0xsender"
        recipient = "0xrecipient"
        nonce = 1
        tx_hash = "0xtxhash"
        time = 1234567890

        selected_values, change_value, change_tx, main_tx = populated_account_pick_values.pick_values_for_transaction(
            required_amount, sender, recipient, nonce, tx_hash, time
        )

        assert len(selected_values) >= 2
        total_selected = sum(v.value_num for v in selected_values)
        assert total_selected >= required_amount
        assert main_tx is not None

    def test_pick_values_insufficient_balance(self, populated_account_pick_values):
        """Test picking values with insufficient balance."""
        required_amount = 2008
        sender = "0xsender"
        recipient = "0xrecipient"
        nonce = 1
        tx_hash = "0xtxhash"
        time = 1234567890

        with pytest.raises(ValueError, match="余额不足！"):
            populated_account_pick_values.pick_values_for_transaction(
                required_amount, sender, recipient, nonce, tx_hash, time
            )

    def test_pick_values_invalid_amount(self, populated_account_pick_values):
        """Test picking values with invalid amount."""
        required_amount = 0
        sender = "0xsender"
        recipient = "0xrecipient"
        nonce = 1
        tx_hash = "0xtxhash"
        time = 1234567890

        with pytest.raises(ValueError, match="交易金额必须大于等于1"):
            populated_account_pick_values.pick_values_for_transaction(
                required_amount, sender, recipient, nonce, tx_hash, time
            )

    def test_pick_values_no_available_values(self, account_pick_values):
        """Test picking values with no available values."""
        required_amount = 100
        sender = "0xsender"
        recipient = "0xrecipient"
        nonce = 1
        tx_hash = "0xtxhash"
        time = 1234567890

        with pytest.raises(ValueError, match="余额不足！"):
            account_pick_values.pick_values_for_transaction(
                required_amount, sender, recipient, nonce, tx_hash, time
            )


class TestAccountPickValuesStateManagement:
    """Test suite for state management methods."""

    def test_commit_transaction_values(self, populated_account_pick_values):
        """Test committing transaction values."""
        # First pick some values
        required_amount = 200
        sender = "0xsender"
        recipient = "0xrecipient"
        nonce = 1
        tx_hash = "0xtxhash"
        time = 1234567890

        selected_values, _, _, _ = populated_account_pick_values.pick_values_for_transaction(
            required_amount, sender, recipient, nonce, tx_hash, time
        )

        # Check initial state
        assert selected_values[0].state == ValueState.SELECTED

        # Commit the values
        result = populated_account_pick_values.commit_transaction_values(selected_values)
        assert result is True
        assert selected_values[0].state == ValueState.LOCAL_COMMITTED

    def test_confirm_transaction_values(self, populated_account_pick_values):
        """Test confirming transaction values."""
        # First pick and commit some values
        required_amount = 200
        sender = "0xsender"
        recipient = "0xrecipient"
        nonce = 1
        tx_hash = "0xtxhash"
        time = 1234567890

        selected_values, _, _, _ = populated_account_pick_values.pick_values_for_transaction(
            required_amount, sender, recipient, nonce, tx_hash, time
        )

        populated_account_pick_values.commit_transaction_values(selected_values)

        # Confirm the values
        result = populated_account_pick_values.confirm_transaction_values(selected_values)
        assert result is True
        assert selected_values[0].state == ValueState.CONFIRMED

    def test_rollback_transaction_selection(self, populated_account_pick_values):
        """Test rolling back transaction selection."""
        # First pick some values
        required_amount = 200
        sender = "0xsender"
        recipient = "0xrecipient"
        nonce = 1
        tx_hash = "0xtxhash"
        time = 1234567890

        selected_values, _, _, _ = populated_account_pick_values.pick_values_for_transaction(
            required_amount, sender, recipient, nonce, tx_hash, time
        )

        # Check initial state
        assert selected_values[0].state == ValueState.SELECTED

        # Rollback the selection
        result = populated_account_pick_values.rollback_transaction_selection(selected_values)
        assert result is True
        assert selected_values[0].state == ValueState.UNSPENT


class TestAccountPickValuesBalanceManagement:
    """Test suite for balance management methods."""

    def test_get_account_balance_by_state(self, populated_account_pick_values):
        """Test getting account balance by state."""
        # Get initial balance
        initial_unspent = populated_account_pick_values.get_account_balance(ValueState.UNSPENT)
        
        # Add values with different states
        values = [
            Value("0x6000", 100, ValueState.UNSPENT),
            Value("0x7000", 200, ValueState.SELECTED),
            Value("0x8000", 150, ValueState.LOCAL_COMMITTED),
            Value("0x9000", 300, ValueState.CONFIRMED)
        ]
        populated_account_pick_values.add_values_from_list(values)

        assert populated_account_pick_values.get_account_balance(ValueState.UNSPENT) == initial_unspent + 100
        assert populated_account_pick_values.get_account_balance(ValueState.SELECTED) == 200
        assert populated_account_pick_values.get_account_balance(ValueState.LOCAL_COMMITTED) == 150
        assert populated_account_pick_values.get_account_balance(ValueState.CONFIRMED) == 300

    def test_get_total_account_balance(self, populated_account_pick_values):
        """Test getting total account balance."""
        total_balance = populated_account_pick_values.get_total_account_balance()
        # Expected balance from initial values
        expected_balance = 1000  # 100+200+150+300+250
        assert total_balance == expected_balance

    def test_get_account_values_by_state(self, populated_account_pick_values):
        """Test getting account values by state."""
        # Add values with different states
        values = [
            Value("0x6000", 100, ValueState.SELECTED),
            Value("0x7000", 200, ValueState.CONFIRMED)
        ]
        populated_account_pick_values.add_values_from_list(values)

        unspent_values = populated_account_pick_values.get_account_values(ValueState.UNSPENT)
        selected_values = populated_account_pick_values.get_account_values(ValueState.SELECTED)
        confirmed_values = populated_account_pick_values.get_account_values(ValueState.CONFIRMED)
        all_values = populated_account_pick_values.get_account_values()

        assert len(unspent_values) == 5
        assert len(selected_values) == 1
        assert len(confirmed_values) == 1
        assert len(all_values) == 7


class TestAccountPickValuesCleanupAndValidation:
    """Test suite for cleanup and validation methods."""

    def test_cleanup_confirmed_values(self, populated_account_pick_values):
        """Test cleaning up confirmed values."""
        # Add some confirmed values
        confirmed_values = [
            Value("0x6000", 100, ValueState.CONFIRMED),
            Value("0x7000", 200, ValueState.CONFIRMED)
        ]
        populated_account_pick_values.add_values_from_list(confirmed_values)

        # Check initial count
        initial_count = len(populated_account_pick_values.get_account_values())
        confirmed_count = len(populated_account_pick_values.get_account_values(ValueState.CONFIRMED))

        # Cleanup confirmed values
        cleaned_count = populated_account_pick_values.cleanup_confirmed_values()
        assert cleaned_count == confirmed_count

        # Check final count
        final_count = len(populated_account_pick_values.get_account_values())
        assert final_count == initial_count - confirmed_count
        assert len(populated_account_pick_values.get_account_values(ValueState.CONFIRMED)) == 0

    def test_validate_account_integrity(self, populated_account_pick_values):
        """Test validating account integrity."""
        # Should be valid initially
        assert populated_account_pick_values.validate_account_integrity() is True

        # Add non-overlapping values
        non_overlapping_values = [
            Value("0x6000", 100, ValueState.UNSPENT),  # Does not overlap
        ]
        populated_account_pick_values.add_values_from_list(non_overlapping_values)

        # Should still be valid
        assert populated_account_pick_values.validate_account_integrity() is True


class TestAccountPickValuesEdgeCases:
    """Test suite for edge cases and error conditions."""

    def test_empty_account_operations(self, account_pick_values):
        """Test operations on empty account."""
        assert account_pick_values.get_account_balance() == 0
        assert account_pick_values.get_total_account_balance() == 0
        assert len(account_pick_values.get_account_values()) == 0
        assert account_pick_values.cleanup_confirmed_values() == 0
        assert account_pick_values.validate_account_integrity() is True

    def test_large_amount_selection(self, populated_account_pick_values):
        """Test selecting large amounts."""
        total_balance = populated_account_pick_values.get_account_balance()
        sender = "0xsender"
        recipient = "0xrecipient"
        nonce = 1
        tx_hash = "0xtxhash"
        time = 1234567890

        selected_values, change_value, change_tx, main_tx = populated_account_pick_values.pick_values_for_transaction(
            total_balance, sender, recipient, nonce, tx_hash, time
        )

        assert len(selected_values) >= 1
        total_selected = sum(v.value_num for v in selected_values)
        assert total_selected >= total_balance
        assert change_value is None or change_value.value_num == total_selected - total_balance

    def test_find_node_by_value(self, populated_account_pick_values):
        """Test finding node by value."""
        test_value = populated_account_pick_values.get_account_values()[0]
        node_id = populated_account_pick_values._find_node_by_value(test_value)
        assert node_id is not None

        # Test with non-existent value
        fake_value = Value("0x9999", 100, ValueState.UNSPENT)
        node_id = populated_account_pick_values._find_node_by_value(fake_value)
        assert node_id is None

    def test_update_value_state(self, populated_account_pick_values):
        """Test updating value state."""
        test_value = populated_account_pick_values.get_account_values()[0]
        original_state = test_value.state

        # Update to SELECTED
        result = populated_account_pick_values._update_value_state(test_value, ValueState.SELECTED)
        assert result is True
        assert test_value.state == ValueState.SELECTED

        # Update back to UNSPENT
        result = populated_account_pick_values._update_value_state(test_value, ValueState.UNSPENT)
        assert result is True
        assert test_value.state == ValueState.UNSPENT

        # Test with non-existent value
        fake_value = Value("0x9999", 100, ValueState.UNSPENT)
        result = populated_account_pick_values._update_value_state(fake_value, ValueState.SELECTED)
        assert result is False


# Global test values for the test
global_test_values = [
    Value("0x1000", 100, ValueState.UNSPENT),
    Value("0x2000", 200, ValueState.UNSPENT),
    Value("0x3000", 150, ValueState.UNSPENT),
    Value("0x4000", 300, ValueState.UNSPENT),
    Value("0x5000", 250, ValueState.UNSPENT)
]


def main():
    """Simple entry function to run tests."""
    print("Running AccountPickValues tests...")
    print("To run all tests, use: pytest -v")
    print("To run specific test class, use: pytest -v test_account_pick_values.py::TestAccountPickValuesInitialization")
    print("To run with coverage, use: pytest --cov=.")
    
    # Run pytest programmatically
    exit_code = pytest.main([__file__, "-v"])
    return exit_code


if __name__ == "__main__":
    exit(main())