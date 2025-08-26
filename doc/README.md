# EZChain 测试指南

## 概述

本文档提供了 EZChain 项目中如何运行和编写测试的详细说明。项目使用 pytest 作为测试框架，提供了全面的单元测试覆盖。

## 测试结构

```
EZ_Test/
├── test_bloom.py              # Bloom过滤器测试
├── test_merkle_proof.py       # Merkle证明测试
├── test_merkle_tree.py        # Merkle树测试
├── test_multi_transactions.py  # 多交易测试
├── test_single_transaction.py # 单交易测试
└── test_value.py              # Value类测试
```

## 测试框架

### 依赖项

所有测试依赖项都在 `requirements.txt` 中定义，包括：
- pytest>=7.0.0 - 测试框架
- 其他项目依赖项

### 运行测试

#### 1. 安装依赖

```bash
pip install -r requirements.txt
```

#### 2. 运行所有测试

```bash
python -m pytest EZ_Test/ -v
```

#### 3. 运行特定测试文件

```bash
python -m pytest EZ_Test/test_bloom.py -v
python -m pytest EZ_Test/test_merkle_tree.py -v
```

#### 4. 运行特定测试类

```bash
python -m pytest EZ_Test/test_value.py::TestValueInitialization -v
```

#### 5. 运行特定测试方法

```bash
python -m pytest EZ_Test/test_value.py::TestValueInitialization::test_valid_initialization -v
```

#### 6. 生成测试覆盖率报告

```bash
pip install pytest-cov
python -m pytest EZ_Test/ --cov=EZ_Block_Units --cov-report=html
```

#### 7. 运行测试并显示详细信息

```bash
python -m pytest EZ_Test/ -v --tb=short
```

## 测试架构

### 测试类组织

每个测试文件都包含多个测试类，按功能模块组织：

- **基础功能测试** (`Test*Basic`, `Test*Initialization`)
- **高级功能测试** (`Test*Advanced`, `Test*Integration`)  
- **边界情况测试** (`Test*EdgeCases`)
- **错误处理测试** (`Test*ErrorHandling`)

### Fixtures 使用

测试使用 pytest fixtures 来提供共享的测试数据：

```python
@pytest.fixture
def value_test_data():
    """Fixture for value test data."""
    valid_begin = "0x1000"
    valid_num = 100
    return valid_begin, valid_num, Value(valid_begin, valid_num)
```

### 测试模式

1. **类结构测试**：使用类组织相关测试方法
2. **参数化测试**：使用 `@pytest.mark.parametrize` 进行参数化测试
3. **Fixture共享**：使用fixtures提供可重用的测试数据
4. **断言丰富**：使用多种断言方法验证不同方面

## 各模块测试说明

### Bloom过滤器测试 (test_bloom.py)

测试Bloom过滤器的核心功能：
- 基本初始化和添加元素
- 压缩和解压缩功能
- 假阳性率测试
- JSON序列化
- 边界情况处理

**运行命令**：
```bash
python -m pytest EZ_Test/test_bloom.py -v
```

### Merkle树测试 (test_merkle_tree.py)

测试Merkle树的构建和验证：
- 节点初始化和哈希计算
- 树构建和根哈希生成
- 树验证算法
- 父子关系维护
- 各种数据大小和类型的处理

**运行命令**：
```bash
python -m pytest EZ_Test/test_merkle_tree.py -v
```

### Merkle证明测试 (test_merkle_proof.py)

测试Merkle证明的验证：
- 证明初始化
- 有效和无效证明验证
- 单项证明处理
- 大数据集证明
- Unicode数据处理

**运行命令**：
```bash
python -m pytest EZ_Test/test_merkle_proof.py -v
```

### 多交易测试 (test_multi_transactions.py)

测试多交易功能：
- 多交易初始化
- 编码和解码
- 签名和验证
- 时间戳处理
- 属性访问

**运行命令**：
```bash
python -m pytest EZ_Test/test_multi_transactions.py -v
```

### 单交易测试 (test_single_transaction.py)

测试单个交易功能：
- 交易创建和哈希计算
- 序列化和反序列化
- 签名和验证
- 值操作
- 输出方法

**运行命令**：
```bash
python -m pytest EZ_Test/test_single_transaction.py -v
```

### Value类测试 (test_value.py)

测试Value类的核心功能：
- 初始化和验证
- 十六进制转换
- 值分割
- 交集计算
- 状态管理
- 边界情况处理

**运行命令**：
```bash
python -m pytest EZ_Test/test_value.py -v
```

## 编写新测试

### 测试命名约定

- 测试文件：`test_*.py`
- 测试类：`Test*`
- 测试方法：`test_*`

### 测试模板

```python
import pytest
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from your_module import YourClass

@pytest.fixture
def test_data():
    """Fixture for test data."""
    return YourClass("test_value")

class TestYourClass:
    """Test suite for YourClass."""
    
    def test_initialization(self, test_data):
        """Test initialization."""
        assert test_data.value == "test_value"
    
    def test_functionality(self, test_data):
        """Test core functionality."""
        result = test_data.some_method()
        assert result is not None
    
    def test_error_handling(self):
        """Test error handling."""
        with pytest.raises(ValueError):
            YourClass("invalid_value")
```

### 最佳实践

1. **保持测试独立性**：每个测试应该独立运行
2. **使用fixtures**：避免重复代码
3. **描述性命名**：测试名称应该清楚描述测试内容
4. **测试覆盖**：覆盖正常、边界和错误情况
5. **保持简洁**：测试应该简洁明了

## 故障排除

### 常见问题

1. **导入错误**：确保Python路径正确设置
2. **依赖缺失**：安装所有requirements.txt中的依赖
3. **测试失败**：检查具体的错误信息和堆栈跟踪

### 调试测试

```bash
# 详细输出
python -m pytest EZ_Test/ -v --tb=long

# 只运行失败的测试
python -m pytest EZ_Test/ --lf

# 停在第一个失败
python -m pytest EZ_Test/ --x
```

## 持续集成

建议将测试集成到CI/CD流程中：

```yaml
# GitHub Actions示例
- name: Run tests
  run: |
    pip install -r requirements.txt
    python -m pytest EZ_Test/ --cov=.
```

## 测试统计

- 总测试数：158个
- 测试文件数：6个
- 测试通过率：100%

所有测试都能独立运行，提供全面的代码覆盖和功能验证。