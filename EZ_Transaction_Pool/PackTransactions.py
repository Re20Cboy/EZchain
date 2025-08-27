"""
交易打包模块
从交易池中提取交易，打包形成区块所需数据结构
根据Block.py的设计，区块包含：
- m_tree_root: 由交易池中MultiTransactions的digest构成默克尔树的根
- bloom: 将交易池中所有MultiTransactions的Sender添加进去的布隆过滤器
"""

import copy
import sys
import os
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from EZ_Transaction_Pool.TransactionPool import TransactionPool
from EZ_Transaction.MultiTransactions import MultiTransactions
from EZ_Transaction.SingleTransaction import Transaction
from EZ_Main_Chain.Block import Block
from EZ_Block_Units.MerkleTree import MerkleTree
from EZ_Tool_Box.Hash import sha256_hash


@dataclass
class PackagedBlockData:
    """打包好的区块数据结构，专为Block.py设计"""
    selected_multi_txns: List[MultiTransactions]  # 选中的多重交易列表
    merkle_root: str  # 默克尔根（由MultiTransactions的digest构成）
    sender_addresses: List[str]  # 发送者地址列表（用于布隆过滤器）
    package_time: datetime.datetime  # 打包时间
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'multi_transactions_digests': [txn.digest for txn in self.selected_multi_txns],
            'merkle_root': self.merkle_root,
            'sender_addresses': self.sender_addresses,
            'package_time': self.package_time.isoformat()
        }


class TransactionPackager:
    """交易打包器，专为Block.py设计"""
    
    def __init__(self, max_multi_txns_per_block: int = 100):
        """
        初始化交易打包器
        
        Args:
            max_multi_txns_per_block: 每个区块最大多重交易数量
        """
        self.max_multi_txns_per_block = max_multi_txns_per_block
    
    def package_transactions(self, transaction_pool: TransactionPool, 
                           selection_strategy: str = "fifo") -> PackagedBlockData:
        """
        从交易池中打包交易形成区块数据
        
        Args:
            transaction_pool: 交易池对象
            selection_strategy: 交易选择策略 ("fifo": 先进先出, "fee": 按手续费排序)
            
        Returns:
            PackagedBlockData: 打包好的区块数据
        """
        try:
            # 从交易池获取所有待打包交易
            all_multi_txns = transaction_pool.get_all_multi_transactions()
            
            if not all_multi_txns:
                return PackagedBlockData(
                    selected_multi_txns=[],
                    merkle_root="",
                    sender_addresses=[],
                    package_time=datetime.datetime.now()
                )
            
            # 根据策略选择交易
            selected_multi_txns = self._select_transactions(all_multi_txns, selection_strategy)
            
            # 限制交易数量
            selected_multi_txns = selected_multi_txns[:self.max_multi_txns_per_block]
            
            # 提取发送者地址（用于布隆过滤器）
            sender_addresses = self._extract_sender_addresses(selected_multi_txns)
            
            # 构建默克尔树（使用MultiTransactions的digest）
            merkle_root = self._build_merkle_tree(selected_multi_txns)
            
            return PackagedBlockData(
                selected_multi_txns=selected_multi_txns,
                merkle_root=merkle_root,
                sender_addresses=sender_addresses,
                package_time=datetime.datetime.now()
            )
            
        except Exception as e:
            raise Exception(f"Error packaging transactions: {str(e)}")
    
    def _select_transactions(self, multi_txns: List[MultiTransactions], strategy: str) -> List[MultiTransactions]:
        """
        根据策略选择交易
        
        Args:
            multi_txns: 多重交易列表
            strategy: 选择策略
            
        Returns:
            选择后的多重交易列表
        """
        if strategy == "fifo":
            # 先进先出策略
            return multi_txns
        elif strategy == "fee":
            # 按手续费排序（这里简单按交易数量作为手续费代理）
            return sorted(multi_txns, key=lambda x: len(x.multi_txns), reverse=True)
        else:
            # 默认先进先出
            return multi_txns
    
    def _extract_sender_addresses(self, multi_txns: List[MultiTransactions]) -> List[str]:
        """
        提取发送者地址（用于布隆过滤器）
        
        Args:
            multi_txns: 多重交易列表
            
        Returns:
            发送者地址列表
        """
        senders = set()
        for multi_txn in multi_txns:
            if multi_txn.sender:
                senders.add(multi_txn.sender)
        return list(senders)
    
    def _build_merkle_tree(self, multi_txns: List[MultiTransactions]) -> str:
        """
        构建默克尔树并返回根哈希
        使用MultiTransactions的digest作为叶子节点
        
        Args:
            multi_txns: 多重交易列表
            
        Returns:
            默克尔根哈希
        """
        if not multi_txns:
            return ""
        
        # 使用多重交易的digest作为默克尔树的叶子节点
        leaf_hashes = []
        for multi_txn in multi_txns:
            if multi_txn.digest:
                leaf_hashes.append(multi_txn.digest)
            else:
                # 如果没有digest，使用编码后的数据哈希
                leaf_hashes.append(sha256_hash(multi_txn.encode()))
        
        # 构建默克尔树
        merkle_tree = MerkleTree(leaf_hashes)
        return merkle_tree.get_root_hash()
    
    def create_block_from_package(self, package_data: PackagedBlockData, 
                                 miner_address: str, 
                                 previous_hash: str,
                                 block_index: int) -> Block:
        """
        从打包数据创建区块
        
        Args:
            package_data: 打包的区块数据
            miner_address: 矿工地址
            previous_hash: 前一个区块的哈希
            block_index: 区块索引
            
        Returns:
            Block: 创建的区块对象
        """
        # 创建区块
        block = Block(
            index=block_index,
            m_tree_root=package_data.merkle_root,
            miner=miner_address,
            pre_hash=previous_hash,
            time=package_data.package_time
        )
        
        # 将所有MultiTransactions的Sender添加到布隆过滤器
        for sender in package_data.sender_addresses:
            block.add_item_to_bloom(sender)
        
        return block
    
    def remove_packaged_transactions(self, transaction_pool: TransactionPool, 
                                  packaged_txns: List[MultiTransactions]) -> int:
        """
        从交易池中移除已打包的交易
        
        Args:
            transaction_pool: 交易池对象
            packaged_txns: 已打包的多重交易列表
            
        Returns:
            成功移除的交易数量
        """
        removed_count = 0
        
        for multi_txn in packaged_txns:
            if multi_txn.digest:
                success = transaction_pool.remove_multi_transactions(multi_txn.digest)
                if success:
                    removed_count += 1
        
        return removed_count
    
    def get_package_stats(self, package_data: PackagedBlockData) -> Dict[str, Any]:
        """
        获取打包统计信息
        
        Args:
            package_data: 打包的区块数据
            
        Returns:
            统计信息字典
        """
        # 计算总的单独交易数量
        total_single_txns = sum(len(multi_txn.multi_txns) for multi_txn in package_data.selected_multi_txns)
        
        return {
            'total_multi_transactions': len(package_data.selected_multi_txns),
            'total_single_transactions': total_single_txns,
            'unique_senders': len(package_data.sender_addresses),
            'merkle_root': package_data.merkle_root,
            'package_time': package_data.package_time.isoformat(),
            'selected_multi_txns_digests': [txn.digest for txn in package_data.selected_multi_txns]
        }


# 便捷函数
def package_transactions_from_pool(transaction_pool: TransactionPool,
                                 miner_address: str,
                                 previous_hash: str,
                                 block_index: int,
                                 max_multi_txns: int = 100) -> Tuple[PackagedBlockData, Block]:
    """
    从交易池打包交易的便捷函数
    
    Args:
        transaction_pool: 交易池对象
        miner_address: 矿工地址
        previous_hash: 前一个区块的哈希
        block_index: 区块索引
        max_multi_txns: 最大多重交易数量
        
    Returns:
        (打包数据, 区块对象) 的元组
    """
    packager = TransactionPackager(max_multi_txns_per_block=max_multi_txns)
    
    # 打包交易
    package_data = packager.package_transactions(
        transaction_pool=transaction_pool
    )
    
    # 创建区块
    block = packager.create_block_from_package(
        package_data=package_data,
        miner_address=miner_address,
        previous_hash=previous_hash,
        block_index=block_index
    )
    
    # 从交易池移除已打包的交易
    removed_count = packager.remove_packaged_transactions(
        transaction_pool=transaction_pool,
        packaged_txns=package_data.selected_multi_txns
    )
    
    # 计算统计信息
    total_single_txns = sum(len(multi_txn.multi_txns) for multi_txn in package_data.selected_multi_txns)
    
    print(f"Successfully packaged {len(package_data.selected_multi_txns)} multi-transactions "
          f"({total_single_txns} single transactions) "
          f"and removed {removed_count} transactions from pool")
    print(f"Merkle root: {package_data.merkle_root}")
    print(f"Senders added to bloom filter: {package_data.sender_addresses}")
    
    return package_data, block

