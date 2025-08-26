from typing import List, Tuple, Optional
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from EZ_Value.Value import Value, ValueState
from EZ_Value.AccountValueCollection import AccountValueCollection
from EZ_Transaction.SingleTransaction import Transaction

class AccountPickValues:
    """增强版Value选择器，基于AccountValueCollection实现高效调度"""
    
    def __init__(self, account_address: str):
        self.account_collection = AccountValueCollection(account_address)
        
    def add_values_from_list(self, values: List[Value]) -> int:
        """从Value列表批量添加Value"""
        added_count = 0
        for value in values:
            if self.account_collection.add_value(value):
                added_count += 1
        return added_count
    
    def pick_values_for_transaction(self, required_amount: int, sender: str, recipient: str, 
                                 nonce: int, tx_hash: str, time: int) -> Tuple[List[Value], Optional[Value], Optional[Transaction], Optional[Transaction]]:
        """为交易选择Value，返回选中的值、找零、找零交易、主交易"""
        if required_amount < 1:
            raise ValueError("交易金额必须大于等于1")
            
        selected_values = []
        total_selected = 0
        change_value = None
        
        # 获取可用的未花销Value
        available_values = self.account_collection.find_by_state(ValueState.UNSPENT)
        
        # 贪心算法选择Value
        for value in available_values:
            if total_selected >= required_amount:
                break
            
            selected_values.append(value)
            total_selected += value.value_num
            
        # 检查余额是否足够
        if total_selected < required_amount:
            raise ValueError("余额不足！")
            
        # 计算找零
        change_amount = total_selected - required_amount
        
        # 创建交易
        change_transaction = None
        main_transaction = None
        
        #TODO: 未实现交易签名
        #判断是否需要找零
        if change_amount > 0 and selected_values != []:
            # 选择最后一个Value进行分裂
            last_value = selected_values[-1]
            
            # 在AccountValueCollection中找到对应的节点并分裂
            node_id = self._find_node_by_value(last_value)
            if node_id:
                v1, v2 = self.account_collection.split_value(node_id, change_amount)
                
                if v1 and v2:
                    # 更新选中值列表
                    selected_values[-1] = v1
                    change_value = v2
                    
                    # 将找零v2状态设置为SELECTED
                    self._update_value_state(v2, ValueState.SELECTED)
                    
                    # 创建找零交易
                    change_transaction = Transaction(
                        sender=sender,
                        recipient=recipient,
                        nonce=nonce,
                        signature=None,
                        value=[v2],
                        tx_hash=tx_hash,
                        time=time
                    )
                    
                    # 创建主交易
                    main_transaction = Transaction(
                        sender=sender,
                        recipient=recipient,
                        nonce=nonce,
                        signature=None,
                        value=[v1] + selected_values[:-1],
                        tx_hash=tx_hash,
                        time=time
                    )
        else:
            # 不需要找零，直接使用所有选中的值
            main_transaction = Transaction(
                sender=sender,
                recipient=recipient,
                nonce=nonce,
                signature=None,
                value=selected_values,
                tx_hash=tx_hash,
                time=time
            )
        
        # 将选中的Value状态更新为SELECTED
        for value in selected_values:
            self._update_value_state(value, ValueState.SELECTED)
            
        return selected_values, change_value, change_transaction, main_transaction
    
    def commit_transaction_values(self, selected_values: List[Value]) -> bool:
        """将选中的Value状态更新为LOCAL_COMMITTED"""
        for value in selected_values:
            self._update_value_state(value, ValueState.LOCAL_COMMITTED)
        return True
    
    def confirm_transaction_values(self, confirmed_values: List[Value]) -> bool:
        """确认交易，将Value状态更新为CONFIRMED"""
        for value in confirmed_values:
            self._update_value_state(value, ValueState.CONFIRMED)
        return True
    
    def rollback_transaction_selection(self, selected_values: List[Value]) -> bool:
        """回滚交易选择，将Value状态恢复为UNSPENT"""
        for value in selected_values:
            self._update_value_state(value, ValueState.UNSPENT)
        return True
    
    # 暂时不需要使用合并功能（EZchain系统暂不提供此功能）
    def optimize_values(self) -> List[Value]:
        """优化相邻的Value，合并连续的Value"""
        values = self.account_collection.get_values_sorted_by_begin_index()
        merged_values = []
        
        for i in range(len(values)):
            current_value = values[i]
            merged = False
            
            # 检查是否可以与之前的值合并
            if merged_values and self._are_adjacent(merged_values[-1], current_value):
                node_id1 = self._find_node_by_value(merged_values[-1])
                node_id2 = self._find_node_by_value(current_value)
                if node_id1 and node_id2:
                    merged_value = self.account_collection.merge_adjacent_values(node_id1, node_id2)
                    if merged_value:
                        merged_values[-1] = merged_value
                        merged = True
            
            if not merged:
                merged_values.append(current_value)
                
        return merged_values
    
    def get_account_balance(self, state: ValueState = ValueState.UNSPENT) -> int:
        """获取账户指定状态的余额"""
        return self.account_collection.get_balance_by_state(state)
    
    def get_total_account_balance(self) -> int:
        """获取账户总余额"""
        return self.account_collection.get_total_balance()
    
    def get_account_values(self, state: Optional[ValueState] = None) -> List[Value]:
        """获取账户Value列表"""
        if state is None:
            return self.account_collection.get_all_values()
        return self.account_collection.find_by_state(state)
    
    def cleanup_confirmed_values(self) -> int:
        """清除已确认的Value"""
        count = len(self.account_collection._state_index[ValueState.CONFIRMED])
        self.account_collection.clear_spent_values()
        return count
    
    def validate_account_integrity(self) -> bool:
        """验证账户完整性"""
        return self.account_collection.validate_no_overlap()
    
    def _find_node_by_value(self, target_value: Value) -> Optional[str]:
        """根据Value找到对应的node_id"""
        for node_id, node in self.account_collection._index_map.items():
            if node.value.is_same_value(target_value):
                return node_id
        return None
    
    def _update_value_state(self, value: Value, new_state: ValueState) -> bool:
        """更新Value状态"""
        node_id = self._find_node_by_value(value)
        if node_id:
            return self.account_collection.update_value_state(node_id, new_state)
        return False
    
    # 暂时不需要使用合并功能（EZchain系统暂不提供此功能）
    def _are_adjacent(self, value1: Value, value2: Value) -> bool:
        """检查两个Value是否相邻"""
        if value1.state != value2.state:
            return False
            
        end1 = value1.get_decimal_end_index()
        start2 = value2.get_decimal_begin_index()
        
        return end1 + 1 == start2