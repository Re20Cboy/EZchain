from typing import List, Tuple, Optional

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from EZ_Transaction.SingleTransaction import Transaction
from EZ_Value.Value import Value

class PickValues:
    """
    A class for picking values from available UTXOs and generating transactions.
    
    This class implements the greedy algorithm for selecting UTXOs to meet
    a specific transaction amount, with support for change handling.
    """
    
    def pick_values_and_generate_txns(v_lst: [List[Value]], tx_num: int, tx_sender: str, tx_recipient: str, 
                                      tx_nonce: int, tx_hash: str, tx_time: int) -> Tuple[List[int], int, Optional[Transaction], Optional[Transaction]]:
        """Pick values and generate transactions for the specified amount.
        
        Args:
            tx_num: The total amount of value to pick (must be >= 1)
            tx_sender: Sender address for transactions
            tx_recipient: Recipient address for transactions
            tx_nonce: Nonce for transactions
            tx_hash: Transaction hash
            tx_time: Transaction timestamp

        Returns:
            tuple: (costList, changeValueIndex, txn_2_sender, txn_2_recipient)
                - costList: List of indices of selected ValuePrfBlockPairs
                - changeValueIndex: Index of the value that was split for change, or -1
                - txn_2_sender: Transaction for the change amount
                - txn_2_recipient: Transaction for the main amount
            
        Raises:
            ValueError: If tx_num is less than 1 or balance is insufficient
        """
        if tx_num < 1:
            raise ValueError("The value of tx_num cannot be less than 1")

        total_selected = 0
        selected_indices = []
        change_value_index = -1
        change_transaction = None
        main_transaction = None
        
        # Iterate through available values to select enough for the transaction
        for index, value in enumerate(v_lst):
            # Skip values that are unconfirmed
            if value.can_be_select() is False:
                continue

            # Skip values already selected in previous rounds
            if value in [cost_value[0] for cost_value in self.costedValuesAndRecipes]:
                continue
                
            total_selected += value.valueNum
            selected_indices.append(index)
            
            # Check if we've selected enough value
            if total_selected >= tx_num:
                change_value_index = index
                break
                
        # Check if we have enough balance
        if total_selected < tx_num:
            raise ValueError("Insufficient balance!")
            
        change_amount = total_selected - tx_num
        
        # If there's change, split the last selected value and create transactions
        if change_amount > 0:
            change_value_obj = self.ValuePrfBlockPair[change_value_index][0]
            main_value, change_value = change_value_obj.split_value(change_amount)
            
            # Create transaction for the change amount
            change_transaction = Transaction(
                sender=tx_sender,
                recipient=tx_recipient,
                nonce=tx_nonce,
                signature=None,
                value=[change_value],
                tx_hash=tx_hash,
                time=tx_time
            )
            change_transaction.sig_txn(self.privateKey)
            
            # Create transaction for the main amount
            main_transaction = Transaction(
                sender=tx_sender,
                recipient=tx_recipient,
                nonce=tx_nonce,
                signature=None,
                value=[main_value],
                tx_hash=tx_hash,
                time=tx_time
            )
            main_transaction.sig_txn(self.privateKey)

            # Record the main value as used
            self.costedValuesAndRecipes.append((main_value, tx_recipient))
        else:
            change_value_index = -1
            
        return selected_indices, change_value_index, change_transaction, main_transaction