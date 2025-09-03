"""
Multi-Transaction Creation Module for EZchain Blockchain

This module provides a comprehensive multi-transaction creation system that integrates
value selection, secure signature handling, and batch transaction management.
"""

import sys
import os
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from EZ_Transaction.SingleTransaction import Transaction
from EZ_Transaction.MultiTransactions import MultiTransactions
from EZ_Value.AccountPickValues import AccountPickValues
from EZ_Value.Value import Value, ValueState
from EZ_Tool_Box.SecureSignature import secure_signature_handler
from EZ_Tool_Box.Hash import sha256_hash


class CreateMultiTransactions:
    """
    Enhanced multi-transaction creation system that integrates with existing
    value selection and secure signature functionality.
    """
    
    def __init__(self, sender_address: str):
        """
        Initialize the multi-transaction creator with sender's account.
        
        Args:
            sender_address: The address of the sender account
        """
        self.sender_address = sender_address
        self.value_selector = AccountPickValues(sender_address)
        self.created_multi_transactions = []
    
    def create_multi_transactions(
        self,
        transaction_requests: List[Dict[str, Any]],
        private_key_pem: bytes,
        base_nonce: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create multiple transactions as a single MultiTransactions batch.
        
        Args:
            transaction_requests: List of transaction requests with 'recipient' and 'amount'
            private_key_pem: Private key in PEM format for signing
            base_nonce: Base nonce for transactions (auto-generated if None)
            
        Returns:
            Dictionary containing MultiTransactions data and metadata
        """
        if not transaction_requests:
            raise ValueError("Transaction requests cannot be empty")
        
        if base_nonce is None:
            base_nonce = self._generate_nonce()
        
        timestamp = datetime.now().isoformat()
        
        # Process each transaction request
        transactions = []
        selected_values_list = []
        change_values_list = []
        total_amount = 0
        
        for i, request in enumerate(transaction_requests):
            recipient = request.get('recipient')
            amount = request.get('amount')
            
            if not recipient or amount is None:
                raise ValueError(f"Transaction request {i} missing recipient or amount")
            
            # Calculate nonce for this transaction
            nonce = base_nonce + i
            
            # Select values for this transaction
            selected_values, change_value, change_transaction, main_transaction = \
                self.value_selector.pick_values_for_transaction(
                    required_amount=amount,
                    sender=self.sender_address,
                    recipient=recipient,
                    nonce=nonce,
                    time=timestamp
                )
            
            # Create main transaction
            main_transaction = Transaction(
                sender=self.sender_address,
                recipient=recipient,
                nonce=nonce,
                signature=None,
                value=selected_values,
                time=timestamp
            )
            
            # Sign the main transaction
            main_transaction.sig_txn(private_key_pem)
            
            # Handle change transaction if needed
            change_txn_obj = None
            if change_value:
                change_transaction = Transaction(
                    sender=self.sender_address,
                    recipient=self.sender_address,
                    nonce=nonce,
                    signature=None,
                    value=[change_value],
                    time=timestamp
                )
                
                # Sign the change transaction
                change_transaction.sig_txn(private_key_pem)
                change_txn_obj = change_transaction
                change_values_list.append(change_value)
            
            transactions.append(main_transaction)
            if change_txn_obj:
                transactions.append(change_txn_obj)
            
            selected_values_list.extend(selected_values)
            total_amount += amount
        
        # Create MultiTransactions object
        multi_txn = MultiTransactions(
            sender=self.sender_address,
            multi_txns=transactions
        )
        
        # Set the timestamp
        multi_txn.time = timestamp
        
        # Sign the MultiTransactions
        multi_txn.sig_acc_txn(private_key_pem)
        
        # Commit all selected values
        self.value_selector.commit_transaction_values(selected_values_list)
        
        # Store created multi-transactions
        result = {
            "multi_transactions": multi_txn,
            "transactions": transactions,
            "selected_values": selected_values_list,
            "change_values": change_values_list,
            "total_amount": total_amount,
            "transaction_count": len(transaction_requests),
            "base_nonce": base_nonce,
            "timestamp": timestamp
        }
        
        self.created_multi_transactions.append(result)
        return result
    
    def create_uniform_multi_transactions(
        self,
        recipients: List[str],
        amount_per_transaction: int,
        private_key_pem: bytes,
        base_nonce: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create multiple transactions with the same amount for different recipients.
        
        Args:
            recipients: List of recipient addresses
            amount_per_transaction: Amount to send to each recipient
            private_key_pem: Private key in PEM format for signing
            base_nonce: Base nonce for transactions (auto-generated if None)
            
        Returns:
            Dictionary containing MultiTransactions data and metadata
        """
        transaction_requests = [
            {"recipient": recipient, "amount": amount_per_transaction}
            for recipient in recipients
        ]
        
        return self.create_multi_transactions(transaction_requests, private_key_pem, base_nonce)
    
    def create_variable_multi_transactions(
        self,
        recipient_amount_pairs: List[Tuple[str, int]],
        private_key_pem: bytes,
        base_nonce: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create multiple transactions with different amounts for different recipients.
        
        Args:
            recipient_amount_pairs: List of (recipient, amount) tuples
            private_key_pem: Private key in PEM format for signing
            base_nonce: Base nonce for transactions (auto-generated if None)
            
        Returns:
            Dictionary containing MultiTransactions data and metadata
        """
        transaction_requests = [
            {"recipient": recipient, "amount": amount}
            for recipient, amount in recipient_amount_pairs
        ]
        
        return self.create_multi_transactions(transaction_requests, private_key_pem, base_nonce)
    
    def verify_multi_transactions_signature(
        self,
        multi_txn: MultiTransactions,
        public_key_pem: bytes
    ) -> bool:
        """
        Verify a MultiTransactions signature using the secure signature handler.
        
        Args:
            multi_txn: The MultiTransactions to verify
            public_key_pem: Public key in PEM format
            
        Returns:
            True if signature is valid, False otherwise
        """
        return multi_txn.check_acc_txn_sig(public_key_pem)
    
    def verify_all_transaction_signatures(
        self,
        multi_txn: MultiTransactions,
        public_key_pem: bytes
    ) -> Dict[str, bool]:
        """
        Verify all individual transaction signatures within a MultiTransactions.
        
        Args:
            multi_txn: The MultiTransactions containing transactions to verify
            public_key_pem: Public key in PEM format
            
        Returns:
            Dictionary mapping transaction indices to verification results
        """
        results = {}
        
        for i, txn in enumerate(multi_txn.multi_txns):
            results[f"transaction_{i}"] = txn.check_txn_sig(public_key_pem)
        
        return results
    
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
    
    def confirm_multi_transactions(self, multi_txn_result: Dict[str, Any]) -> bool:
        """
        Confirm a multi-transaction and update value states.
        
        Args:
            multi_txn_result: Result from create_multi_transactions method
            
        Returns:
            True if confirmation successful, False otherwise
        """
        try:
            # Confirm all selected values
            if multi_txn_result["selected_values"]:
                self.value_selector.confirm_transaction_values(
                    multi_txn_result["selected_values"]
                )
            
            # Confirm change values
            if multi_txn_result["change_values"]:
                self.value_selector.confirm_transaction_values(
                    multi_txn_result["change_values"]
                )
            
            return True
        except Exception as e:
            print(f"Error confirming multi-transaction: {e}")
            return False
    
    def print_multi_transactions_details(self, multi_txn_result: Dict[str, Any]) -> None:
        """
        Print detailed information about a multi-transaction.
        
        Args:
            multi_txn_result: Result from create_multi_transactions method
        """
        print("=== Multi-Transactions Details ===")
        print(f"Sender: {self.sender_address}")
        print(f"Transaction Count: {multi_txn_result['transaction_count']}")
        print(f"Total Amount: {multi_txn_result['total_amount']}")
        print(f"Base Nonce: {multi_txn_result['base_nonce']}")
        print(f"Timestamp: {multi_txn_result['timestamp']}")
        print(f"Multi-Transactions Hash: {multi_txn_result['multi_transactions'].digest}")
        
        print("\nIndividual Transactions:")
        for i, txn in enumerate(multi_txn_result['transactions']):
            print(f"  Transaction {i+1}:")
            print(f"    Recipient: {txn.recipient}")
            print(f"    Nonce: {txn.nonce}")
            print(f"    Hash: {txn.tx_hash.hex()}")
            print(f"    Values: {len(txn.value)} value(s)")
        
        print(f"\nTotal Selected Values: {len(multi_txn_result['selected_values'])}")
        print(f"Total Change Values: {len(multi_txn_result['change_values'])}")
        print("===============================")
    
    def get_transaction_summary(self, multi_txn_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get a summary of the multi-transaction.
        
        Args:
            multi_txn_result: Result from create_multi_transactions method
            
        Returns:
            Dictionary containing transaction summary
        """
        return {
            "sender": self.sender_address,
            "transaction_count": multi_txn_result['transaction_count'],
            "total_amount": multi_txn_result['total_amount'],
            "total_values_used": len(multi_txn_result['selected_values']),
            "total_change_values": len(multi_txn_result['change_values']),
            "base_nonce": multi_txn_result['base_nonce'],
            "timestamp": multi_txn_result['timestamp'],
            "multi_transactions_hash": multi_txn_result['multi_transactions'].digest,
            "recipients": [txn.recipient for txn in multi_txn_result['transactions'] 
                          if txn.recipient != self.sender_address]  # Exclude change transactions
        }
    
    def validate_multi_transactions_structure(self, multi_txn: MultiTransactions) -> Tuple[bool, str]:
        """
        Validate the structure of a MultiTransactions object.
        
        Args:
            multi_txn: The MultiTransactions to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not multi_txn.multi_txns:
            return False, "MultiTransactions cannot be empty"
        
        if not multi_txn.sender:
            return False, "Sender cannot be empty"
        
        if multi_txn.sender != self.sender_address:
            return False, f"Sender mismatch: expected {self.sender_address}, got {multi_txn.sender}"
        
        # Check all transactions have the same sender
        for i, txn in enumerate(multi_txn.multi_txns):
            if not isinstance(txn, Transaction):
                return False, f"Transaction {i} is not a valid Transaction object"
            
            if txn.sender != self.sender_address:
                return False, f"Transaction {i} has different sender: expected {self.sender_address}, got {txn.sender}"
        
        return True, "Validation passed"
    
    def submit_to_transaction_pool(self, multi_txn_result: Dict[str, Any], transaction_pool, public_key_pem: bytes = None) -> Tuple[bool, str]:
        """
        Submit the MultiTransactions to a transaction pool.
        
        Args:
            multi_txn_result: Result from create_multi_transactions method
            transaction_pool: TransactionPool instance to submit to
            public_key_pem: Public key for validation (optional)
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Validate structure first
            is_valid, error_msg = self.validate_multi_transactions_structure(multi_txn_result['multi_transactions'])
            if not is_valid:
                return False, error_msg
            
            # Submit to pool
            success, message = transaction_pool.add_multi_transactions(
                multi_txn_result['multi_transactions'], 
                public_key_pem
            )
            
            return success, message
        except Exception as e:
            return False, f"Error submitting to transaction pool: {str(e)}"
    
    def _generate_nonce(self) -> int:
        """Generate a unique nonce for the transactions."""
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
    
    def get_created_multi_transactions(self) -> List[Dict[str, Any]]:
        """
        Get all created multi-transactions.
        
        Returns:
            List of multi-transaction results
        """
        return self.created_multi_transactions.copy()
    
    def clear_created_multi_transactions(self) -> None:
        """Clear the list of created multi-transactions."""
        self.created_multi_transactions.clear()