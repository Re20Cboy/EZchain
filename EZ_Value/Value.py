import re


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
        self.beginIndex = beginIndex
        self.valueNum = valueNum
        self.endIndex = self.get_end_index(beginIndex, valueNum)

    def print_value(self):
        print('value #begin:' + str(self.beginIndex))
        print('value #end:' + str(self.endIndex))
        print('value num:' + str(self.valueNum))

    def get_decimal_beginIndex(self):
        return int(self.beginIndex, 16)

    def get_decimal_endIndex(self):
        return int(self.endIndex, 16)

    def split_value(self, change):  # 对此值进行分割
        V1 = Value(self.beginIndex, self.valueNum - change)
        tmpIndex = hex(V1.get_decimal_endIndex() + 1)
        V2 = Value(tmpIndex, change)
        return V1, V2  # V2是找零

    def get_end_index(self, beginIndex, valueNum):
        decimal_number = int(beginIndex, 16)
        result = decimal_number + valueNum - 1
        return hex(result)

    def _is_valid_hex(self, hex_string):
        return re.match(r"^0x[0-9A-Fa-f]+$", hex_string) is not None
        
    def check_value(self):  # 检测Value的合法性
        if self.valueNum <= 0 or not self._is_valid_hex(self.beginIndex) or not self._is_valid_hex(self.endIndex):
            return False
        return self.endIndex == self.get_end_index(self.beginIndex, self.valueNum)

    def get_intersect_value(self, target):  # target是Value类型, 获取和target有交集的值的部分
        decimal_begin = self.get_decimal_beginIndex()
        decimal_end = self.get_decimal_endIndex()
        decimal_target_begin = int(target.beginIndex, 16)
        decimal_target_end = int(target.endIndex, 16)
        
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
        decimal_begin = self.get_decimal_beginIndex()
        decimal_end = self.get_decimal_endIndex()
        decimal_target_begin = int(target.beginIndex, 16)
        decimal_target_end = int(target.endIndex, 16)
        return decimal_end >= decimal_target_begin and decimal_target_end >= decimal_begin

    def is_in_value(self, target):  # target是Value类型, 判断target是否在本value内
        decimal_begin = self.get_decimal_beginIndex()
        decimal_end = self.get_decimal_endIndex()
        decimal_target_begin = int(target.beginIndex, 16)
        decimal_target_end = int(target.endIndex, 16)
        return decimal_target_begin >= decimal_begin and decimal_target_end <= decimal_end

    def is_same_value(self, target):  # target是Value类型, 判断target是否就是本value
        if not isinstance(target, Value):
            print('ERR: func isSameValue get illegal input!')
            return False
        return target.beginIndex == self.beginIndex and target.endIndex == self.endIndex and target.valueNum == self.valueNum