import re


class Value:  # 针对VCB区块链的专门设计的值结构，总量2^259 = 16^65
    def __init__(self, beginIndex, valueNum):  # beginIndex是16进制str，valueNum是10进制int
        # 值的开始和结束index都包含在值内
        self.beginIndex = beginIndex
        self.valueNum = valueNum
        self.endIndex = self.getEndIndex(beginIndex, valueNum)

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

    def check_value(self):  # 检测Value的合法性
        def is_hexadecimal(string):
            pattern = r"^0x[0-9A-Fa-f]+$"
            return re.match(pattern, string) != None

        if self.valueNum <= 0:
            return False
        if not is_hexadecimal(self.beginIndex):
            return False
        if not is_hexadecimal(self.endIndex):
            return False
        if self.endIndex != self.getEndIndex(self.beginIndex, self.valueNum):
            return False
        return True

    def get_intersect_value(self, target):  # target是Value类型, 获取和target有交集的值的部分
        decimal_targetBegin = int(target.beginIndex, 16)
        decimal_targetEnd = int(target.endIndex, 16)
        decimal_beginIndex = self.get_decimal_beginIndex()
        decimal_endIndex = self.get_decimal_endIndex()
        IntersectBegin = max(decimal_targetBegin, decimal_beginIndex)
        IntersectEnd = min(decimal_targetEnd, decimal_endIndex)
        if IntersectBegin <= IntersectEnd:
            IntersectValueNum = IntersectEnd - IntersectBegin + 1
            tmp1 = IntersectBegin - decimal_beginIndex
            tmp2 = decimal_endIndex - IntersectEnd
            IntersectValue = Value(hex(IntersectBegin), IntersectValueNum)
            RestValues = []
            if tmp1 != 0:
                if tmp2 != 0:
                    tmpV1 = Value(hex(decimal_beginIndex), tmp1)
                    tmpV2 = Value(hex(IntersectEnd + 1), tmp2)
                    RestValues.append(tmpV1)
                    RestValues.append(tmpV2)
                else:  # tmp1 != 0; tmp2 = 0
                    tmpV1 = Value(hex(decimal_beginIndex), tmp1)
                    RestValues.append(tmpV1)
            else:  # tmp1 = 0
                if tmp2 != 0:
                    tmpV2 = Value(hex(IntersectEnd + 1), tmp2)
                    RestValues.append(tmpV2)
                else:  # tmp1 = 0; tmp2 = 0
                    pass
            return (IntersectValue, RestValues)
        else:
            return None

    def is_intersect_value(self, target):  # target是Value类型, 判断target是否和本value有交集
        decimal_targetBegin = int(target.beginIndex, 16)
        decimal_targetEnd = int(target.endIndex, 16)
        decimal_beginIndex = self.get_decimal_beginIndex()
        decimal_endIndex = self.get_decimal_endIndex()
        if decimal_endIndex >= decimal_targetBegin:
            if decimal_targetEnd >= decimal_beginIndex:
                return True
        return False
        # return ((decimal_endIndex >= decimal_targetBegin) and (decimal_targetEnd >= decimal_beginIndex))

    def is_in_value(self, target):  # target是Value类型, 判断target是否在本value内
        decimal_targetBegin = int(target.beginIndex, 16)
        decimal_targetEnd = int(target.endIndex, 16)
        decimal_beginIndex = self.get_decimal_beginIndex()
        decimal_endIndex = self.get_decimal_endIndex()
        return decimal_targetBegin >= decimal_beginIndex and decimal_targetEnd <= decimal_endIndex

    def is_same_value(self, target):  # target是Value类型, 判断target是否就是本value
        if type(target) != Value:
            print('ERR: func isSameValue get illegal input!')
            return False
        if target.beginIndex == self.beginIndex and target.endIndex == self.endIndex and target.valueNum == self.valueNum:
            return True
        else:
            return False