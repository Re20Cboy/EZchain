"""
Transaction Creation Module for EZchain Blockchain

This module provides a comprehensive transaction creation system that integrates
value selection, secure signature handling, and transaction management.
"""

import sys
import os
from typing import List, Optional, Dict, Any
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from EZ_Transaction.SingleTransaction import Transaction
from EZ_Value.AccountPickValues import AccountPickValues
from EZ_Value.Value import Value, ValueState
from EZ_Tool_Box.SecureSignature import secure_signature_handler
from EZ_Tool_Box.Hash import sha256_hash


class CreateTransaction:
    """
    Enhanced transaction creation system that integrates with existing
    value selection and secure signature functionality.
    """
    
    def __init__(self, sender_address: str):
        """
        Initialize the transaction creator with sender's account.
        
        Args:
            sender_address: The address of the sender account
        """
        self.sender_address = sender_address
        self.value_selector = AccountPickValues(sender_address)
        self.created_transactions = []
    
    def create_transaction(
        self,
        recipient: str,
        amount: int,
        private_key_pem: bytes,
        nonce: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a transaction with automatic value selection.
        
        Args:
            recipient: Recipient address
            amount: Transaction amount
            private_key_pem: Private key in PEM format for signing
            nonce: Transaction nonce (auto-generated if None)
            
        Returns:
            Dictionary containing transaction data and metadata
        """
        if nonce is None:
            nonce = self._generate_nonce()
        
        timestamp = datetime.now().isoformat()
        
        # Select values for the transaction
        selected_values, change_value, change_transaction, main_transaction = \
            self.value_selector.pick_values_for_transaction(
                required_amount=amount,
                sender=self.sender_address,
                recipient=recipient,
                nonce=nonce,
                time=timestamp
            )
        
        # Create main transaction using the Transaction constructor with auto-calculated hash
        main_transaction = Transaction(
            sender=self.sender_address,
            recipient=recipient,
            nonce=nonce,
            signature=None,
            value=selected_values,
            time=timestamp
        )
        
        # Sign the main transaction using secure signature handler
        main_transaction.sig_txn(private_key_pem)
        
        # Handle change transaction if needed
        if change_value:
            # Create change transaction using the Transaction constructor
            change_transaction = Transaction(
                sender=self.sender_address,
                recipient=self.sender_address,  # Change goes back to sender
                nonce=nonce,
                signature=None,
                value=[change_value],
                time=timestamp
            )
            
            # Sign the change transaction
            change_transaction.sig_txn(private_key_pem)
        
        # Commit the selected values
        self.value_selector.commit_transaction_values(selected_values)
        
        # Store created transactions
        result = {
            "main_transaction": main_transaction,
            "change_transaction": change_transaction,
            "selected_values": selected_values,
            "change_value": change_value,
            "total_amount": amount,
            "transaction_fee": 0  # Fee calculation can be added here
        }
        
        self.created_transactions.append(result)
        return result
    
    def verify_transaction_signature(
        self,
        transaction: Transaction,
        public_key_pem: bytes
    ) -> bool:
        """
        Verify a transaction signature using the secure signature handler.
        
        Args:
            transaction: The transaction to verify
            public_key_pem: Public key in PEM format
            
        Returns:
            True if signature is valid, False otherwise
        """
        return transaction.check_txn_sig(public_key_pem)
    
    def get_account_balance(self) -> int:
        """
        Get the current account balance.
        
        Returns:
            Available balance amount
        """
        return self.value_selector.get_account_balance(ValueState.UNSPENT)
    
    def get_account_values(self, state: Optional[ValueState] = None) -> List[Value]:
        """
        Get values from the account.
        
        Args:
            state: Optional state filter
            
        Returns:
            List of values
        """
        return self.value_selector.get_account_values(state)
    
    def confirm_transaction(self, transaction_result: Dict[str, Any]) -> bool:
        """
        Confirm a transaction and update value states.
        
        Args:
            transaction_result: Result from create_transaction method
            
        Returns:
            True if confirmation successful, False otherwise
        """
        try:
            # Confirm main transaction values
            if transaction_result["selected_values"]:
                self.value_selector.confirm_transaction_values(
                    transaction_result["selected_values"]
                )
            
            # Confirm change transaction values
            if transaction_result["change_value"]:
                self.value_selector.confirm_transaction_values(
                    [transaction_result["change_value"]]
                )
            
            return True
        except Exception as e:
            print(f"Error confirming transaction: {e}")
            return False
    
    def print_transaction_details(self, transaction_result: Dict[str, Any]) -> None:
        """
        Print detailed information about a transaction.
        
        Args:
            transaction_result: Result from create_transaction method
        """
        print("=== Transaction Details ===")
        print(f"Sender: {self.sender_address}")
        print(f"Recipient: {transaction_result['main_transaction'].recipient}")
        print(f"Nonce: {transaction_result['main_transaction'].nonce}")
        print(f"Total Amount: {transaction_result['total_amount']}")
        print(f"Transaction Hash: {transaction_result['main_transaction'].tx_hash.hex()}")
        
        print("\nSelected Values:")
        for i, value in enumerate(transaction_result['selected_values']):
            print(f"  Value {i+1}: {value.begin_index} - {value.end_index} ({value.value_num})")
        
        if transaction_result['change_value']:
            print(f"\nChange Value: {transaction_result['change_value'].begin_index} - {transaction_result['change_value'].end_index} ({transaction_result['change_value'].value_num})")
        
        if transaction_result['change_transaction']:
            print(f"\nChange Transaction Hash: {transaction_result['change_transaction'].tx_hash.hex()}")
        
        print("========================")
    
    def _generate_nonce(self) -> int:
        """Generate a unique nonce for the transaction."""
        return int(datetime.now().timestamp() * 1000000)
    
    
    def cleanup_confirmed_values(self) -> int:
        """
        Clean up confirmed values from the account.
        
        Returns:
            Number of cleaned up values
        """
        return self.value_selector.cleanup_confirmed_values()
    
    def validate_account_integrity(self) -> bool:
        """
        Validate the integrity of the account's values.
        
        Returns:
            True if account is valid, False otherwise
        """
        return self.value_selector.validate_account_integrity()
