# 集成测试说明

## 概述

这个目录包含了两种类型的测试：

1. **单元测试** (`test_unit_creat_single_transaction.py`) - 使用mock隔离测试单个模块
2. **集成测试** (`test_integration_creat_single_transaction.py`) - 真实调用模块间交互测试

## 测试策略

### 单元测试 (Unit Tests)
- **目的**: 测试 `CreateTransaction` 类的内部逻辑
- **方法**: 使用 `unittest.mock.patch` 隔离外部依赖
- **优点**: 快速、稳定、可重复
- **适用场景**: 验证单个模块的正确性

### 集成测试 (Integration Tests)
- **目的**: 验证模块间的真实交互和数据流
- **方法**: 真实调用所有依赖模块，不使用mock
- **优点**: 验证完整的业务逻辑和数据状态
- **适用场景**: 验证模块协作和端到端流程

## 运行测试

### 运行所有测试
```bash
cd D:\real_EZchain\EZ_Test
python -m pytest
```

### 只运行单元测试
```bash
python -m pytest test_unit_creat_single_transaction.py -v
```

### 只运行集成测试
```bash
python -m pytest test_integration_creat_single_transaction.py -v
```

### 运行特定测试
```bash
# 单个测试
python -m pytest test_integration_creat_single_transaction.py::TestIntegrationCreateTransaction::test_real_value_state_management -v -s

# 带调试输出
python -m pytest test_integration_creat_single_transaction.py::TestIntegrationCreateTransaction::test_real_value_state_management -v -s -k "value_state"
```

## 集成测试覆盖的功能

### 1. Value状态管理测试
- Value的添加和状态转换
- 账户余额跟踪
- 账户完整性验证

### 2. 交易创建测试
- 无找零交易创建
- 有找零交易创建
- 边界条件测试

### 3. 交易流程测试
- 多笔交易工作流
- 交易确认流程
- 已确认Value的清理

### 4. 异常处理测试
- 余额不足处理
- 无效输入处理

## 测试数据说明

### Value对象
- `beginIndex`: 16进制字符串，如 "0x1000"
- `valueNum`: 10进制整数，表示金额
- `state`: Value状态枚举 (UNSPENT, SELECTED, LOCAL_COMMITTED, CONFIRMED)

### 交易对象
- `sender`: 发送方地址
- `recipient`: 接收方地址
- `nonce`: 交易序号
- `signature`: 交易签名
- `value`: 交易包含的Value列表
- `time`: 交易时间戳

## 测试环境要求

- Python 3.11+
- pytest 8.0+
- cryptography 库
- 所有EZchain模块 (EZ_Transaction, EZ_Value, EZ_Tool_Box)

## 测试结果分析

### 通过的测试
- ✅ Value状态管理
- ✅ 交易创建 (无找零/有找零)
- ✅ 余额不足处理
- ✅ 多笔交易工作流
- ✅ 交易确认流程
- ✅ 账户余额跟踪
- ✅ 边界条件测试
- ✅ Value分裂逻辑

### 警告信息
- 关于私钥加载的安全警告是正常的，测试环境中的预期行为

## 开发建议

1. **新功能开发**: 先写单元测试，确保模块逻辑正确
2. **集成测试**: 在功能开发完成后，运行集成测试验证模块协作
3. **回归测试**: 修改代码后，同时运行两种测试确保没有破坏现有功能
4. **调试**: 使用 `-s` 参数启用调试输出，观察详细执行过程

## 扩展测试

如需添加新的集成测试：

1. 在 `TestIntegrationCreateTransaction` 类中添加新方法
2. 使用真实的 `AccountPickValues` 和 `Value` 对象
3. 调用 `CreateTransaction` 的真实方法
4. 验证结果和状态变化

示例：
```python
def test_new_integration_scenario(self, create_transaction, test_recipient, private_key_pem):
    # 添加测试数据
    value_selector = create_transaction.value_selector
    value_selector.add_values_from_list([Value("0x1000", 1000)])
    
    # 真实调用
    result = create_transaction.create_transaction(
        recipient=test_recipient,
        amount=500,
        private_key_pem=private_key_pem
    )
    
    # 验证结果
    assert result["total_amount"] == 500
```