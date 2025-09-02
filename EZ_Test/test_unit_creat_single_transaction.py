#!/usr/bin/env python3
"""
Comprehensive unit tests for CreatSingleTransaction.py with pytest framework.
"""

import pytest
import sys
import os
import tempfile
from datetime import datetime
from unittest.mock import patch, MagicMock
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from EZ_Transaction.CreatSingleTransaction import CreateTransaction
from EZ_Transaction.SingleTransaction import Transaction
from EZ_Value.Value import Value, ValueState
from EZ_Value.AccountPickValues import AccountPickValues


class TestCreateTransaction:
    """Test suite for CreateTransaction class."""

    @pytest.fixture
    def private_key_pem(self):
        """Generate a private key in PEM format."""
        private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
        return private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

    @pytest.fixture
    def public_key_pem(self, private_key_pem):
        """Generate a public key in PEM format from private key."""
        private_key = serialization.load_pem_private_key(
            private_key_pem, 
            password=None, 
            backend=default_backend()
        )
        public_key = private_key.public_key()
        return public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

    @pytest.fixture
    def test_address(self):
        """Test sender address."""
        return "0xTestSender123"

    @pytest.fixture
    def test_recipient(self):
        """Test recipient address."""
        return "0xTestRecipient456"

    @pytest.fixture
    def create_transaction(self, test_address):
        """CreateTransaction instance for testing."""
        return CreateTransaction(test_address)

    def test_create_transaction_initialization(self, create_transaction, test_address):
        """Test CreateTransaction initialization."""
        assert create_transaction.sender_address == test_address
        assert isinstance(create_transaction.value_selector, AccountPickValues)
        assert create_transaction.created_transactions == []

    def test_generate_nonce(self, create_transaction):
        """Test nonce generation."""
        import time
        
        # Ensure different timestamps by adding a small delay
        time.sleep(0.001)
        nonce1 = create_transaction._generate_nonce()
        time.sleep(0.001)
        nonce2 = create_transaction._generate_nonce()
        
        # Nonces should be different
        assert nonce1 != nonce2
        # Nonces should be integers
        assert isinstance(nonce1, int)
        assert isinstance(nonce2, int)
        # Nonces should be positive
        assert nonce1 > 0
        assert nonce2 > 0

    def test_create_transaction_with_sufficient_funds(
        self, 
        create_transaction, 
        test_recipient, 
        private_key_pem,
        public_key_pem
    ):
        """Test transaction creation with sufficient funds."""
        # Add some test values to the account
        test_values = [
            Value("0x1000", 1000),
            Value("0x2000", 500)
        ]
        
        # Mock the value selector to return test values
        with patch.object(create_transaction.value_selector, 'pick_values_for_transaction') as mock_pick:
            mock_pick.return_value = (
                test_values,  # selected_values
                None,        # change_value
                None,        # change_transaction
                None         # main_transaction
            )
            
            with patch.object(Transaction, 'sig_txn') as mock_sig:
                mock_sig.return_value = None
            
            with patch.object(create_transaction.value_selector, 'commit_transaction_values') as mock_commit:
                mock_commit.return_value = None
                
                # Create transaction
                result = create_transaction.create_transaction(
                    recipient=test_recipient,
                    amount=800,
                    private_key_pem=private_key_pem
                )
                
                # Verify result structure
                assert "main_transaction" in result
                assert "change_transaction" in result
                assert "selected_values" in result
                assert "change_value" in result
                assert "total_amount" in result
                assert "transaction_fee" in result
                
                # Verify main transaction
                main_tx = result["main_transaction"]
                assert isinstance(main_tx, Transaction)
                assert main_tx.sender == create_transaction.sender_address
                assert main_tx.recipient == test_recipient
                assert main_tx.signature is not None
                
                # Verify total amount (sum of all selected values, not requested amount)
                assert result["total_amount"] == 1500
                
                # Verify signatures
                assert create_transaction.verify_transaction_signature(main_tx, public_key_pem)

    def test_create_transaction_with_change(
        self,
        create_transaction,
        test_recipient,
        private_key_pem,
        public_key_pem
    ):
        """Test transaction creation with change."""
        test_values = [Value("0x1000", 1000)]
        change_value = Value("0x2000", 200)
        
        # Mock the value selector to return values and change
        with patch.object(create_transaction.value_selector, 'pick_values_for_transaction') as mock_pick:
            mock_pick.return_value = (
                test_values,      # selected_values
                change_value,    # change_value
                None,            # change_transaction
                None             # main_transaction
            )
            
            with patch.object(create_transaction.value_selector, 'commit_transaction_values') as mock_commit:
                mock_commit.return_value = None
                
                # Create transaction with amount that requires change
                result = create_transaction.create_transaction(
                    recipient=test_recipient,
                    amount=800,
                    private_key_pem=private_key_pem
                )
                
                # Verify change transaction exists
                assert result["change_transaction"] is not None
                assert result["change_value"] is not None
                
                # Verify change transaction details
                change_tx = result["change_transaction"]
                assert isinstance(change_tx, Transaction)
                assert change_tx.sender == create_transaction.sender_address
                assert change_tx.recipient == create_transaction.sender_address  # Change back to sender
                assert change_tx.signature is not None
                
                # Verify change value
                assert result["change_value"] == change_value
                
                # Verify total amount + change = selected values amount
                assert result["total_amount"] == 800  # Requested amount
                assert result["change_value"].value_num == 200  # Change amount

    def test_create_transaction_insufficient_funds(
        self,
        create_transaction,
        test_recipient,
        private_key_pem
    ):
        """Test transaction creation with insufficient funds."""
        # Mock the value selector to return insufficient values
        with patch.object(create_transaction.value_selector, 'pick_values_for_transaction') as mock_pick:
            # Simulate insufficient funds by raising an exception
            mock_pick.side_effect = ValueError("Insufficient funds")
            
            with pytest.raises(ValueError, match="Insufficient funds"):
                create_transaction.create_transaction(
                    recipient=test_recipient,
                    amount=10000,
                    private_key_pem=private_key_pem
                )

    def test_create_transaction_with_custom_nonce(
        self,
        create_transaction,
        test_recipient,
        private_key_pem,
        public_key_pem
    ):
        """Test transaction creation with custom nonce."""
        custom_nonce = 12345
        test_values = [Value("0x1000", 1000)]
        
        with patch.object(create_transaction.value_selector, 'pick_values_for_transaction') as mock_pick:
            mock_pick.return_value = (test_values, None, None, None)
            
            with patch.object(create_transaction.value_selector, 'commit_transaction_values') as mock_commit:
                mock_commit.return_value = None
                
                # Create transaction with custom nonce
                result = create_transaction.create_transaction(
                    recipient=test_recipient,
                    amount=500,
                    private_key_pem=private_key_pem,
                    nonce=custom_nonce
                )
                
                # Verify nonce is used correctly
                main_tx = result["main_transaction"]
                assert main_tx.nonce == custom_nonce

    def test_get_account_balance(self, create_transaction):
        """Test getting account balance."""
        expected_balance = 1500
        
        with patch.object(create_transaction.value_selector, 'get_account_balance') as mock_balance:
            mock_balance.return_value = expected_balance
            
            balance = create_transaction.get_account_balance()
            
            assert balance == expected_balance
            mock_balance.assert_called_once_with(ValueState.UNSPENT)

    def test_get_account_values(self, create_transaction):
        """Test getting account values."""
        test_values = [Value("0x1000", 1000), Value("0x2000", 500)]
        
        with patch.object(create_transaction.value_selector, 'get_account_values') as mock_values:
            mock_values.return_value = test_values
            
            values = create_transaction.get_account_values()
            
            assert values == test_values
            mock_values.assert_called_once_with(None)

    def test_get_account_values_with_state_filter(self, create_transaction):
        """Test getting account values with state filter."""
        test_values = [Value("0x1000", 1000)]
        
        with patch.object(create_transaction.value_selector, 'get_account_values') as mock_values:
            mock_values.return_value = test_values
            
            values = create_transaction.get_account_values(ValueState.UNSPENT)
            
            assert values == test_values
            mock_values.assert_called_once_with(ValueState.UNSPENT)

    def test_confirm_transaction_success(self, create_transaction):
        """Test successful transaction confirmation."""
        test_values = [Value("0x1000", 1000)]
        change_value = Value("0x2000", 200)
        
        transaction_result = {
            "selected_values": test_values,
            "change_value": change_value
        }
        
        with patch.object(create_transaction.value_selector, 'confirm_transaction_values') as mock_confirm:
            mock_confirm.return_value = None
            
            result = create_transaction.confirm_transaction(transaction_result)
            
            assert result is True
            assert mock_confirm.call_count == 2  # Called for both selected and change values

    def test_confirm_transaction_no_change(self, create_transaction):
        """Test transaction confirmation with no change."""
        test_values = [Value("0x1000", 1000)]
        
        transaction_result = {
            "selected_values": test_values,
            "change_value": None
        }
        
        with patch.object(create_transaction.value_selector, 'confirm_transaction_values') as mock_confirm:
            mock_confirm.return_value = None
            
            result = create_transaction.confirm_transaction(transaction_result)
            
            assert result is True
            assert mock_confirm.call_count == 1  # Called only for selected values

    def test_confirm_transaction_failure(self, create_transaction):
        """Test transaction confirmation failure."""
        test_values = [Value("0x1000", 1000)]
        
        transaction_result = {
            "selected_values": test_values,
            "change_value": None
        }
        
        with patch.object(create_transaction.value_selector, 'confirm_transaction_values') as mock_confirm:
            mock_confirm.side_effect = Exception("Confirmation failed")
            
            result = create_transaction.confirm_transaction(transaction_result)
            
            assert result is False

    def test_cleanup_confirmed_values(self, create_transaction):
        """Test cleaning up confirmed values."""
        expected_count = 3
        
        with patch.object(create_transaction.value_selector, 'cleanup_confirmed_values') as mock_cleanup:
            mock_cleanup.return_value = expected_count
            
            count = create_transaction.cleanup_confirmed_values()
            
            assert count == expected_count
            mock_cleanup.assert_called_once()

    def test_validate_account_integrity(self, create_transaction):
        """Test account integrity validation."""
        expected_result = True
        
        with patch.object(create_transaction.value_selector, 'validate_account_integrity') as mock_validate:
            mock_validate.return_value = expected_result
            
            result = create_transaction.validate_account_integrity()
            
            assert result == expected_result
            mock_validate.assert_called_once()

    def test_print_transaction_details(self, create_transaction, capsys):
        """Test printing transaction details."""
        test_values = [Value("0x1000", 1000)]
        change_value = Value("0x2000", 200)
        
        # Mock transaction with hash
        main_tx = Transaction(
            sender=create_transaction.sender_address,
            recipient="0xRecipient",
            nonce=123,
            signature="mock_signature",
            value=test_values,
            time=datetime.now().isoformat()
        )
        main_tx.tx_hash = b"mock_hash_123"
        
        change_tx = Transaction(
            sender=create_transaction.sender_address,
            recipient=create_transaction.sender_address,
            nonce=123,
            signature="mock_signature",
            value=[change_value],
            time=datetime.now().isoformat()
        )
        change_tx.tx_hash = b"mock_hash_change"
        
        transaction_result = {
            "main_transaction": main_tx,
            "change_transaction": change_tx,
            "selected_values": test_values,
            "change_value": change_value,
            "total_amount": 1000,
            "transaction_fee": 0
        }
        
        # Call print method
        create_transaction.print_transaction_details(transaction_result)
        
        # Check output
        captured = capsys.readouterr()
        assert "=== Transaction Details ===" in captured.out
        assert f"Sender: {create_transaction.sender_address}" in captured.out
        assert "Total Amount: 1000" in captured.out
        assert "Transaction Hash: mock_hash_123" in captured.out
        assert "Change Transaction Hash: mock_hash_change" in captured.out

    def test_invalid_private_key_format(self, create_transaction, test_recipient):
        """Test transaction creation with invalid private key format."""
        invalid_key = b"invalid_key_format"
        
        with patch.object(create_transaction.value_selector, 'pick_values_for_transaction') as mock_pick:
            mock_pick.return_value = ([Value("0x1000", 1000)], None, None, None)
            
            with patch.object(create_transaction.value_selector, 'commit_transaction_values') as mock_commit:
                mock_commit.return_value = None
                
                # Should raise an exception due to invalid key format
                with pytest.raises(Exception):
                    create_transaction.create_transaction(
                        recipient=test_recipient,
                        amount=500,
                        private_key_pem=invalid_key
                    )

    def test_multiple_transactions_creation(self, create_transaction, test_recipient, private_key_pem, public_key_pem):
        """Test creating multiple transactions."""
        test_values1 = [Value("0x1000", 1000)]
        test_values2 = [Value("0x2000", 500)]
        
        # First transaction
        with patch.object(create_transaction.value_selector, 'pick_values_for_transaction') as mock_pick:
            mock_pick.return_value = (test_values1, None, None, None)
            
            with patch.object(create_transaction.value_selector, 'commit_transaction_values') as mock_commit:
                mock_commit.return_value = None
                
                result1 = create_transaction.create_transaction(
                    recipient=test_recipient,
                    amount=800,
                    private_key_pem=private_key_pem
                )
                
                assert len(create_transaction.created_transactions) == 1
                
                # Second transaction
                mock_pick.return_value = (test_values2, None, None, None)
                mock_commit.return_value = None
                
                result2 = create_transaction.create_transaction(
                    recipient=test_recipient,
                    amount=300,
                    private_key_pem=private_key_pem
                )
                
                assert len(create_transaction.created_transactions) == 2
                assert create_transaction.created_transactions[0] == result1
                assert create_transaction.created_transactions[1] == result2

    @pytest.mark.parametrize("amount,expected_total", [
        (100, 100),
        (500, 500),
        (1000, 1000),
        (0, 0),  # Edge case: zero amount
    ])
    def test_various_transaction_amounts(
        self,
        create_transaction,
        test_recipient,
        private_key_pem,
        amount,
        expected_total
    ):
        """Test transaction creation with various amounts."""
        test_values = [Value("0x1000", 1000)]
        
        with patch.object(create_transaction.value_selector, 'pick_values_for_transaction') as mock_pick:
            mock_pick.return_value = (test_values, None, None, None)
            
            with patch.object(create_transaction.value_selector, 'commit_transaction_values') as mock_commit:
                mock_commit.return_value = None
                
                result = create_transaction.create_transaction(
                    recipient=test_recipient,
                    amount=amount,
                    private_key_pem=private_key_pem
                )
                
                assert result["total_amount"] == expected_total

if __name__ == "__main__":
    pytest.main([__file__, "-v"])