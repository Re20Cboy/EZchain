from typing import List, Tuple, Optional, Set, Dict
from collections import defaultdict
import uuid

from EZ_Value.Value import Value, ValueState

class ValueNode:
    """链表节点，用于管理Value及其索引"""
    def __init__(self, value: Value, node_id: str = None):
        self.value = value
        self.node_id = node_id or str(uuid.uuid4())
        self.next = None
        self.prev = None
        
class AccountValueCollection:
    """账户Value集合管理类 - 使用链表结构解决index混乱问题"""
    
    def __init__(self, account_address: str):
        self.account_address = account_address
        self.head = None  # 链表头节点
        self.tail = None  # 链表尾节点
        self.size = 0
        self._index_map = {}  # node_id到节点的映射
        self._state_index = defaultdict(set)  # 按状态快速索引
        self._decimal_begin_map = {}  # 按起始十进制值映射，用于快速查找
        
    def add_value(self, value: Value, position: str = "end") -> bool:
        """添加Value到集合中"""
        node = ValueNode(value)
        
        if position == "end":
            if self.tail is None:
                self.head = node
                self.tail = node
            else:
                self.tail.next = node
                node.prev = self.tail
                self.tail = node
        elif position == "beginning":
            if self.head is None:
                self.head = node
                self.tail = node
            else:
                self.head.prev = node
                node.next = self.head
                self.head = node
        else:
            raise ValueError("position must be 'end' or 'beginning'")
        
        self._index_map[node.node_id] = node
        self._state_index[value.state].add(node.node_id)
        self._decimal_begin_map[value.get_decimal_begin_index()] = node.node_id
        self.size += 1
        
        return True
    
    def remove_value(self, node_id: str) -> bool:
        """根据node_id移除Value"""
        if node_id not in self._index_map:
            return False
            
        node = self._index_map[node_id]
        
        # 从状态索引中移除
        self._state_index[node.value.state].discard(node_id)
        
        # 从十进制索引中移除
        decimal_begin = node.value.get_decimal_begin_index()
        if decimal_begin in self._decimal_begin_map and self._decimal_begin_map[decimal_begin] == node_id:
            del self._decimal_begin_map[decimal_begin]
        
        # 从链表中移除节点
        if node.prev:
            node.prev.next = node.next
        else:
            self.head = node.next
            
        if node.next:
            node.next.prev = node.prev
        else:
            self.tail = node.prev
            
        # 从索引映射中移除
        del self._index_map[node_id]
        self.size -= 1
        
        return True
    
    def find_by_state(self, state: ValueState) -> List[Value]:
        """根据状态查找所有Value"""
        node_ids = self._state_index.get(state, set())
        return [self._index_map[node_id].value for node_id in node_ids]
    
    def find_by_range(self, start_decimal: int, end_decimal: int) -> List[Value]:
        """根据十进制范围查找Value"""
        result = []
        current = self.head
        
        while current:
            value = current.value
            val_start = value.get_decimal_begin_index()
            val_end = value.get_decimal_end_index()
            
            if not (val_end < start_decimal or val_start > end_decimal):
                result.append(value)
                
            current = current.next
            
        return result
    
    def find_intersecting_values(self, target: Value) -> List[Value]:
        """查找与target有交集的所有Value"""
        result = []
        current = self.head
        
        while current:
            if current.value.is_intersect_value(target):
                result.append(current.value)
            current = current.next
            
        return result
    
    def split_value(self, node_id: str, change: int) -> Tuple[Optional[Value], Optional[Value]]:
        """分裂指定Value"""
        if node_id not in self._index_map:
            return None, None
            
        node = self._index_map[node_id]
        original_value = node.value
        
        if change <= 0 or change >= original_value.value_num:
            return None, None
            
        # 分裂Value
        v1, v2 = original_value.split_value(change)
        
        # 更新原节点为V1
        node.value = v1
        
        # 创建新节点存放V2
        new_node = ValueNode(v2)
        
        # 将新节点插入到原节点之后
        new_node.prev = node
        new_node.next = node.next
        if node.next:
            node.next.prev = new_node
        else:
            self.tail = new_node
        node.next = new_node
        
        # 更新索引
        self._index_map[new_node.node_id] = new_node
        self._state_index[v2.state].add(new_node.node_id)
        self._decimal_begin_map[v2.get_decimal_begin_index()] = new_node.node_id
        self.size += 1
        
        return v1, v2
    
    # 暂时不需要使用合并功能（EZchain系统暂不提供此功能）
    def merge_adjacent_values(self, node_id1: str, node_id2: str) -> Optional[Value]:
        """合并两个相邻的Value"""
        if node_id1 not in self._index_map or node_id2 not in self._index_map:
            return None
            
        node1 = self._index_map[node_id1]
        node2 = self._index_map[node_id2]
        
        # 检查是否相邻
        if node1.next != node2 or node1.value.state != node2.value.state:
            return None
            
        # 创建合并后的Value
        new_begin = node1.value.begin_index
        new_num = node1.value.value_num + node2.value.value_num
        merged_value = Value(new_begin, new_num, node1.value.state)
        
        # 更新第一个节点
        node1.value = merged_value
        
        # 移除第二个节点
        self.remove_value(node_id2)
        
        return merged_value
    
    def update_value_state(self, node_id: str, new_state: ValueState) -> bool:
        """更新Value状态"""
        if node_id not in self._index_map:
            return False
            
        node = self._index_map[node_id]
        old_state = node.value.state
        
        if old_state == new_state:
            return True
            
        # 更新状态索引
        self._state_index[old_state].discard(node_id)
        self._state_index[new_state].add(node_id)
        node.value.set_state(new_state)
        
        return True
    
    def get_all_values(self) -> List[Value]:
        """获取所有Value"""
        result = []
        current = self.head
        while current:
            result.append(current.value)
            current = current.next
        return result
    
    def get_values_sorted_by_begin_index(self) -> List[Value]:
        """按起始索引排序获取所有Value"""
        return sorted(self.get_all_values(), key=lambda v: v.get_decimal_begin_index())
    
    def get_balance_by_state(self, state: ValueState = ValueState.UNSPENT) -> int:
        """计算指定状态的总余额"""
        values = self.find_by_state(state)
        return sum(v.value_num for v in values)
    
    def get_total_balance(self) -> int:
        """计算总余额"""
        return sum(v.value_num for v in self.get_all_values())
    
    def clear_spent_values(self):
        """清除已确认的Value"""
        spent_node_ids = list(self._state_index[ValueState.CONFIRMED])
        for node_id in spent_node_ids:
            self.remove_value(node_id)
    
    def validate_no_overlap(self) -> bool:
        """验证所有Value之间没有重叠"""
        values = self.get_values_sorted_by_begin_index()
        for i in range(len(values) - 1):
            if values[i].get_decimal_end_index() >= values[i + 1].get_decimal_begin_index():
                return False
        return True
    
    def __len__(self) -> int:
        return self.size
    
    def __iter__(self):
        current = self.head
        while current:
            yield current.value
            current = current.next
    
    def __contains__(self, value: Value) -> bool:
        current = self.head
        while current:
            if current.value.is_same_value(value):
                return True
            current = current.next
        return False