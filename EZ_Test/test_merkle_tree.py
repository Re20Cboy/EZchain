#!/usr/bin/env python3
"""
Unit tests for Merkle Tree module.
"""

import unittest
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


class TestMerkleTreeNode(unittest.TestCase):
    """Test suite for Merkle Tree Node implementation."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.content = "test_content"
        self.value = "test_hash_value"
        self.left_node = MerkleTreeNode(None, None, "left_hash", "left_content")
        self.right_node = MerkleTreeNode(None, None, "right_hash", "right_content")
        
    def test_node_initialization(self):
        """Test MerkleTreeNode initialization."""
        node = MerkleTreeNode(self.left_node, self.right_node, self.value, self.content)

        self.assertEqual(node.left, self.left_node)
        self.assertEqual(node.right, self.right_node)
        self.assertEqual(node.value, self.value)
        self.assertEqual(node.content, self.content)
        self.assertEqual(node.path, [])
        self.assertIsNone(node.leaf_index)
        self.assertIsNone(node.father)
        
    def test_node_with_leaf_index(self):
        """Test node initialization with leaf index."""
        leaf_index = 5
        node = MerkleTreeNode(None, None, self.value, self.content, leaf_index=leaf_index)

        self.assertEqual(node.leaf_index, leaf_index)
        
    def test_node_with_path(self):
        """Test node initialization with path."""
        path = [1, 2, 3]
        node = MerkleTreeNode(None, None, self.value, self.content, path=path)

        self.assertEqual(node.path, path)
        
    def test_node_hash_method(self):
        """Test static hash method."""
        test_value = "test_string_to_hash"
        expected_hash = sha256_hash(test_value)

        # Hash should be a string
        self.assertIsInstance(expected_hash, str)
        
        # Hash should be consistent (same input = same output)
        hash1 = sha256_hash(test_value)
        hash2 = sha256_hash(test_value)
        self.assertEqual(hash1, hash2)
        
        # Different inputs should have different hashes
        hash3 = sha256_hash("different_string")
        self.assertNotEqual(hash1, hash3)
        
    def test_node_string_representation(self):
        """Test node string representation."""
        node = MerkleTreeNode(None, None, self.value, self.content)
        str_repr = str(node)
        
        self.assertEqual(str_repr, self.value)
        
    

class TestMerkleTree(unittest.TestCase):
    """Test suite for Merkle Tree implementation."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_data = ["data1", "data2", "data3", "data4"]
        self.empty_data = []
        self.single_data = ["single_item"]
        self.odd_data = ["data1", "data2", "data3"]
        
    def test_tree_initialization(self):
        """Test MerkleTree initialization."""
        tree = MerkleTree(self.test_data)

        self.assertEqual(len(tree.leaves), len(self.test_data))
        self.assertIsNotNone(tree.root)
        self.assertIsNotNone(tree.prf_list)
        
    def test_tree_genesis_block_initialization(self):
        """Test genesis block tree initialization."""
        tree = MerkleTree(self.single_data, is_genesis_block=True)

        self.assertEqual(len(tree.leaves), 1)
        self.assertEqual(tree.root.value, tree.leaves[0].value)
        self.assertEqual(tree.root, tree.leaves[0])
        
    def test_tree_empty_data(self):
        """Test tree initialization with empty data."""
        # This should handle empty data gracefully
        tree = MerkleTree(self.empty_data)
        self.assertEqual(len(tree.leaves), 0)
        
    def test_tree_single_item(self):
        """Test tree with single item (non-genesis)."""
        tree = MerkleTree(self.single_data)
        
        self.assertEqual(len(tree.leaves), 1)
        self.assertIsNotNone(tree.root)
        
    def test_tree_root_hash(self):
        """Test get_root_hash method."""
        tree = MerkleTree(self.test_data)
        root_hash = tree.get_root_hash()
        
        self.assertIsInstance(root_hash, str)
        self.assertEqual(root_hash, tree.root.value)
        
        # Test with different data should produce different root hash
        tree2 = MerkleTree(["different_data"])
        self.assertNotEqual(root_hash, tree2.get_root_hash())
        
    def test_tree_validation(self):
        """Test tree validation method."""
        tree = MerkleTree(self.test_data)

        # Valid tree should return True
        self.assertTrue(tree.check_tree())
        
    def test_tree_single_leaf_validation(self):
        """Test validation with single leaf."""
        tree = MerkleTree(self.single_data)
        self.assertTrue(tree.check_tree())
        
    def test_tree_validation_with_modified_data(self):
        """Test tree validation with corrupted data."""
        tree = MerkleTree(self.test_data)
        
        # Corrupt a leaf node's content and hash
        original_hash = tree.leaves[0].value
        tree.leaves[0].content = "corrupted_content"
        tree.leaves[0].value = "corrupted_hash"
        
        # Tree should fail validation
        self.assertFalse(tree.check_tree())
        
        # Restore original content
        tree.leaves[0].content = self.test_data[0]
        tree.leaves[0].value = original_hash
        
        # Tree should pass validation again
        self.assertTrue(tree.check_tree())
        
    def test_tree_leaves_properties(self):
        """Test leaves properties and indexing."""
        tree = MerkleTree(self.test_data)

        # Check that leaves are properly indexed
        for i, leaf in enumerate(tree.leaves):
            self.assertEqual(leaf.leaf_index, i)
            self.assertEqual(leaf.content, self.test_data[i])
            
    def test_tree_prf_list_generation(self):
        """Test proof list generation."""
        tree = MerkleTree(self.test_data)

        self.assertIsNotNone(tree.prf_list)
        self.assertEqual(len(tree.prf_list), len(self.test_data))
        
        # Each proof should be a list
        for proof in tree.prf_list:
            self.assertIsInstance(proof, list)
            
    def test_tree_different_data_sizes(self):
        """Test tree with different data sizes."""
        test_cases = [
            ["item1"],  # Single item
            ["item1", "item2"],  # Even number
            ["item1", "item2", "item3"],  # Odd number
            ["item1", "item2", "item3", "item4", "item5"],  # Larger odd number
        ]
        
        for data in test_cases:
            with self.subTest(data=data):
                tree = MerkleTree(data)
                self.assertTrue(tree.check_tree())
                
    def test_tree_duplicate_data(self):
        """Test tree with duplicate data items."""
        duplicate_data = ["same", "same", "same", "different"]
        tree = MerkleTree(duplicate_data)

        # Tree should still be valid
        self.assertTrue(tree.check_tree())
        
        # But different positions should have different paths/indexes
        for i, leaf in enumerate(tree.leaves):
            self.assertEqual(leaf.leaf_index, i)
            
    def test_tree_hash_consistency(self):
        """Test hash consistency across multiple tree creations."""
        tree1 = MerkleTree(self.test_data)
        tree2 = MerkleTree(self.test_data)

        # Same data should produce same root hash
        self.assertEqual(tree1.get_root_hash(), tree2.get_root_hash())
        
        # Leaves should have same hashes in same positions
        for i in range(len(tree1.leaves)):
            self.assertEqual(tree1.leaves[i].value, tree2.leaves[i].value)
            
    def test_tree_path_generation(self):
        """Test path generation in leaves."""
        tree = MerkleTree(self.test_data)

        # All leaves should have paths
        for leaf in tree.leaves:
            self.assertIsInstance(leaf.path, list)
            
    def test_tree_large_dataset(self):
        """Test tree with larger dataset."""
        large_data = [f"item_{i}" for i in range(100)]
        tree = MerkleTree(large_data)

        self.assertTrue(tree.check_tree())
        self.assertEqual(len(tree.leaves), 100)
        
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
        self.assertTrue(tree.check_tree())
        
    def test_node_father_relationship(self):
        """Test father-child relationship setup in Merkle Tree."""
        test_data = ["data1", "data2", "data3", "data4"]
        tree = MerkleTree(test_data)

        # Test that all leaf nodes have their father set
        for leaf in tree.leaves:
            self.assertIsNotNone(leaf.father, f"Leaf node {leaf.leaf_index} should have a father")
            
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
            self.assertIsNotNone(node.father, f"Internal node should have a father")
            
        # Test that root has no father
        self.assertIsNone(tree.root.father, "Root node should not have a father")
        
        # Test specific parent-child relationships
        # For a tree with 4 leaves: [0,1,2,3]
        # Level 1: parent(0,1) and parent(2,3)
        # Level 2: root(parent(0,1), parent(2,3))
        
        # Find parent of leaf 0
        leaf0_parent = tree.leaves[0].father
        self.assertEqual(leaf0_parent.left, tree.leaves[0])
        self.assertEqual(leaf0_parent.right, tree.leaves[1])
        
        # Find parent of leaf 2
        leaf2_parent = tree.leaves[2].father
        self.assertEqual(leaf2_parent.left, tree.leaves[2])
        self.assertEqual(leaf2_parent.right, tree.leaves[3])
        
        # Root should be the parent of the two parent nodes
        self.assertEqual(tree.root, leaf0_parent.father)
        self.assertEqual(tree.root, leaf2_parent.father)
        

class TestMerkleTreeEdgeCases(unittest.TestCase):
    """Test suite for Merkle Tree edge cases."""
    
    """def test_tree_none_data(self):
        tree = merkle_tree([None, None, None])
        self.assertTrue(tree.check_tree())"""
        
    def test_tree_unicode_data(self):
        """Test tree with unicode data."""
        unicode_data = ["你好", "世界", "🌍", "🚀"]
        tree = MerkleTree(unicode_data)
        self.assertTrue(tree.check_tree())
        
    def test_tree_extremely_large_data(self):
        """Test tree with very large data."""
        large_data = ["a" * 10000 for _ in range(10)]
        tree = MerkleTree(large_data)
        self.assertTrue(tree.check_tree())


if __name__ == '__main__':
    unittest.main(verbosity=2)