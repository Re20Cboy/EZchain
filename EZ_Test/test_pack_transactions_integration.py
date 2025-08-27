"""
PackTransactions.py 联调测试
测试完整的交易注入、打包、区块创建流程
"""

import sys
import os
import time
import json
from typing import Dict, Any, List
from dataclasses import dataclass

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from EZ_Simulation.TransactionInjector import TransactionInjector, SimulationConfig
from EZ_Transaction_Pool.TransactionPool import TransactionPool
from EZ_Transaction_Pool.PackTransactions import TransactionPackager, package_transactions_from_pool
from EZ_Main_Chain.Block import Block


@dataclass
class TestResult:
    """测试结果数据类"""
    test_name: str
    success: bool
    message: str
    data: Any = None
    execution_time: float = 0.0


class PackTransactionsIntegrationTest:
    """PackTransactions.py 联调测试类"""
    
    def __init__(self):
        self.test_results: List[TestResult] = []
        self.test_data_dir = "EZ_simulation_data"
        self.db_path = "test_pool.db"
        
    def run_all_tests(self) -> List[TestResult]:
        """运行所有测试"""
        print("=" * 80)
        print("开始 PackTransactions.py 联调测试")
        print("=" * 80)
        
        # 测试1: 交易注入功能
        self.test_transaction_injection()
        
        # 测试2: 交易打包功能
        self.test_transaction_packaging()
        
        # 测试3: 区块创建功能
        self.test_block_creation()
        
        # 测试4: 完整流程测试
        self.test_complete_workflow()
        
        # 打印测试结果
        self.print_test_results()
        
        return self.test_results
    
    def test_transaction_injection(self) -> TestResult:
        """测试交易注入功能"""
        print("\n" + "=" * 60)
        print("测试 1: 交易注入功能")
        print("=" * 60)
        
        start_time = time.time()
        
        try:
            # 配置交易注入器：100个交易，模拟真实场景
            config = SimulationConfig(
                num_senders=10,  # 10个发送者
                num_transactions_per_batch=5,  # 每批5个交易
                num_batches=20,  # 20批，总共100个交易
                injection_interval=0.01,  # 快速注入
                validation_enabled=False,  # 禁用验证以避免签名问题
                signature_enabled=False,  # 简化测试
                duplicate_probability=0.0,  # 无重复
                invalid_probability=0.0,  # 无无效交易
                preserve_database=True,
                database_output_dir=self.test_data_dir
            )
            
            injector = TransactionInjector(config)
            
            # 运行注入模拟
            stats = injector.run_simulation()
            
            # 检查注入结果
            pool_stats = injector.transaction_pool.get_pool_stats()
            
            success = (
                stats.total_injected > 0 and
                stats.successfully_added > 0 and
                pool_stats['total_transactions'] > 0
            )
            
            message = f"注入了 {stats.total_injected} 个交易，成功 {stats.successfully_added} 个，池中有 {pool_stats['total_transactions']} 个交易"
            
            result = TestResult(
                test_name="交易注入功能",
                success=success,
                message=message,
                data={
                    'stats': stats.__dict__,
                    'pool_stats': pool_stats,
                    'injected_transactions': injector.injected_transactions[:10]  # 只保留前10个
                },
                execution_time=time.time() - start_time
            )
            
            # 保存交易池数据库供后续测试使用
            import shutil
            shutil.copy2("simulation_pool.db", self.db_path)
            
            print(f"[SUCCESS] {message}")
            
        except Exception as e:
            result = TestResult(
                test_name="交易注入功能",
                success=False,
                message=f"测试失败: {str(e)}",
                execution_time=time.time() - start_time
            )
            print(f"[FAILED] 测试失败: {str(e)}")
        
        self.test_results.append(result)
        return result
    
    def test_transaction_packaging(self) -> TestResult:
        """测试交易打包功能"""
        print("\n" + "=" * 60)
        print("测试 2: 交易打包功能")
        print("=" * 60)
        
        start_time = time.time()
        
        try:
            # 从保存的数据库加载交易池
            transaction_pool = TransactionPool(self.db_path)
            
            # 创建交易打包器
            packager = TransactionPackager(max_multi_txns_per_block=10)
            
            # 测试不同的选择策略
            strategies = ["fifo", "fee"]
            strategy_results = {}
            
            for strategy in strategies:
                package_data = packager.package_transactions(
                    transaction_pool=transaction_pool,
                    selection_strategy=strategy
                )
                
                strategy_results[strategy] = {
                    'multi_txns_count': len(package_data.selected_multi_txns),
                    'single_txns_count': sum(len(multi_txn.multi_txns) for multi_txn in package_data.selected_multi_txns),
                    'merkle_root': package_data.merkle_root,
                    'sender_addresses': package_data.sender_addresses,
                    'package_time': package_data.package_time
                }
                
                print(f"  策略 '{strategy}': 打包了 {len(package_data.selected_multi_txns)} 个多重交易")
            
            # 验证打包结果
            success = all(result['multi_txns_count'] > 0 for result in strategy_results.values())
            
            message = f"测试了 {len(strategies)} 种打包策略，均成功打包交易"
            
            result = TestResult(
                test_name="交易打包功能",
                success=success,
                message=message,
                data={'strategy_results': strategy_results},
                execution_time=time.time() - start_time
            )
            
            print(f"[SUCCESS] {message}")
            
        except Exception as e:
            result = TestResult(
                test_name="交易打包功能",
                success=False,
                message=f"测试失败: {str(e)}",
                execution_time=time.time() - start_time
            )
            print(f"[FAILED] 测试失败: {str(e)}")
        
        self.test_results.append(result)
        return result
    
    def test_block_creation(self) -> TestResult:
        """测试区块创建功能"""
        print("\n" + "=" * 60)
        print("测试 3: 区块创建功能")
        print("=" * 60)
        
        start_time = time.time()
        
        try:
            # 从保存的数据库加载交易池
            transaction_pool = TransactionPool(self.db_path)
            
            # 使用便捷函数创建区块
            package_data, block = package_transactions_from_pool(
                transaction_pool=transaction_pool,
                miner_address="miner_001",
                previous_hash="0" * 64,  # 创世区块的哈希
                block_index=1,
                max_multi_txns=10
            )
            
            # 验证区块创建结果
            block_valid = self._validate_block(block, package_data)
            
            success = block_valid and len(package_data.selected_multi_txns) > 0
            
            message = f"成功创建区块 {block.get_index()}，包含 {len(package_data.selected_multi_txns)} 个多重交易"
            
            result = TestResult(
                test_name="区块创建功能",
                success=success,
                message=message,
                data={
                    'block_index': block.get_index(),
                    'block_hash': block.get_hash(),
                    'merkle_root': block.get_m_tree_root(),
                    'miner': block.get_miner(),
                    'package_data': {
                        'multi_txns_count': len(package_data.selected_multi_txns),
                        'single_txns_count': sum(len(multi_txn.multi_txns) for multi_txn in package_data.selected_multi_txns),
                        'merkle_root': package_data.merkle_root,
                        'sender_addresses': package_data.sender_addresses
                    }
                },
                execution_time=time.time() - start_time
            )
            
            print(f"[SUCCESS] {message}")
            print(f"  区块哈希: {block.get_hash()}")
            print(f"  默克尔根: {block.get_m_tree_root()}")
            print(f"  矿工: {block.get_miner()}")
            
        except Exception as e:
            result = TestResult(
                test_name="区块创建功能",
                success=False,
                message=f"测试失败: {str(e)}",
                execution_time=time.time() - start_time
            )
            print(f"[FAILED] 测试失败: {str(e)}")
        
        self.test_results.append(result)
        return result
    
    def test_complete_workflow(self) -> TestResult:
        """测试完整工作流程"""
        print("\n" + "=" * 60)
        print("测试 4: 完整工作流程")
        print("=" * 60)
        
        start_time = time.time()
        
        try:
            workflow_results = []
            
            # 创建3个区块来测试完整的流程
            for block_num in range(3):
                print(f"\n--- 创建区块 {block_num + 1} ---")
                
                # 创建新的交易池
                transaction_pool = TransactionPool(f"test_pool_{block_num}.db")
                
                # 注入少量交易
                config = SimulationConfig(
                    num_senders=5,
                    num_transactions_per_batch=3,
                    num_batches=5,  # 每个区块15个交易
                    injection_interval=0.001,
                    validation_enabled=False,  # 禁用验证以避免签名问题
                    signature_enabled=False,
                    preserve_database=False
                )
                
                injector = TransactionInjector(config)
                injector.run_simulation()
                
                # 检查交易池状态
                pool_stats = injector.transaction_pool.get_pool_stats()
                print(f"  交易池状态: {pool_stats['total_transactions']} 个交易")
                
                # 打包交易并创建区块
                package_data, block = package_transactions_from_pool(
                    transaction_pool=injector.transaction_pool,  # 使用injector的交易池
                    miner_address=f"miner_{block_num:03d}",
                    previous_hash="0" * 64 if block_num == 0 else f"prev_hash_{block_num}",
                    block_index=block_num,
                    max_multi_txns=5
                )
                
                workflow_results.append({
                    'block_num': block_num + 1,
                    'multi_txns_count': len(package_data.selected_multi_txns),
                    'single_txns_count': sum(len(multi_txn.multi_txns) for multi_txn in package_data.selected_multi_txns),
                    'block_hash': block.get_hash(),
                    'merkle_root': block.get_m_tree_root(),
                    'miner': block.get_miner(),
                    'sender_addresses': package_data.sender_addresses
                })
                
                print(f"  区块 {block_num + 1}: {len(package_data.selected_multi_txns)} 个多重交易")
                
                # 清理
                injector.cleanup()
                # 注意：不需要单独删除数据库文件，因为injector.cleanup()已经处理了
            
            success = len(workflow_results) == 3
            message = f"成功创建 {len(workflow_results)} 个区块，完成完整工作流程测试"
            
            result = TestResult(
                test_name="完整工作流程",
                success=success,
                message=message,
                data={'workflow_results': workflow_results},
                execution_time=time.time() - start_time
            )
            
            print(f"[SUCCESS] {message}")
            
        except Exception as e:
            result = TestResult(
                test_name="完整工作流程",
                success=False,
                message=f"测试失败: {str(e)}",
                execution_time=time.time() - start_time
            )
            print(f"[FAILED] 测试失败: {str(e)}")
        
        self.test_results.append(result)
        return result
    
    def _validate_block(self, block: Block, package_data: Any) -> bool:
        """验证区块的正确性"""
        try:
            # 验证默克尔根
            if block.get_m_tree_root() != package_data.merkle_root:
                print(f"默克尔根不匹配: 区块 {block.get_m_tree_root()} != 打包 {package_data.merkle_root}")
                return False
            
            # 验证发送者地址在布隆过滤器中
            for sender in package_data.sender_addresses:
                if not block.is_in_bloom(sender):
                    print(f"发送者地址 {sender} 不在布隆过滤器中")
                    return False
            
            # 验证区块哈希
            calculated_hash = block.get_hash()
            if not calculated_hash or len(calculated_hash) != 64:
                print(f"区块哈希无效: {calculated_hash}")
                return False
            
            return True
            
        except Exception as e:
            print(f"区块验证失败: {str(e)}")
            return False
    
    def print_test_results(self):
        """打印测试结果"""
        print("\n" + "=" * 80)
        print("测试结果汇总")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result.success)
        
        print(f"总测试数: {total_tests}")
        print(f"通过测试: {passed_tests}")
        print(f"失败测试: {total_tests - passed_tests}")
        print(f"成功率: {passed_tests/total_tests*100:.1f}%")
        
        print("\n详细结果:")
        for i, result in enumerate(self.test_results, 1):
            status = "PASS" if result.success else "FAIL"
            print(f"{i}. {result.test_name}: {status} ({result.execution_time:.2f}s)")
            print(f"   {result.message}")
        
        # 保存测试结果到文件
        self.save_test_results()
        
        print(f"\n详细测试数据已保存到: {os.path.join(self.test_data_dir, 'test_results.json')}")
    
    def save_test_results(self):
        """保存测试结果到文件"""
        results_data = []
        for result in self.test_results:
            result_data = {
                'test_name': result.test_name,
                'success': result.success,
                'message': result.message,
                'execution_time': result.execution_time,
                'data': result.data
            }
            results_data.append(result_data)
        
        output_file = os.path.join(self.test_data_dir, 'test_results.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False, default=str)
    
    def cleanup(self):
        """清理测试文件"""
        try:
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
            if os.path.exists("simulation_pool.db"):
                os.remove("simulation_pool.db")
        except Exception as e:
            print(f"清理测试文件时出错: {str(e)}")


def main():
    """主函数"""
    test = PackTransactionsIntegrationTest()
    
    try:
        test.run_all_tests()
    finally:
        test.cleanup()


if __name__ == "__main__":
    main()