import re

#TODO：值的状态：未花销、本地提交待确认、链上已确认（=已花费）

class Value:  # 针对VCB区块链的专门设计的值结构，总量2^259 = 16^65
    def __init__(self, beginIndex, valueNum):  # beginIndex是16进制str，valueNum是10进制int
        # 输入参数验证
        if not isinstance(beginIndex, str):
            raise TypeError("beginIndex must be a string")
        if not isinstance(valueNum, int):
            raise TypeError("valueNum must be an integer")
        
        if valueNum <= 0:
            raise ValueError("valueNum must be positive")
        
        if not self._is_valid_hex(beginIndex):
            raise ValueError("beginIndex must be a valid hexadecimal string starting with '0x'")
        
        # 值的开始和结束index都包含在值内
        self.begin_index = beginIndex
        self.value_num = valueNum
        self.end_index = self.get_end_index(beginIndex, valueNum)

    def print_value(self):
        print('value #begin:' + str(self.begin_index))
        print('value #end:' + str(self.end_index))
        print('value num:' + str(self.value_num))

    def get_decimal_begin_index(self):
        return int(self.begin_index, 16)

    def get_decimal_end_index(self):
        return int(self.end_index, 16)

    def split_value(self, change):  # 对此值进行分割
        # 边缘值检测
        if change <= 0 or change >= self.value_num:
            raise ValueError("Invalid change value")
        V1 = Value(self.begin_index, self.value_num - change)
        tmpIndex = hex(V1.get_decimal_end_index() + 1)
        V2 = Value(tmpIndex, change)
        return V1, V2  # V2是找零

    def get_end_index(self, begin_index, value_num):
        decimal_number = int(begin_index, 16)
        result = decimal_number + value_num - 1
        return hex(result)

    def _is_valid_hex(self, hex_string):
        return re.match(r"^0x[0-9A-Fa-f]+$", hex_string) is not None
        
    def check_value(self):  # 检测Value的合法性
        if self.value_num <= 0 or not self._is_valid_hex(self.begin_index) or not self._is_valid_hex(self.end_index):
            return False
        return self.end_index == self.get_end_index(self.begin_index, self.value_num)

    def get_intersect_value(self, target):  # target是Value类型, 获取和target有交集的值的部分
        decimal_begin = self.get_decimal_begin_index()
        decimal_end = self.get_decimal_end_index()
        decimal_target_begin = int(target.begin_index, 16)
        decimal_target_end = int(target.end_index, 16)
        
        intersect_begin = max(decimal_target_begin, decimal_begin)
        intersect_end = min(decimal_target_end, decimal_end)
        
        if intersect_begin > intersect_end:
            return None
            
        intersect_value = Value(hex(intersect_begin), intersect_end - intersect_begin + 1)
        
        rest_values = []
        if decimal_begin < intersect_begin:
            rest_values.append(Value(hex(decimal_begin), intersect_begin - decimal_begin))
        if intersect_end < decimal_end:
            rest_values.append(Value(hex(intersect_end + 1), decimal_end - intersect_end))
            
        return (intersect_value, rest_values)

    def is_intersect_value(self, target):  # target是Value类型, 判断target是否和本value有交集
        decimal_begin = self.get_decimal_begin_index()
        decimal_end = self.get_decimal_end_index()
        decimal_target_begin = int(target.begin_index, 16)
        decimal_target_end = int(target.end_index, 16)
        return decimal_end >= decimal_target_begin and decimal_target_end >= decimal_begin

    def is_in_value(self, target):  # target是Value类型, 判断target是否在本value内
        decimal_begin = self.get_decimal_begin_index()
        decimal_end = self.get_decimal_end_index()
        decimal_target_begin = int(target.begin_index, 16)
        decimal_target_end = int(target.end_index, 16)
        return decimal_target_begin >= decimal_begin and decimal_target_end <= decimal_end

    def is_same_value(self, target):  # target是Value类型, 判断target是否就是本value
        if not isinstance(target, Value):
            print('ERR: func isSameValue get illegal input!')
            return False
        return target.begin_index == self.begin_index and target.end_index == self.end_index and target.value_num == self.value_num