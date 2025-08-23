import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from EZ_Transaction.SingleTransaction import Transaction

#TODO: 值选择模块应提供多种选择算法插件（e.g., 贪心选择）。



class PickValues:
    def pick_values_and_generate_txns(self, tx_num, tx_sender, tx_recipient, tx_nonce, tx_hash, tx_time):
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
            
        Raises:
            ValueError: If tx_num is less than 1 or balance is insufficient
        """
        if tx_num < 1:
            raise ValueError("The value of tx_num cannot be less than 1")

        tmp_cost = 0
        cost_list = []
        change_value_index = -1
        txn_2_sender = None
        txn_2_recipient = None
        value_enough = False
        
        for i, vpb_pair in enumerate(self.ValuePrfBlockPair):
            value = vpb_pair[0]

            # check the value is costed (unconfirmed and confirmed)
            if value in self.unconfirmed_value_list:
                continue

            # check the values whether have been select in pre round txn
            if value in [cost_value[0] for cost_value in self.costedValuesAndRecipes]:
                continue
                
            tmp_cost += value.valueNum
            cost_list.append(i)
            
            if tmp_cost >= tx_num:
                change_value_index = i
                value_enough = True
                break
                
        if not value_enough:
            raise ValueError("Insufficient balance!")
            
        change = tmp_cost - tx_num
        
        if change > 0:
            value_obj = self.ValuePrfBlockPair[change_value_index][0]
            V1, V2 = value_obj.split_value(change)
            
            txn_2_sender = Transaction(
                sender=tx_sender,
                recipient=tx_recipient,
                nonce=tx_nonce,
                signature=None,
                value=[V2],
                tx_hash=tx_hash,
                time=tx_time
            )
            txn_2_sender.sig_txn(self.privateKey)
            
            txn_2_recipient = Transaction(
                sender=tx_sender,
                recipient=tx_recipient,
                nonce=tx_nonce,
                signature=None,
                value=[V1],
                tx_hash=tx_hash,
                time=tx_time
            )
            txn_2_recipient.sig_txn(self.privateKey)

            self.costedValuesAndRecipes.append((V1, tx_recipient))
        else:
            change_value_index = -1
            
        return cost_list, change_value_index, txn_2_sender, txn_2_recipient