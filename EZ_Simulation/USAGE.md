# 交易注入仿真系统 - 使用说明

## 概述

这个交易注入仿真系统专门为 EZChain 区块链项目设计，可以模拟交易提交至交易池的完整过程。

## 快速开始

### 1. 基本使用

```python
from EZ_Simulation.TransactionInjector import TransactionInjector, SimulationConfig

# 创建配置
config = SimulationConfig(
    num_senders=3,        # 发送方数量
    num_batches=5,        # 批次数量
    injection_interval=0.2 # 注入间隔（秒）
)

# 创建注入器并运行仿真
injector = TransactionInjector(config)
stats = injector.run_simulation()

# 清理资源
injector.cleanup()
```

### 2. 运行示例

```bash
# 基本仿真
python -c "from EZ_Simulation.run_simulation_examples import run_basic_simulation; run_basic_simulation()"

# 压力测试
python -c "from EZ_Simulation.run_simulation_examples import run_stress_test; run_stress_test()"

# 验证测试
python -c "from EZ_Simulation.run_simulation_examples import run_validation_test; run_validation_test()"
```

### 3. 运行测试

```bash
# 运行所有测试
python -m unittest EZ_Test.test_transaction_injector -v

# 运行特定测试
python -m unittest EZ_Test.test_transaction_injector.TestTransactionInjector.test_inject_single_transaction -v
```

## 配置参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `num_senders` | 发送方数量 | 5 |
| `num_transactions_per_batch` | 每批交易数量 | 10 |
| `num_batches` | 批次数量 | 20 |
| `injection_interval` | 注入间隔（秒） | 0.1 |
| `validation_enabled` | 是否启用验证 | True |
| `signature_enabled` | 是否启用签名 | True |
| `duplicate_probability` | 重复交易概率 | 0.05 |
| `invalid_probability` | 无效交易概率 | 0.02 |

## 注意事项

1. **签名验证**: 由于仿真环境限制，实际的签名验证被禁用，系统使用虚拟签名
2. **数据库**: 仿真会创建临时数据库文件，程序结束后会自动清理
3. **性能**: 大规模仿真可能需要调整参数以避免性能问题

## 文件结构

```
EZ_Simulation/
├── TransactionInjector.py      # 主要仿真代码
├── run_simulation_examples.py  # 示例脚本
└── README.md                  # 详细文档

EZ_Test/
└── test_transaction_injector.py # 测试代码
```

## 输出示例

```
Starting transaction injection simulation...
Configuration: SimulationConfig(num_senders=3, num_batches=5, ...)

--- Batch 1/5 ---
  Transaction 1: SUCCESS - MultiTransactions added successfully
  Current Stats: 1 injected, 1 successful, 0 failed validation, 0 duplicates

... (更多批次) ...

============================================================
SIMULATION RESULTS
============================================================
Total simulation time: 0.83 seconds
Total transactions injected: 5
Successfully added to pool: 5
Success rate: 100.00%
Injection rate: 6.03 tx/sec

Transaction Pool Status:
  Transactions in pool: 5
  Unique senders: 2
  Pool size: 3980 bytes
============================================================
```

## 故障排除

### 常见问题

1. **验证失败**: 确保 `validation_enabled=False` 用于基本测试
2. **导入错误**: 确保项目根目录在 Python 路径中
3. **数据库错误**: 确保有写入权限和磁盘空间

### 调试技巧

1. 使用较小的参数值进行测试
2. 检查日志输出了解详细错误信息
3. 运行单元测试确保组件正常工作

## 扩展功能

系统支持以下扩展：
- 自定义交易生成器
- 自定义验证逻辑
- 事件回调机制
- 性能监控和统计
