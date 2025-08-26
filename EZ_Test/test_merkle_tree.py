#!/usr/bin/env python3
"""
Unit tests for Merkle Tree module.
"""

import pytest
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(__file__) + '/..')

try:
    from EZ_Block_Units.MerkleTree import MerkleTree, MerkleTreeNode
    from EZ_Tool_Box.Hash import sha256_hash
except ImportError as e:
    print(f"Error importing MerkleTree or sha256_hash: {e}")
    sys.exit(1)


@pytest.fixture
def merkle_node_data():
    """Fixture for merkle node tests."""
    content = "test_content"
    value = "test_hash_value"
    left_node = MerkleTreeNode(None, None, "left_hash", "left_content")
    right_node = MerkleTreeNode(None, None, "right_hash", "right_content")
    return content, value, left_node, right_node


class TestMerkleTreeNode:
    """Test suite for Merkle Tree Node implementation."""
        
    def test_node_initialization(self, merkle_node_data):
        """Test MerkleTreeNode initialization."""
        content, value, left_node, right_node = merkle_node_data
        node = MerkleTreeNode(left_node, right_node, value, content)

        assert node.left == left_node
        assert node.right == right_node
        assert node.value == value
        assert node.content == content
        assert node.path == []
        assert node.leaf_index is None
        assert node.father is None
        
    def test_node_with_leaf_index(self, merkle_node_data):
        """Test node initialization with leaf index."""
        content, value, left_node, right_node = merkle_node_data
        leaf_index = 5
        node = MerkleTreeNode(None, None, value, content, leaf_index=leaf_index)

        assert node.leaf_index == leaf_index
        
    def test_node_with_path(self, merkle_node_data):
        """Test node initialization with path."""
        content, value, left_node, right_node = merkle_node_data
        path = [1, 2, 3]
        node = MerkleTreeNode(None, None, value, content, path=path)

        assert node.path == path
        
    def test_node_hash_method(self):
        """Test static hash method."""
        test_value = "test_string_to_hash"
        expected_hash = sha256_hash(test_value)

        # Hash should be a string
        assert isinstance(expected_hash, str)
        
        # Hash should be consistent (same input = same output)
        hash1 = sha256_hash(test_value)
        hash2 = sha256_hash(test_value)
        assert hash1 == hash2
        
        # Different inputs should have different hashes
        hash3 = sha256_hash("different_string")
        assert hash1 != hash3
        
    def test_node_string_representation(self, merkle_node_data):
        """Test node string representation."""
        content, value, left_node, right_node = merkle_node_data
        node = MerkleTreeNode(None, None, value, content)
        str_repr = str(node)
        
        assert str_repr == value
        
    

@pytest.fixture
def merkle_tree_data():
    """Fixture for merkle tree tests."""
    test_data = ["data1", "data2", "data3", "data4"]
    empty_data = []
    single_data = ["single_item"]
    odd_data = ["data1", "data2", "data3"]
    return test_data, empty_data, single_data, odd_data


class TestMerkleTree:
    """Test suite for Merkle Tree implementation."""
        
    def test_tree_initialization(self, merkle_tree_data):
        """Test MerkleTree initialization."""
        test_data, empty_data, single_data, odd_data = merkle_tree_data
        tree = MerkleTree(test_data)

        assert len(tree.leaves) == len(test_data)
        assert tree.root is not None
        assert tree.prf_list is not None
        
    def test_tree_genesis_block_initialization(self, merkle_tree_data):
        """Test genesis block tree initialization."""
        test_data, empty_data, single_data, odd_data = merkle_tree_data
        tree = MerkleTree(single_data, is_genesis_block=True)

        assert len(tree.leaves) == 1
        assert tree.root.value == tree.leaves[0].value
        assert tree.root == tree.leaves[0]
        
    def test_tree_empty_data(self, merkle_tree_data):
        """Test tree initialization with empty data."""
        test_data, empty_data, single_data, odd_data = merkle_tree_data
        # This should handle empty data gracefully
        tree = MerkleTree(empty_data)
        assert len(tree.leaves) == 0
        
    def test_tree_single_item(self, merkle_tree_data):
        """Test tree with single item (non-genesis)."""
        test_data, empty_data, single_data, odd_data = merkle_tree_data
        tree = MerkleTree(single_data)
        
        assert len(tree.leaves) == 1
        assert tree.root is not None
        
    def test_tree_root_hash(self, merkle_tree_data):
        """Test get_root_hash method."""
        test_data, empty_data, single_data, odd_data = merkle_tree_data
        tree = MerkleTree(test_data)
        root_hash = tree.get_root_hash()
        
        assert isinstance(root_hash, str)
        assert root_hash == tree.root.value
        
        # Test with different data should produce different root hash
        tree2 = MerkleTree(["different_data"])
        assert root_hash != tree2.get_root_hash()
        
    def test_tree_validation(self, merkle_tree_data):
        """Test tree validation method."""
        test_data, empty_data, single_data, odd_data = merkle_tree_data
        tree = MerkleTree(test_data)

        # Valid tree should return True
        assert tree.check_tree()
        
    def test_tree_single_leaf_validation(self, merkle_tree_data):
        """Test validation with single leaf."""
        test_data, empty_data, single_data, odd_data = merkle_tree_data
        tree = MerkleTree(single_data)
        assert tree.check_tree()
        
    def test_tree_validation_with_modified_data(self, merkle_tree_data):
        """Test tree validation with corrupted data."""
        test_data, empty_data, single_data, odd_data = merkle_tree_data
        tree = MerkleTree(test_data)
        
        # Corrupt a leaf node's content and hash
        original_hash = tree.leaves[0].value
        tree.leaves[0].content = "corrupted_content"
        tree.leaves[0].value = "corrupted_hash"
        
        # Tree should fail validation
        assert not tree.check_tree()
        
        # Restore original content
        tree.leaves[0].content = test_data[0]
        tree.leaves[0].value = original_hash
        
        # Tree should pass validation again
        assert tree.check_tree()
        
    def test_tree_leaves_properties(self, merkle_tree_data):
        """Test leaves properties and indexing."""
        test_data, empty_data, single_data, odd_data = merkle_tree_data
        tree = MerkleTree(test_data)

        # Check that leaves are properly indexed
        for i, leaf in enumerate(tree.leaves):
            assert leaf.leaf_index == i
            assert leaf.content == test_data[i]
            
    def test_tree_prf_list_generation(self, merkle_tree_data):
        """Test proof list generation."""
        test_data, empty_data, single_data, odd_data = merkle_tree_data
        tree = MerkleTree(test_data)

        assert tree.prf_list is not None
        assert len(tree.prf_list) == len(test_data)
        
        # Each proof should be a list
        for proof in tree.prf_list:
            assert isinstance(proof, list)
            
    def test_tree_different_data_sizes(self, merkle_tree_data):
        """Test tree with different data sizes."""
        test_data, empty_data, single_data, odd_data = merkle_tree_data
        test_cases = [
            ["item1"],  # Single item
            ["item1", "item2"],  # Even number
            ["item1", "item2", "item3"],  # Odd number
            ["item1", "item2", "item3", "item4", "item5"],  # Larger odd number
        ]
        
        for data in test_cases:
            tree = MerkleTree(data)
            assert tree.check_tree()
                
    def test_tree_duplicate_data(self):
        """Test tree with duplicate data items."""
        duplicate_data = ["same", "same", "same", "different"]
        tree = MerkleTree(duplicate_data)

        # Tree should still be valid
        assert tree.check_tree()
        
        # But different positions should have different paths/indexes
        for i, leaf in enumerate(tree.leaves):
            assert leaf.leaf_index == i
            
    def test_tree_hash_consistency(self, merkle_tree_data):
        """Test hash consistency across multiple tree creations."""
        test_data, empty_data, single_data, odd_data = merkle_tree_data
        tree1 = MerkleTree(test_data)
        tree2 = MerkleTree(test_data)

        # Same data should produce same root hash
        assert tree1.get_root_hash() == tree2.get_root_hash()
        
        # Leaves should have same hashes in same positions
        for i in range(len(tree1.leaves)):
            assert tree1.leaves[i].value == tree2.leaves[i].value
            
    def test_tree_path_generation(self, merkle_tree_data):
        """Test path generation in leaves."""
        test_data, empty_data, single_data, odd_data = merkle_tree_data
        tree = MerkleTree(test_data)

        # All leaves should have paths
        for leaf in tree.leaves:
            assert isinstance(leaf.path, list)
            
    def test_tree_large_dataset(self, merkle_tree_data):
        """Test tree with larger dataset."""
        test_data, empty_data, single_data, odd_data = merkle_tree_data
        large_data = [f"item_{i}" for i in range(100)]
        tree = MerkleTree(large_data)

        assert tree.check_tree()
        assert len(tree.leaves) == 100
        
    def test_tree_string_data(self):
        """Test tree with various string data."""
        string_data = [
            "short",
            "medium_length_string",
            "a" * 1000,  # Long string
            "",  # Empty string
            "special_chars_!@#$%^&*()",
        ]

        tree = MerkleTree(string_data)
        assert tree.check_tree()
        
    def test_node_father_relationship(self):
        """Test father-child relationship setup in Merkle Tree."""
        test_data = ["data1", "data2", "data3", "data4"]
        tree = MerkleTree(test_data)

        # Test that all leaf nodes have their father set
        for leaf in tree.leaves:
            assert leaf.father is not None, f"Leaf node {leaf.leaf_index} should have a father"
            
        # Test that internal nodes have their father set (except root)
        internal_nodes = []
        def collect_internal_nodes(node):
            if node and node.left and node.right:  # Internal node
                if node != tree.root:  # Not the root
                    internal_nodes.append(node)
                collect_internal_nodes(node.left)
                collect_internal_nodes(node.right)
        
        collect_internal_nodes(tree.root)
        
        for node in internal_nodes:
            assert node.father is not None, f"Internal node should have a father"
            
        # Test that root has no father
        assert tree.root.father is None, "Root node should not have a father"
        
        # Test specific parent-child relationships
        # For a tree with 4 leaves: [0,1,2,3]
        # Level 1: parent(0,1) and parent(2,3)
        # Level 2: root(parent(0,1), parent(2,3))
        
        # Find parent of leaf 0
        leaf0_parent = tree.leaves[0].father
        assert leaf0_parent.left == tree.leaves[0]
        assert leaf0_parent.right == tree.leaves[1]
        
        # Find parent of leaf 2
        leaf2_parent = tree.leaves[2].father
        assert leaf2_parent.left == tree.leaves[2]
        assert leaf2_parent.right == tree.leaves[3]
        
        # Root should be the parent of the two parent nodes
        assert tree.root == leaf0_parent.father
        assert tree.root == leaf2_parent.father
        

class TestMerkleTreeEdgeCases:
    """Test suite for Merkle Tree edge cases."""
        
    def test_tree_unicode_data(self):
        """Test tree with unicode data."""
        unicode_data = ["你好", "世界", "🌍", "🚀"]
        tree = MerkleTree(unicode_data)
        assert tree.check_tree()
        
    def test_tree_extremely_large_data(self):
        """Test tree with very large data."""
        large_data = ["a" * 10000 for _ in range(10)]
        tree = MerkleTree(large_data)
        assert tree.check_tree()
